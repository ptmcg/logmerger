#
# logmerger.py
#
# Utility for viewing multiple log files in a side-by-side merged format.
#
# Copyright 2023, Paul McGuire
#

import argparse
from collections.abc import Generator, Iterable
from datetime import datetime, timedelta
import itertools
import re
import sys
from pathlib import Path
from typing import TypeVar, Union

import littletable as lt

from logmerger.file_reading import FileReader
from logmerger.interactive_viewing import InteractiveLogMergeViewerApp
from logmerger.merging import Merger
from logmerger.multiline_log_handler import MultilineLogCollapser
from logmerger.timestamp_wrapper import TimestampedLineTransformer


T = TypeVar("T")
try:
    from typing import Never
except ImportError:
    from typing import NoReturn as Never


def make_argument_parser() -> argparse.ArgumentParser:
    epilog_notes = """
    Start and end timestamps to clip the given files to a particular time window can be 
    given in `YYYY-MM-DD HH:MM:SS.SSS` format, with trailing milliseconds and seconds
    optional, and "," permissible for the decimal point. A "T" can be included between
    the date and time to simplify entering the timestamp on a command line 
    (otherwise would require enclosing in quotes because of the intervening space). These
    command line values do not need to match the timestamp formats in the log files.

    These values may also be given as relative times, such as "15m" for "15 minutes ago".
    Valid units are "s", "m", "h", and "d" for seconds, minutes, hours, or days.
    """

    # When changing these arguments, update relevant sections in
    # - README.md
    # - about.py
    #
    parser = argparse.ArgumentParser(prog="logmerger", epilog=epilog_notes)
    parser.add_argument("files", nargs="*", help="log files to be merged")
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        default=True,
        help="show merged output using interactive TUI browser (default)",
    )
    parser.add_argument(
        "--inline",
        action="store_true",
        default=False,
        help="show merged log data as inline merge",
    )
    parser.add_argument(
        "--output", "-o",
        # type=argparse.FileType('w'),
        help="save merged output to file ('-' for stdout; files ending in '.md' are saved using Markdown)",
    )
    parser.add_argument(
        '--start',
        '-s',
        required=False,
        help="start time to select time window for merging logs",
    )
    parser.add_argument(
        '--end',
        '-e',
        required=False,
        help="end time to select time window for merging logs",
    )
    parser.add_argument(
        "--autoclip", "-ac",
        action="store_true",
        help="clip merging to time range of logs in first log file",
    )
    parser.add_argument(
        "--ignore_non_timestamped",
        action="store_true",
        help="ignore log lines that do not have a timestamp"
    )
    parser.add_argument(
        "--width", "-w",
        type=int,
        help="total screen width to use for interactive mode (defaults to current screen width)",
        default=0,
    )
    parser.add_argument(
        "--line_numbers", "-ln", action="store_true", help="add line number column"
    )
    parser.add_argument(
        "--show_clock", "-clock", action="store_true", help="show running clock in header"
    )
    parser.add_argument("--csv", "-csv", help="save merged logs to CSV file")
    parser.add_argument(
        "--encoding", "-enc",
        type=str,
        default=sys.getfilesystemencoding(),
        help="encoding to use when reading log files (defaults to the system default encoding)")
    parser.add_argument(
        "--timestamp_format",
        dest="timestamp_formats",
        nargs="*",
        action="append",
        help="custom timestamp format"
    )
    parser.add_argument("--demo", action="store_true", help="Run interactive demo")

    return parser


VALID_INPUT_TIME_FORMATS = [
    "%Y-%m-%d %H:%M:%S.%f",
    "%Y-%m-%d %H:%M:%S,%f",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%dT%H:%M:%S.%f",
    "%Y-%m-%dT%H:%M:%S,%f",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M",
    "%Y-%m-%d",
]


def parse_time_using(ts_str: str, formats: Union[str, list[str]]) -> datetime:
    """
    Given a timestamp string of unknown format, try parsing it against
    a format or list of formats.
    """
    if not isinstance(formats, (list, tuple)):
        formats = [formats]
    for fmt in formats:
        try:
            return datetime.strptime(ts_str, fmt)
        except ValueError:
            pass

    raise ValueError(f"no matching format for input string {ts_str!r}")


def parse_relative_time(ts_str: str) -> datetime:
    """
    Given a string representing a relative timestamp of an integer
    followed by "s", "m", "h", or "d", return a datetime object that
    many seconds, minutes, hours, or days in the past.
    """
    parts = re.match(r"(\d+)([smhd])$", ts_str, flags=re.IGNORECASE)
    if parts is None:
        raise ValueError(f"invalid relative time string {ts_str!r}")

    qty, unit = parts.groups()
    seconds = int(qty)
    now = datetime.now()
    for unit_type, mult in [("s", 1), ("m", 60), ("h", 60), ("d", 24)]:
        seconds *= mult
        if unit == unit_type:
            return now - timedelta(seconds=seconds)



def label(s: str):
    def _inner(seq: Iterable[T]) -> Generator[tuple[str, T], None, None]:
        """
        method to make each item of an Iterable into a tuple containing the
        label (so that as items from different iterators are later combined, we'll know
        which iterator a particular item came from)
        """
        yield from ((s, obj) for obj in seq)
    return _inner


class LogMergerApplication:
    def __init__(self, config: argparse.Namespace):
        self.config = config

        if config.timestamp_formats:
            formats = sum(config.timestamp_formats, [])
            for ts_format in formats:
                TimestampedLineTransformer.make_custom_transformers(ts_format)

        self.file_names = config.files
        self.total_width = config.width
        self.autoclip = config.autoclip
        self.append_non_timestamped_lines = not config.ignore_non_timestamped

        if config.start is None:
            self.start_time = datetime.min
        else:
            if config.start.endswith(("s", "m", "h", "d")):
                self.start_time = parse_relative_time(config.start)
            else:
                self.start_time = parse_time_using(config.start, VALID_INPUT_TIME_FORMATS)

        if config.end is None:
            self.end_time = datetime.max
        else:
            if config.end.endswith(("s", "m", "h", "d")):
                self.end_time = parse_relative_time(config.end)
            else:
                self.end_time = parse_time_using(config.end, VALID_INPUT_TIME_FORMATS)

        if self.end_time <= self.start_time:
            raise ValueError("invalid start/end times - start must be before end")

        self.time_clip = None
        if config.end:
            self.time_clip = self._time_clip_early_exit
        elif config.start:
            self.time_clip = self._time_clip_after_start

        self.interactive = config.interactive
        self.textual_output = self.interactive
        self.save_to_file = config.output
        self.save_to_csv = config.csv

        self.encoding = self.config.encoding

    def _time_clip_after_start(self, ts: datetime) -> bool:
        return ts is None or self.start_time <= ts

    def _time_clip_early_exit(self, ts: datetime) -> bool:
        if ts is None:
            return True
        if ts > self.end_time:
            raise StopIteration
        return self.start_time <= ts

    def _raw_time_clip(self, ts_log: tuple[datetime, str]) -> bool:
        ts, _ = ts_log
        return ts is None or self.start_time <= ts <= self.end_time

    def run(self) -> None:
        # generate dicts, one per timestamp, with values for each log file for the respective
        # log line from that file at that timestamp, or "" if no log line at that timestamp
        merged_lines = self._merge_log_file_lines()

        # build a littletable Table for easy tabular output, and insert the dicts of merged lines
        merged_lines_table = lt.Table()
        merged_lines_table.insert_many(merged_lines)

        if self.save_to_csv:
            merged_lines_table.csv_export(self.save_to_csv)

        elif self.save_to_file:
            if self.save_to_file == "-":
                # present the table to stdout - using a rich Table, the columns will auto-size to content and terminal
                # width

                # guard against embedded rich-like tags
                for line in merged_lines_table:
                    for k, v in vars(line).items():
                        if k in ("timestamp", "line"):
                            continue
                        setattr(line, k, v.replace("[/", r"\[/"))

                merged_lines_table.present(width=self.total_width)

            elif self.save_to_file.endswith(".md"):
                # present the table to a file, using Markdown format
                col_names = merged_lines_table.info()["fields"]
                for col in col_names:
                    merged_lines_table.add_field(col, lambda rec: getattr(rec, col).replace("\n", "<br />"))
                md_output = merged_lines_table.as_markdown(groupby="timestamp")
                Path(self.save_to_file).write_text(md_output)
            else:
                # present the table to a file

                # guard against embedded rich-like tags
                for line in merged_lines_table:
                    for k, v in vars(line).items():
                        if k in ("timestamp", "line"):
                            continue
                        setattr(line, k, v.replace("[/", r"\[/"))

                box_style = lt.box.MINIMAL
                with open(self.save_to_file, "w") as present_file:
                    merged_lines_table.present(file=present_file, box=box_style, width=self.total_width)

        elif self.textual_output:
            self._display_merged_lines_interactively(merged_lines_table)

    def _merge_log_file_lines(self) -> Generator[dict[str, T], None, None]:

        # scan input files to determine timestamp format, and create appropriate transformer for each
        readers = [FileReader.get_reader(fname, self.encoding) for fname in self.file_names]
        peek_iters, readers = zip(*[itertools.tee(rdr) for rdr in readers])

        transformers = []
        for peek_iter in peek_iters:
            try:
                transformers.append(
                    TimestampedLineTransformer.make_transformer_from_sample_line(
                        next(peek_iter)
                    )
                )
            except StopIteration:
                # this was an empty file, put do-nothing transformer in its place
                transformers.append(lambda *args: None)

        if self.autoclip:
            clip_peek, rdr0 = itertools.tee(readers[0])
            readers = (rdr0, *readers[1:])
            peek_transformer = transformers[0]
            for peek_line in clip_peek:
                first_ts, _ = peek_transformer(peek_line)
                if first_ts is not None:
                    break
            else:
                raise ValueError(f"no timestamps found in log file {self.file_names[0]!r}")

            self.start_time = self.end_time = first_ts
            for ts, _ in (peek_transformer(line) for line in clip_peek):
                if ts is None:
                    continue
                if ts > self.end_time:
                    self.end_time = ts
                elif ts < self.start_time:
                    self.start_time = ts
            self.time_clip = self._time_clip_early_exit

        # build iterators over each file that:
        # - transform each line into a (datetime, str) tuple (where the str is everything after the
        #   timestamp, so that it doesn't get repeated in the output table)
        # - collapses multiline logs (lines that go beyond just one line, with subsequent lines that
        #   do not start with a timestamp - tracebacks are a common example)
        # - labels each item with its source filename (so that after pulling an entry for the heap, we
        #   know which file it came from)
        # (for background on why we must use map() instead of a generator expression,
        # see https://chat.stackoverflow.com/transcript/message/56645472#56645472)

        # create a nested iterator for each log file to read, rstrip, transform, clip,
        # collapse, and label each log line
        log_file_line_iters = [
            label(fname)(
                MultilineLogCollapser(self.time_clip, include_non_timestamped_lines=self.append_non_timestamped_lines)(
                    filter(self._raw_time_clip, map(xformer, map(str.rstrip, reader)))
                )
            )
            for fname, xformer, reader in zip(self.file_names, transformers, readers)
        ]

        # use the Merger class which internally uses a heap to pull values in timestamp order from
        # all the iterators, and then uses groupby to group them by common timestamp
        merger = Merger(log_file_line_iters, key_function=lambda log_data: log_data[1][0])

        if self.config.line_numbers:
            initialize_row_dict = lambda n, ts: {  # noqa
                "line": str(n),
                "timestamp": ts.strftime("%Y-%m-%d %H:%M:%S.%f")[:23] if ts > datetime.min else ""
            }
        else:
            initialize_row_dict = lambda n, ts: {  # noqa
                "timestamp": ts.strftime("%Y-%m-%d %H:%M:%S.%f")[:23] if ts > datetime.min else ""
            }

        # build and yield a dict for each timestamp
        for line_number, (timestamp, items) in enumerate(merger, start=1):

            # initialize the entry for this timestamp with empty strings for each given file
            line_dict = {
                **initialize_row_dict(line_number, timestamp),
                **{}.fromkeys(self.file_names, ""),
            }

            # copy from the group each file's respective logging for this timestamp, and
            # insert into the dict for this timestamp
            for item in items:
                fname, (_, line) = item
                line_dict[fname] = line

            # yield the populated dict
            yield line_dict

    def _display_merged_lines_interactively(
            self,
            merged_log_lines: lt.Table,
    ) -> Never:

        app = InteractiveLogMergeViewerApp()
        app.config(
            log_file_names=self.file_names,
            display_width=self.total_width,
            show_line_numbers=self.config.line_numbers,
            merged_log_lines_table=merged_log_lines,
            show_merged_logs_inline=self.config.inline,
            show_clock=self.config.show_clock,
        )
        app.run()


def main():

    parser = make_argument_parser()
    args_ns = parser.parse_args()

    if args_ns.demo:
        # put pretend file names in to run demo
        args_ns.files = ["logfile_1.demo", "logfile_2.demo"]
    else:
        # special logic for fnames - can only be empty if running demo
        if not args_ns.files:
            parser.print_usage()
            print("One or more log files required")
            exit(1)

    # if output being piped to a file, clear interactive mode
    if not sys.stdout.isatty():
        args_ns.interactive = False
        if not args_ns.output:
            args_ns.output = "-"

    app = LogMergerApplication(args_ns)
    app.run()


if __name__ == '__main__':
    main()
