#
# log_merger.py
#
# Utility for viewing multiple log files in a side-by-side merged format.
#
# Copyright 2023, Paul McGuire
#

import argparse
from collections.abc import Generator, Iterable
from datetime import datetime
import textwrap
from typing import TypeVar

import littletable as lt
from textual.binding import Binding
from textual.widgets import Footer

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


def merge_log_file_lines(log_file_names: list[str]) -> Generator[dict[str, T], None, None]:

    # scan input files to determine timestamp format, and create appropriate transformer for each
    transformers = [TimestampedLineTransformer.make_transformer_from_file(fname) for fname in log_file_names]

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
                        map(xformer, (line.rstrip() for line in open(fname)))
                    )
                )
            )
        ) for fname, xformer in zip(log_file_names, transformers)
    ]

    # use the Merger class which internally uses a heap to pull values in timestamp order from
    # all the iterators, and then uses groupby to group them by common timestamp
    merger = Merger(log_file_line_iters, key_function=lambda log_data: log_data[1][0])

    # build and yield a dict for each timestamp
    for timestamp, items in merger:
        items = list(items)

        # initialize the entry for this timestamp with empty strings for each given file
        line_dict = {
            "timestamp": format_timestamp(timestamp),
            **{}.fromkeys(log_file_names, ""),
        }

        # copy from the group each file's respective logging for this timestamp, and
        # insert into the dict for this timestamp
        for item in items:
            fname, (_, line) = item
            line_dict[fname] = line

        # yield the populated dict
        yield line_dict


def main():

    parser = make_argument_parser()
    args_ns = parser.parse_args()

    fnames = args_ns.files
    interactive = args_ns.interactive
    total_width = args_ns.width

    textual_output = interactive
    table_output = not interactive
    save_to_csv = args_ns.csv

    # generate dicts, one per timestamp, with values for each log file for the respective
    # log line from that file at that timestamp, or "" if no log line at that timestamp
    merged_lines = merge_log_file_lines(fnames)

    # build a littletable Table for easy tabular output, and insert the dicts of merged lines
    tbl = lt.Table()
    tbl.insert_many(merged_lines)

    if save_to_csv:
        tbl.csv_export(args_ns.csv)

    elif table_output:
        # present the table - using a rich Table, the columns will auto-size to content and terminal
        # width
        tbl.present()

    elif textual_output:
        from textual.app import App, ComposeResult
        from textual.widgets import DataTable

        class TableApp(App):
            BINDINGS = [
                Binding(key="q", action="quit", description="Quit"),
            ]

            def compose(self) -> ComposeResult:
                yield DataTable(fixed_columns=1)
                yield Footer()

            def on_mount(self) -> None:
                table = self.query_one(DataTable)
                table.cursor_type = "row"
                table.zebra_stripes = True
                col_names = tbl.info()["fields"]
                table.add_columns(*col_names)

                screen_width = total_width or app.size.width
                # guesstimate how much width each file will require
                width_per_file = int((screen_width - 25) * 0.95 // len(fnames))

                def max_line_count(sseq: list[str]):
                    """
                    The number of lines for this row is the maximum number of newlines
                    in any value, plus 1.
                    """
                    return max(s.count("\n") for s in sseq) + 1

                for line in tbl:
                    raw_row_values = list(vars(line).values())
                    if any(len(rv_line) > width_per_file for rv in raw_row_values for rv_line in rv.splitlines()):
                        row_values = []
                        for v in vars(line).values():
                            vlines = ("\n".join(textwrap.wrap(rvl, width_per_file)) for rvl in v.splitlines())
                            row_values.append("\n".join(vlines))
                        table.add_row(*row_values, height=max_line_count(row_values))
                    else:
                        table.add_row(*raw_row_values, height=max_line_count(raw_row_values))

        app = TableApp()
        app.run()


if __name__ == '__main__':
    main()
