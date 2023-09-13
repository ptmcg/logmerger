from __future__ import annotations

import abc
import types
import typing


class FileReader:
    @classmethod
    def get_reader(cls, name: str, encoding: str) -> FileReader:
        for subcls in cls.__subclasses__():
            if subcls is TextFileReader:
                continue
            if subcls._can_read(name):
                return subcls(name, encoding)
        return TextFileReader(name, encoding)

    @classmethod
    @abc.abstractmethod
    def _can_read(cls, fname: str) -> bool:
        """Override in subclasses"""

    @abc.abstractmethod
    def _close_reader(self):
        """Override in subclasses"""

    def __init__(self, file_name: str, encoding: str):
        self.file_name = file_name
        self.encoding = encoding
        self._iter = iter(())

    def __iter__(self):
        return self._iter

    def __next__(self):
        try:
            return next(self._iter)
        except StopIteration:
            self._close_reader()
            raise


class TextFileReader(FileReader):
    @classmethod
    def _can_read(cls, fname: str) -> bool:
        return True

    def __init__(self, fname: str, encoding: str):
        super().__init__(fname, encoding)
        self._close_obj = open(self.file_name, encoding=self.encoding)
        self._iter = self._close_obj

    def _close_reader(self):
        self._close_obj.close()


class GzipFileReader(FileReader):
    @classmethod
    def _can_read(cls, fname: str) -> bool:
        return fname.endswith(".gz")

    def __init__(self, fname: str, encoding: str):
        import gzip

        super().__init__(fname, encoding)
        self._close_obj = gzip.GzipFile(filename=self.file_name)
        self._iter = (s.decode(self.encoding) for s in self._close_obj)
        # make fake stat result
        self.file_stat = types.SimpleNamespace(st_ctime=self._close_obj.mtime)

    def _close_reader(self):
        self._close_obj.close()
