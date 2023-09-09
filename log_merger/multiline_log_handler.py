from collections.abc import Generator
from itertools import groupby
from datetime import datetime
from typing import Any, Iterable
from operator import itemgetter
import textwrap


class NewLogLineDetector:
    """
    Callable class used as a key function for itertools.groupby to detect log lines
    that don't start with a timestamp, and to group them with the last line that did
    have a timestamp.
    """
    def __init__(self):
        self._cur_dt = None

    def __call__(self, line_obj: tuple[datetime, Any]) -> datetime:
        dt, *_ = line_obj
        if dt is not None:
            self._cur_dt = dt
        return self._cur_dt


class MultilineLogCollapser:
    """
    Class to take an iterable of (datetime, str) tuples, and use itertools.groupby to
    merge consecutive log lines for a given datetime into one.

    Converts:
        2023-07-14 08:00:04 ERROR  Request processed unsuccessfully
        Something went wrong
        Traceback (last line is latest):
            blah
            blah
        ValueError("shouldn't have done that")
        2023-07-14 08:00:06 INFO   User authentication succeeded

    to two log entries.
    """
    def __init__(self):
        self._newlogline_detector = NewLogLineDetector()

    def __call__(self, log_seq: Iterable[tuple[datetime, str]]) -> Generator[tuple[datetime, str], None, None]:
        for timestamp, lines in sorted(
                ((a, list(b)) for a, b in groupby(log_seq, key=self._newlogline_detector)),
                key=itemgetter(0)):
            yield timestamp, "\n".join(line[1] for line in lines)


if __name__ == '__main__':
    from pathlib import Path
    from timestamp_wrapper import TimestampedLineTransformer
    log_lines = (Path("files") / "log1.txt").read_text().splitlines()
    transformer = TimestampedLineTransformer.make_transformer_from_sample_line(log_lines[0])

    for collapsed in MultilineLogCollapser()(transformer(line) for line in log_lines):
        print(collapsed)
