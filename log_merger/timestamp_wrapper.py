from __future__ import annotations

import os
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
    pattern = ""
    match = lambda s: False

    def __init_subclass__(cls):
        cls.match = re.compile(cls.pattern).match

    @classmethod
    def make_transformer_from_file(cls, file_ref) -> TimestampedLineTransformer:
        if isinstance(file_ref, (str, Path)):
            with open(file_ref) as log_file:
                first_line = log_file.readline()
        else:
            first_line = file_ref.readline()

        xformer = cls.make_transformer_from_sample_line(first_line)
        xformer.add_file_info(Path(file_ref))
        return xformer

    @classmethod
    def make_transformer_from_sample_line(cls, s: str) -> TimestampedLineTransformer:
        for subcls in cls.__subclasses__():
            if subcls.match(s):
                return subcls()
        raise ValueError(f"no match for any timestamp pattern in {s!r}")

    def __init__(self, pattern: str, strptime_format: str):
        self._re_pattern_match = re.compile(pattern).match
        self.pattern: str = pattern
        self.strptime_format: str = strptime_format
        self.file_info: Path = None
        self.file_stat: os.stat_result = None

    def add_file_info(self, file_info: Path) -> None:
        self.file_info = file_info
        self.file_stat = file_info.stat()

    def __call__(self, obj: T) -> tuple[datetime | None, T]:
        m = self._re_pattern_match(obj)
        if m:
            # create (datetime, str) tuple - clip leading datetime string from
            # the log string, so that it doesn't duplicate when presented
            return datetime.strptime(m[1], self.strptime_format), obj[m.span()[1]:]
        else:
            # no leading timestamp, just return None and the original string
            return None, obj


class YMDHMScommaF(TimestampedLineTransformer):
    # log files with timestamp "YYYY-MM-DD HH:MM:SS,SSS"
    pattern = r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})\s"
    strptime_format = "%Y-%m-%d %H:%M:%S,%f"

    def __init__(self):
        super().__init__(self.pattern, self.strptime_format)


class YMDHMSdotF(TimestampedLineTransformer):
    # log files with timestamp "YYYY-MM-DD HH:MM:SS.SSS"
    pattern = r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})\s"
    strptime_format = "%Y-%m-%d %H:%M:%S.%f"

    def __init__(self):
        super().__init__(self.pattern, self.strptime_format)


class YMDHMS(TimestampedLineTransformer):
    # log files with timestamp "YYYY-MM-DD HH:MM:SS"
    pattern = r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s"
    strptime_format = "%Y-%m-%d %H:%M:%S"

    def __init__(self):
        super().__init__(self.pattern, self.strptime_format)


class BDHMS(TimestampedLineTransformer):
    # syslog files with timestamp "mon day hh:mm:ss"
    # (note, year is omitted so let's guess from the log file's create date)
    pattern = r"([JFMASOND][a-z]{2}\s(\s|\d)\d \d{2}:\d{2}:\d{2})\s"
    strptime_format = "%b %d %H:%M:%S"

    def __init__(self):
        super().__init__(self.pattern, self.strptime_format)

    def __call__(self, obj: T) -> tuple[datetime | None, T]:
        # this format does not have a year so assume the file's create time year
        if self.file_stat is not None and self.file_stat.st_ctime:
            date_year = datetime.fromtimestamp(self.file_stat.st_ctime).year
        else:
            date_year = datetime.now().year

        dt, obj = super().__call__(obj)
        if dt is not None:
            dt = dt.replace(year=date_year)
        return dt, obj


if __name__ == '__main__':
    files = "log1.txt log3.txt syslog1.txt".split()
    file_dir = Path(__file__).parent.parent / "files"
    xformers = [TimestampedLineTransformer.make_transformer_from_file(file_dir / f) for f in files]
    for fname, xformer in zip(files, xformers):
        log_lines = (file_dir / fname).read_text().splitlines()
        for ln in log_lines[:3]:
            print(xformer(ln))
