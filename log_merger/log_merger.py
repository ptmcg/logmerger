#
# log_merger.py
#
# Utility for viewing multiple log files in a side-by-side merged format.
#
# Copyright 2023, Paul McGuire
#

import argparse
import sys
from collections.abc import Generator, Iterable
from datetime import datetime
import itertools
import textwrap
import types
from typing import TypeVar

import littletable as lt
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import DataTable, Footer

from .file_reading import FileReader
from .merging import Merger
from .multiline_log_handler import MultilineLogCollapser
from .timestamp_wrapper import TimestampedLineTransformer


T = TypeVar("T")


def make_argument_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="+", help="log files to be merged")
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="show output using interactive TUI browser"
    )
    parser.add_argument(
        "--width", "-w",
        type=int,
        help="total screen width to use for interactive mode (defaults to current screen width)",
        default=0
    )
    parser.add_argument("--csv", "-csv", help="save merged logs to CSV file")
    parser.add_argument(
        "--encoding",
        type=str,
        default=sys.getdefaultencoding(),
        help="encoding to use when reading log files (defaults to the system default encoding)")
    return parser


def label(s: str, seq: Iterable[T]) -> Generator[tuple[str, T], None, None]:
    """
    method to make each item of an Iterable into a tuple containing the
    label (so that as items from different iterators are later combined, we'll know
    which iterator a particular item came from)
    """
    yield from ((s, obj) for obj in seq)


def format_timestamp(dt: datetime) -> str:
    """
    format a datetime to microseconds, truncate to just millis
    """
    return dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:23]


class InteractiveLogMergeViewerApp(App):

    BINDINGS = [
        Binding(key="q", action="quit", description="Quit"),
    ]

    def config(
            self,
            log_file_names: list[str],
            merged_log_lines_table: lt.Table,
            display_width: int,
    ):
        self.log_file_names = log_file_names  # noqa
        self.merged_log_lines_table = merged_log_lines_table  # noqa
        self.display_width = display_width  # noqa

    def compose(self) -> ComposeResult:
        yield DataTable(fixed_columns=1)
        yield Footer()

    def on_mount(self) -> None:
        display_table = self.query_one(DataTable)
        display_table.cursor_type = "row"
        display_table.zebra_stripes = True
        col_names = self.merged_log_lines_table.info()["fields"]
        display_table.add_columns(*col_names)

        screen_width = self.display_width or self.size.width
        # guesstimate how much width each file will require
        width_per_file = int((screen_width - 25) * 0.95 // len(self.log_file_names))

        def max_line_count(sseq: list[str]):
            """
            The number of lines for this row is the maximum number of newlines
            in any value, plus 1.
            """
            return max(s.count("\n") for s in sseq) + 1

        line_ns: types.SimpleNamespace
        for line_ns in self.merged_log_lines_table:
            row_values = list(vars(line_ns).values())
            # see if any text wrapping is required for this line
            # - check each cell to see if any line in the cell exceeds width_per_file
            # - if not, just add this row to the display_table
            if any(len(rv_line) > width_per_file
                   for rv in row_values
                   for rv_line in rv.splitlines()):
                # wrap individual cells (except never wrap the timestamp)
                wrapped_row_values = [row_values[0]]
                for cell_value in row_values[1:]:
                    if "\n" in cell_value or len(cell_value) > width_per_file:
                        cell_lines = (
                            "\n".join(textwrap.wrap(rvl, width_per_file))
                            for rvl in cell_value.splitlines()
                        )
                        wrapped_row_values.append("\n".join(cell_lines))
                    else:
                        wrapped_row_values.append(cell_value)
                display_table.add_row(*wrapped_row_values, height=max_line_count(wrapped_row_values))
            else:
                display_table.add_row(*row_values, height=max_line_count(row_values))


class LogMergerApplication:
    def __init__(self, config: argparse.Namespace):
        self.config = config

        self.fnames = config.files
        self.total_width = config.width

        self.interactive = config.interactive
        self.textual_output = self.interactive
        self.table_output = not self.interactive
        self.save_to_csv = config.csv

        self.encoding = self.config.encoding

    def run(self):
        # generate dicts, one per timestamp, with values for each log file for the respective
        # log line from that file at that timestamp, or "" if no log line at that timestamp
        merged_lines = self.merge_log_file_lines()

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
            self.display_merged_lines_interactively(merged_lines_table)

    def merge_log_file_lines(self) -> Generator[dict[str, T], None, None]:

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
                    (
                        MultilineLogCollapser()(
                            map(xformer, map(str.rstrip, reader))
                        )
                    )
                )
            ) for fname, xformer, reader in zip(self.fnames, transformers, readers)
        ]

        # use the Merger class which internally uses a heap to pull values in timestamp order from
        # all the iterators, and then uses groupby to group them by common timestamp
        merger = Merger(log_file_line_iters, key_function=lambda log_data: log_data[1][0])

        # build and yield a dict for each timestamp
        for timestamp, items in merger:

            # initialize the entry for this timestamp with empty strings for each given file
            line_dict = {
                "timestamp": format_timestamp(timestamp),
                **{}.fromkeys(self.fnames, ""),
            }

            # copy from the group each file's respective logging for this timestamp, and
            # insert into the dict for this timestamp
            for item in items:
                fname, (_, line) = item
                line_dict[fname] = line

            # yield the populated dict
            yield line_dict

    def display_merged_lines_interactively(
            self,
            merged_log_lines: lt.Table,
    ):

        app = InteractiveLogMergeViewerApp()
        app.config(self.fnames, merged_log_lines, self.total_width)
        app.run()


def main():

    parser = make_argument_parser()
    args_ns = parser.parse_args()

    app = LogMergerApplication(args_ns)
    app.run()


if __name__ == '__main__':
    main()
