from collections.abc import Generator, Iterable
from datetime import datetime
from typing import TypeVar

from merging import Merger
from multiline_log_handler import MultilineLogCollapser
from timestamp_wrapper import TimestampedLineTransformer
import littletable as lt


T = TypeVar("T")


def label(s: str, seq: Iterable[T]) -> Generator[tuple[str, T], None, None]:
    """
    method to make each item of an Iterable into a tuple containing the
    label (so that as items from different iterators are later combined, we'll know
    which iterator a particular item came from)
    """
    yield from ((s, obj) for obj in seq)


def clipper(n: int, seq: Iterable) -> Generator[int, None, None]:
    """
    clip an iterable to the first n items
    """
    for i, obj in enumerate(seq):
        if i < n:
            yield obj
        else:
            break


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


def main(args: list[str]):

    # use argparse to get these
    fnames = args[1:]
    interactive = True

    textual_output = interactive
    table_output = not interactive

    # for development demo - eventually switch to argparse or click to get filenames
    if not fnames:
        fnames = ["../files/log1.txt", "../files/syslog1.txt", "../files/log2.txt"]

    # generate dicts, one per timestamp, with values for each log file for the respective
    # log line from that file at that timestamp, or "" if no log line at that timestamp
    merged_lines = merge_log_file_lines(fnames)

    if table_output:
        # build a littletable Table for easy tabular output, and insert the dicts of merged lines
        tbl = lt.Table()
        tbl.insert_many(merged_lines)

        # present the table - using a rich Table, the columns will auto-size to content and terminal
        # width
        tbl.present()

    if textual_output:
        from textual.app import App, ComposeResult
        from textual.widgets import DataTable

        class TableApp(App):
            def compose(self) -> ComposeResult:
                yield DataTable()

            def on_mount(self) -> None:
                table = self.query_one(DataTable)
                table.cursor_type = "row"
                table.zebra_stripes = True
                first_line = next(merged_lines)
                table.add_columns(*first_line.keys())
                table.add_row(*first_line.values())

                def max_line_count(d):
                    """
                    The number of lines for this row is the maximum number of newlines
                    in any value, plus 1.
                    """
                    return max(s.count("\n") for s in d.values()) + 1

                for line in merged_lines:
                    table.add_row(*line.values(), height=max_line_count(line))

        app = TableApp()
        app.run()


if __name__ == '__main__':
    import sys
    main(sys.argv)
