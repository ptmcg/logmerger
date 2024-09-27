import io
import os
import sys
from types import SimpleNamespace
from logmerger.logmerger import LogMergerApplication
from contextlib import redirect_stdout

def _untable(s):
    # s = s.replace(" | ", " ")
    ret = s.splitlines()[1:]
    i_ret = iter(ret)
    for line in i_ret:
        if line.startswith('|---'):
            break
    return [
        line.removeprefix("| ").removesuffix(" |").rstrip()
        for line in i_ret
    ]

class LogMergerTestApp:
    def __init__(self, input_files, **kwargs):
        if isinstance(input_files, str):
            input_files = [input_files]

        args = dict(
            files=input_files,
            interactive=False,
            inline=False,
            output="-",
            start=None,
            end=None,
            width=300,
            line_numbers=False,
            show_clock=False,
            csv=None,
            encoding="UTF-8",
            timestamp_formats=[],
            autoclip=False,
            demo=False,
            ignore_non_timestamped=False,
        )
        args.update(kwargs)
        self.args = SimpleNamespace(**args)

    def __call__(self) -> list[str]:
        with redirect_stdout(io.StringIO()) as capture:
            # use a wide virtual console to suppress wrapping of columns
            save_columns = os.environ.get("COLUMNS", "")
            os.environ["COLUMNS"] = "10000"
            LogMergerApplication(self.args).run()  # noqa
            os.environ["COLUMNS"] = save_columns

        return _untable(capture.getvalue())


if __name__ == '__main__':
    from pprint import pprint
    pprint(LogMergerTestApp(sys.argv[1:])(), width=300)
