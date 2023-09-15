#
# log_merger.py
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
from typing import TypeVar

import littletable as lt

from .file_reading import FileReader
from .interactive_viewing import InteractiveLogMergeViewerApp
from .merging import Merger
from .multiline_log_handler import MultilineLogCollapser
from .timestamp_wrapper import TimestampedLineTransformer


T = TypeVar("T")


def make_argument_parser():
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

    parser = argparse.ArgumentParser(epilog=epilog_notes)
    parser.add_argument("files", nargs="+", help="log files to be merged")
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="show output using interactive TUI browser"
    )
    parser.add_argument('--start', '-s', required=False, help="start time to select time window for merging logs")
    parser.add_argument('--end', '-e', required=False, help="end time to select time window for merging logs")
    parser.add_argument(
        "--width", "-w",
        type=int,
        help="total screen width to use for interactive mode (defaults to current screen width)",
        default=0
    )
    parser.add_argument("--line_numbers", "-ln", action="store_true", help="add line number column")
    parser.add_argument("--csv", "-csv", help="save merged logs to CSV file")
    parser.add_argument(
        "--encoding", "-enc",
        type=str,
        default=sys.getfilesystemencoding(),
        help="encoding to use when reading log files (defaults to the system default encoding)")

    return parser


def parse_time_using(ts_str: str, formats: str | list[str]) -> datetime:
    if not isinstance(formats, (list, tuple)):
        formats = [formats]
    for fmt in formats:
        try:
            return datetime.strptime(ts_str, fmt)
        except ValueError:
            pass
    raise ValueError(f"no matching format for input string {ts_str!r}")


def parse_relative_time(ts_str: str) -> datetime:
    parts = re.match(r"(\d+)([smhd])$", ts_str, flags=re.IGNORECASE)
    if parts:
        qty, unit = parts.groups()
        seconds = int(qty)
        now = datetime.now()
        for unit_type, mult in [("s", 1), ("m", 60), ("h", 60), ("d", 24)]:
            seconds *= mult
            if unit == unit_type:
                return now - timedelta(seconds=seconds)

    raise ValueError(f"invalid relative time string {ts_str!r}")


def label(s: str, seq: Iterable[T]) -> Generator[tuple[str, T], None, None]:
    """
    method to make each item of an Iterable into a tuple containing the
    label (so that as items from different iterators are later combined, we'll know
    which iterator a particular item came from)
    """
    yield from ((s, obj) for obj in seq)


class LogMergerApplication:
    def __init__(self, config: argparse.Namespace):
        self.config = config

        self.fnames = config.files
        self.total_width = config.width

        valid_formats = [
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
        if config.start is None:
            self.start_time = datetime.min
        else:
            if config.start.endswith(tuple("smhd")):
                self.start_time = parse_relative_time(config.start)
            else:
                self.start_time = parse_time_using(config.start, valid_formats)

        if config.end is None:
            self.end_time = datetime.max
        else:
            if config.end.endswith(tuple("smhd")):
                self.end_time = parse_relative_time(config.end)
            else:
                self.end_time = parse_time_using(config.end, valid_formats)

        if self.end_time <= self.start_time:
            raise ValueError("invalid start/end times - start must be before end")

        self.time_clip = lambda ts_log: self.start_time <= ts_log[0] <= self.end_time

        self.interactive = config.interactive
        self.textual_output = self.interactive
        self.table_output = not self.interactive
        self.save_to_csv = config.csv

        self.encoding = self.config.encoding

    def run(self):
        # generate dicts, one per timestamp, with values for each log file for the respective
        # log line from that file at that timestamp, or "" if no log line at that timestamp
        merged_lines = self._merge_log_file_lines()

        # build a littletable Table for easy tabular output, and insert the dicts of merged lines
        merged_lines_table = lt.Table()
        merged_lines_table.insert_many(merged_lines)

        if self.save_to_csv:
            merged_lines_table.csv_export(self.save_to_csv)

        elif self.table_output:
            # present the table - using a rich Table, the columns will auto-size to content and terminal
            # width
            merged_lines_table.present()

        elif self.textual_output:
            self._display_merged_lines_interactively(merged_lines_table)

    def _merge_log_file_lines(self) -> Generator[dict[str, T], None, None]:

        # scan input files to determine timestamp format, and create appropriate transformer for each
        readers = [FileReader.get_reader(fname, self.encoding) for fname in self.fnames]
        peek_iters, readers = zip(*[itertools.tee(rdr) for rdr in readers])
        transformers = [TimestampedLineTransformer.make_transformer_from_sample_line(next(peek_iter))
                        for peek_iter in peek_iters]

        # build iterators over each file that:
        # - transform each line into a (datetime, str) tuple (where the str is everything after the
        #   timestamp, so that it doesn't get repeated in the output table)
        # - collapses multiline logs (lines that go beyond just one line, with subsequent lines that
        #   do not start with a timestamp - tracebacks are a common example)
        # - labels each item the its source filename (so that after pulling an entry for the heap, we
        #   know which file it came from)
        # (for background on why we must use map() instead of a generator expression,
        # see https://chat.stackoverflow.com/transcript/message/56645472#56645472)
        log_file_line_iters = [
            (
                label(
                    fname,
                    filter(self.time_clip, (
                            MultilineLogCollapser()(
                                map(xformer, map(str.rstrip, reader))
                            )
                        )
                    )
                )
            ) for fname, xformer, reader in zip(self.fnames, transformers, readers)
        ]

        # use the Merger class which internally uses a heap to pull values in timestamp order from
        # all the iterators, and then uses groupby to group them by common timestamp
        merger = Merger(log_file_line_iters, key_function=lambda log_data: log_data[1][0])

        if self.config.line_numbers:
            initialize_row_dict = lambda n, ts: {"line": str(n), "timestamp": ts.strftime("%Y-%m-%d %H:%M:%S.%f")[:23]}
        else:
            initialize_row_dict = lambda n, ts: {"timestamp": ts.strftime("%Y-%m-%d %H:%M:%S.%f")[:23]}

        # build and yield a dict for each timestamp
        for line_number, (timestamp, items) in enumerate(merger, start=1):

            # initialize the entry for this timestamp with empty strings for each given file
            line_dict = {
                **initialize_row_dict(line_number, timestamp),
                **{}.fromkeys(self.fnames, ""),
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
    ):

        app = InteractiveLogMergeViewerApp()
        app.config(self.fnames, self.total_width, self.config.line_numbers, merged_log_lines)
        app.run()


def main():

    parser = make_argument_parser()
    args_ns = parser.parse_args()

    app = LogMergerApplication(args_ns)
    app.run()


if __name__ == '__main__':
    main()
