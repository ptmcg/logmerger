from collections.abc import Generator, Callable, Iterable
from itertools import groupby, islice
from datetime import datetime
from typing import Any, Optional
from operator import itemgetter


class WindowedSort:
    def __init__(self, window: int, seq: Iterable, *, key: Optional[Callable] = None):
        self.seq = seq
        self.key_function = key

        self.seq_iter = iter(seq)
        self.lookahead_buffer = list(islice(self.seq_iter, window))
        self.lookahead_buffer.sort(key=self.key_function)
        self.seq_consumed = len(self.lookahead_buffer) < window

    def __iter__(self):
        return self

    def __next__(self):
        if not self.seq_consumed:
            try:
                self.lookahead_buffer.append(next(self.seq_iter))
                self.lookahead_buffer.sort(key=self.key_function)
            except StopIteration:
                self.seq_consumed = True

        if self.lookahead_buffer:
            return self.lookahead_buffer.pop(0)
        else:
            raise StopIteration()


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
        for timestamp, lines in WindowedSort(
                window=60,
                seq=((a, list(b)) for a, b in groupby(log_seq, key=self._newlogline_detector)),
                key=itemgetter(0)
        ):
            yield timestamp, "\n".join(line[1] for line in lines)


if __name__ == '__main__':
    from pathlib import Path
    from timestamp_wrapper import TimestampedLineTransformer
    log_lines = (Path("files") / "log1.txt").read_text().splitlines()
    transformer = TimestampedLineTransformer.make_transformer_from_sample_line(log_lines[0])

    for collapsed in MultilineLogCollapser()(transformer(line) for line in log_lines):
        print(collapsed)
