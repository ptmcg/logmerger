from collections.abc import Iterable
from datetime import datetime
from merging import Merger
from multiline_log_handler import MultilineLogCollapser
from timestamp_wrapper import TimestampedLineTransformer
import littletable as lt



def label(s, seq):
    """
    method to make each item of an Iterable into a tuple containing the
    label (so that as items from different iterators are later combined, we'll know
    which iterator a particular item came from)
    """
    yield from ((s, obj) for obj in seq)


def clipper(n: int, seq: Iterable):
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


def main(args: list[str]):

    fnames = args[1:]
    table_output = True

    # for development demo - eventually switch to argparse or click to get filenames
    if not fnames:
        fnames = ["../files/log1.txt", "../files/log3.txt"]

    # scan input files to determine timestamp format, and create appropriate transformer for each
    transformers = [TimestampedLineTransformer.make_transformer_from_file(fname) for fname in fnames]

    # build iterators over each file that:
    # - transform each line into a (datetime, str) tuple (where the str is everything after the
    #   timestamp, so that it doesn't get repeated in the output table)
    # - collapses multiline logs (lines that go beyond just one line, with subsequent lines that
    #   do not start with a timestamp - tracebacks are a common example)
    # - labels each item the its source filename (so that after pulling an entry for the heap, we
    #   know which file it came from)
    log_file_iters = [
        (
            label(
                fname,
                list(
                    MultilineLogCollapser()(
                        xformer(line.rstrip()) for line in open(fname)
                    )
                )
            )
        ) for fname, xformer in zip(fnames, transformers)
    ]

    # use the Merger class which internally uses a heap to pull values in timestamp order from
    # all the iterators, and then uses groupby to group them by common timestamp
    merger = Merger(log_file_iters, key_function=lambda log_data: log_data[1][0])

    if table_output:
        # build a littletable Table for easy tabular output
        tbl = lt.Table()
        for timestamp, items in merger:
            items = list(items)
            # initialize the entry for this timestamp with empty strings for each given file
            line_dict = {
                "timestamp": format_timestamp(timestamp),
                **{}.fromkeys(fnames, ""),
            }

            # copy from the group each file's respective logging for this timestamp, and
            # insert into the dict for this timestamp
            for item in items:
                fname, (_, line) = item
                line_dict[fname] = line

            # add the dict to the table, for eventual tabular display
            tbl.insert(line_dict)

        # present the table - using a rich Table, the columns will auto-size to content and terminal
        # width
        tbl.present()


if __name__ == '__main__':
    import sys
    main(sys.argv)
