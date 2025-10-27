from collections.abc import Generator, Callable, Iterable
from functools import reduce
from operator import add
from itertools import groupby, islice
from datetime import datetime
from typing import Any, Optional
from operator import itemgetter
import bisect


class WindowedSort:
    def __init__(self, window: int, seq: Iterable, *, key: Optional[Callable] = None):
        self.seq = seq
        self.key_function = key
        self.last_line_key = None

        self.seq_iter = iter(seq)

        # get first 'window' items, and resolve/merge out-of-order entries
        temp = list(islice(self.seq_iter, window))
        temp.sort(key=self.key_function)

        # populate lookahead_buffer, grouping entries in temp by the key_function
        self.lookahead_buffer = []
        for key, lines in groupby(temp, key=self.key_function):
            values_to_merge = (ll[1] for ll in lines)
            self.lookahead_buffer.append((key, reduce(add, values_to_merge)))
            self.last_line_key = key

        # if the lookahead_buffer is smaller than the window, then we have already
        # read all the inbound lines - set seq_consumed flag accordingly
        self.seq_consumed = len(self.lookahead_buffer) < window

    def __iter__(self):
        return self

    def __next__(self):
        if not self.seq_consumed:
            # read another line from the input
            try:
                new_line = next(self.seq_iter)
                new_line_key = self.key_function(new_line)
                if self.last_line_key is None:
                    self.last_line_key = new_line_key
                if new_line_key <= self.last_line_key:
                    # use bisect to locate matching entry or insertion point in sorted lookahead_buffer
                    # find leftmost index where key == new_line_key could appear
                    idx = bisect.bisect_left(self.lookahead_buffer, new_line_key, key=self.key_function)
                    # check if a match exists at idx
                    if idx < len(self.lookahead_buffer) and self.key_function(self.lookahead_buffer[idx]) == new_line_key:
                        matching_ts, matching_log_list = self.lookahead_buffer[idx]
                        _, new_log_items = new_line
                        matching_log_list.extend(new_log_items)
                    else:
                        # insert at the correct position to keep buffer sorted
                        self.lookahead_buffer.insert(idx, new_line)
                else:
                    # append at end (monotonic increase), buffer remains sorted
                    self.lookahead_buffer.append(new_line)
                    self.last_line_key = new_line_key
            except StopIteration:
                self.seq_consumed = True

        # lookahead_buffer is a LIFO queue, return the left-most element
        if self.lookahead_buffer:
            return self.lookahead_buffer.pop(0)
        else:
            # no more data - clear memory for old lookahead_buffer list
            # and signal the end of data by raising StopIteration
            self.lookahead_buffer = []
            raise StopIteration()


class NewLogLineDetector:
    """
    Callable class used as a key function for itertools.groupby to detect log lines
    that don't start with a timestamp, and to group them with the last line that did
    have a timestamp.
    """
    def __init__(self):
        self._cur_dt = datetime.min

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
            sample.py: line 32
                divide(100, 0)
            sample.py: line 8
                return a / b
        ZeroDivisionError: division by zero
        2023-07-14 08:00:06 INFO   User authentication failed

    to two log entries.
    """
    def __init__(
            self,
            time_filter: Optional[Callable[[datetime], bool]] = None,
            *,
            include_non_timestamped_lines: bool = True
    ):
        self._newlogline_detector = NewLogLineDetector()
        self._time_filter_fn = time_filter or (lambda x: True)
        self.include_non_timestamped_lines = include_non_timestamped_lines

    def __call__(self, log_seq: Iterable[tuple[datetime, str]]) -> Generator[tuple[datetime, str], None, None]:
        for timestamp, lines in WindowedSort(
                window=40,
                seq=((a, list(b)) for a, b in groupby(log_seq, key=self._newlogline_detector)),
                key=itemgetter(0)
        ):
            try:
                if self._time_filter_fn(timestamp):
                    if not self.include_non_timestamped_lines:
                        lines = (line for line in lines if line[0] is not None)
                    log_body = (
                        "\n".join(line[1] for line in lines)
                    )
                    yield timestamp, log_body
            except StopIteration:
                break


if __name__ == '__main__':
    from pathlib import Path
    from timestamp_wrapper import TimestampedLineTransformer
    log_lines = (Path("files") / "log1.txt").read_text().splitlines()
    transformer = TimestampedLineTransformer.make_transformer_from_sample_line(log_lines[0])

    for collapsed in MultilineLogCollapser()(transformer(line) for line in log_lines):
        print(collapsed)
