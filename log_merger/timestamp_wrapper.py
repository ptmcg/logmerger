from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re

from typing import TypeVar


T = TypeVar("T")


class TimestampedLineTransformer:
    """
    Class to detect timestamp formats, and auto-transform lines that start with that timestamp into
    (timestamp, rest of the line) tuples.
    """
    _SUPPORTED_FORMATS = [
            (r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})\s", "%Y-%m-%d %H:%M:%S,%f",),
            (r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s", "%Y-%m-%d %H:%M:%S",),
    ]

    @classmethod
    def make_transformer_from_file(cls, file_ref) -> TimestampedLineTransformer:
        if isinstance(file_ref, (str, Path)):
            with open(file_ref) as log_file:
                first_line = log_file.readline()
        else:
            first_line = file_ref.readline()

        return cls.make_transformer_from_sample_line(first_line)

    @classmethod
    def make_transformer_from_sample_line(cls, s: str) -> TimestampedLineTransformer:
        for patt, strptime_format in cls._SUPPORTED_FORMATS:
            if re.match(patt, s):
                return cls(patt, strptime_format)
        raise ValueError(f"no match for any timestamp pattern in {s!r}")

    def __init__(self, pattern: str, strptime_format: str):
        self._re_pattern_match = re.compile(pattern).match
        self.pattern = pattern
        self.strptime_format = strptime_format

    def __call__(self, obj: T) -> tuple[datetime | None, T]:
        m = self._re_pattern_match(obj)
        if m:
            # create (datetime, str) tuple - clip leading datetime string from
            # the log string, so that it doesn't duplicate when presented
            return datetime.strptime(m[1], self.strptime_format), obj[m.span()[1]:]
        else:
            # no leading timestamp, just return None and the original string
            return None, obj


if __name__ == '__main__':
    files = "log1.txt log3.txt".split()
    xformers = [TimestampedLineTransformer.make_transformer_from_file(Path("files") / f) for f in files]
    for fname, xformer in zip(files, xformers):
        log_lines = (Path("files") / fname).read_text().splitlines()
        for ln in log_lines[:3]:
            print(xformer(ln))
