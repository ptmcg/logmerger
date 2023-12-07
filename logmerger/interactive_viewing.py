import asyncio
from datetime import timedelta, datetime
from functools import partial
import itertools
import re
import textwrap
import time
from typing import NamedTuple
import types

import littletable as lt
from rich.text import Text
from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.validation import Integer
from textual.widgets import DataTable, Footer

from logmerger.tui.dialogs import ModalInputDialog, ModalAboutDialog, ModalJumpDialog
from logmerger.tui.validators import TimestampValidator


def _max_line_count(sseq: list[str]) -> int:
    """
    The number of lines for this row is the maximum number of newlines
    in any value, plus 1.
    """
    return max(s.count("\n") for s in sseq) + 1


class Jump(NamedTuple):
    qty: int
    units: str
    delta_time: timedelta = None

    def __neg__(self):
        return Jump(
            -self.qty,
            self.units,
            -self.delta_time if self.delta_time else None
        )

    def as_string(self):
        return f"{self.qty}{self.units[:1]}"

    @classmethod
    def from_string(cls, s: str):
        jump_re = r"([1-9]\d*)\s*(l|us|ms|s|m|h|d)"
        parts = re.match(jump_re, s.lower())
        if not parts:
            return None

        qty_str, units = parts.groups()
        if units == "l":
            return cls(int(qty_str), units)
        else:
            units_map = {
                "us": "microseconds",
                "ms": "milliseconds",
                "s": "seconds",
                "m": "minutes",
                "h": "hours",
                "d": "days",
            }
            td_args = {units_map[units]: int(qty_str)}
            return cls(int(qty_str), units, timedelta(**td_args))


class InteractiveLogMergeViewerApp(App):
    """
    Class to display merged results using textual TUI.
    """
    TITLE = "logmerger"

    BINDINGS = [
        Binding(key="q", action="quit", description="Quit"),
        Binding(key="ctrl+d", action="toggle_dark", description="Toggle Dark Mode"),
        Binding(key="j", action="jump", description="Jump"),
        Binding(key="f", action="find", description="Find"),
        Binding(key="n", action="find_next", description="Next"),
        Binding(key="p", action="find_prev", description="Prev"),
        Binding(key="l", action="goto_line", description="Go to line"),
        Binding(key="t", action="goto_timestamp", description="Go to timestamp"),
        Binding(key="h", action="help_about", description="Help/About"),
    ]

    def __init__(self, *args, **kwargs):
        from logmerger.logmerger import parse_time_using, VALID_INPUT_TIME_FORMATS

        super().__init__(*args, **kwargs)
        self.log_file_names: list[str] = []
        self.merged_log_lines_table: lt.Table = None  # noqa
        self.display_width: int = 0
        self.show_line_numbers: bool = False
        self.show_merged_logs_inline: bool = False
        self.current_search_string: str = ""
        self.current_jump: Jump = None  # noqa
        self.current_goto_timestamp_string: str = ""
        self.timestamp_validator = TimestampValidator(
            timestamp_parser=partial(parse_time_using, formats=VALID_INPUT_TIME_FORMATS),
        )

    def config(
            self,
            *,
            log_file_names: list[str],
            display_width: int,
            show_line_numbers: bool,
            merged_log_lines_table: lt.Table,
            show_merged_logs_inline: bool,
    ) -> None:
        self.log_file_names = log_file_names
        self.merged_log_lines_table = merged_log_lines_table
        self.display_width = display_width
        self.show_line_numbers = show_line_numbers
        self.show_merged_logs_inline = show_merged_logs_inline

    def compose(self) -> ComposeResult:
        yield DataTable()
        yield Footer()

    def on_mount(self) -> None:
        if self.show_merged_logs_inline:
            self.load_data_inline()
        else:
            self.load_data_side_by_side()

    @work
    async def load_data_side_by_side(self):
        fixed_cols = 2 if self.show_line_numbers else 1
        col_names = self.merged_log_lines_table.info()["fields"]

        display_table = self.query_one(DataTable)
        display_table.cursor_type = "row"
        display_table.zebra_stripes = True
        display_table.fixed_columns = fixed_cols
        display_table.add_columns(*col_names)

        # guesstimate how much width to allocate to each file
        screen_width = self.display_width or self.size.width
        timestamp_allowance = 25
        line_number_allowance = 8 if self.show_line_numbers else 0
        screen_width_for_files = screen_width - timestamp_allowance - line_number_allowance
        width_per_file = int(screen_width_for_files * 0.9 // len(self.log_file_names))

        start = time.time()

        line_ns: types.SimpleNamespace
        for i, line_ns in enumerate(self.merged_log_lines_table, start=1):
            if i % 10 == 0:
                # give other UI tasks a chance to work
                await asyncio.sleep(0)
            row_values = list(vars(line_ns).values())

            # see if any text wrapping is required for this line
            # - check each cell to see if any line in the cell exceeds width_per_file
            # - if not, just add this row to the display_table
            if any(len(rv_line) > width_per_file
                   for rv in row_values
                   for rv_line in rv.splitlines()):
                # wrap individual cells (except never wrap the timestamp or leading line number)
                wrapped_row_values = row_values[:fixed_cols]
                for cell_value in row_values[fixed_cols:]:
                    if len(cell_value) > width_per_file or "\n" in cell_value:
                        cell_lines = (
                            "\n ".join(textwrap.wrap(rvl, width_per_file-1))
                            for rvl in cell_value.splitlines()
                        )
                        wrapped_row_values.append("\n".join(cell_lines).replace("[/", r"\[/"))
                    else:
                        wrapped_row_values.append(cell_value.replace("[/", r"\[/"))
            else:
                # no need to wrap any values in this row
                wrapped_row_values = [rv.replace("[/", r"\[/") for rv in row_values]

            display_table.add_row(
                Text(wrapped_row_values[0], justify="right")
                if self.show_line_numbers else wrapped_row_values[0],
                *wrapped_row_values[1:],
                height=_max_line_count(wrapped_row_values))

        elapsed = time.time() - start
        if elapsed > 10:
            self.bell()
            self.notify("Log data complete")

    @work
    async def load_data_inline(self):
        fixed_cols = 2 if self.show_line_numbers else 1
        file_names = self.merged_log_lines_table.info()["fields"]

        display_table = self.query_one(DataTable)
        display_table.cursor_type = "row"
        display_table.zebra_stripes = True
        display_table.fixed_columns = fixed_cols + 1
        if self.show_line_numbers:
            col_names = ['line']
        else:
            col_names = []
        col_names.extend(('timestamp', 'file', 'log'))
        display_table.add_columns(*col_names)

        # guesstimate how much width to allocate to each file
        screen_width = self.display_width or self.size.width
        timestamp_allowance = 25
        line_number_allowance = 8 if self.show_line_numbers else 0
        screen_width_for_files = screen_width - timestamp_allowance - line_number_allowance
        width_for_file_names = min(int(screen_width_for_files), max(len(fn)+1 for fn in file_names))
        width_for_content = screen_width_for_files - width_for_file_names

        start = time.time()

        line_ns: types.SimpleNamespace
        for i, line_ns in enumerate(self.merged_log_lines_table, start=1):
            if i % 10 == 0:
                # give other UI tasks a chance to work
                await asyncio.sleep(0)

            line_ns_vars = vars(line_ns)
            fixed_values = list(line_ns_vars.values())[:fixed_cols]
            line_data = {k: v for k, v in list(line_ns_vars.items())[fixed_cols:] if v.strip()}
            line_files = list(line_data)
            line_content = list(line_data.values())
            row_values = [*fixed_values, line_files, line_content]

            # wrap individual cells (except never wrap the timestamp or leading line number)
            wrapped_row_values = row_values[:fixed_cols]

            # get wrapped versions of each file and its content
            wrapped_file_names = [textwrap.wrap(fname, width_for_file_names-1) for fname in line_files]
            wrapped_file_content = [
                (
                    "\n".join(textwrap.wrap(content_line, width_for_content - 1))
                    for content_line in content.splitlines())
                for content in line_content
            ]

            row_merged_filenames = ""
            row_merged_filecontent = ""

            for fname, fcontent in zip(wrapped_file_names, wrapped_file_content):
                for fname_line, fcontent_line in itertools.zip_longest(fname, fcontent, fillvalue=""):
                    row_merged_filenames += fname_line + "\n"
                    row_merged_filecontent += fcontent_line + "\n"

            wrapped_row_values.extend((row_merged_filenames, row_merged_filecontent))

            display_table.add_row(
                Text(wrapped_row_values[0], justify="right")
                if self.show_line_numbers else wrapped_row_values[0],
                *wrapped_row_values[1:],
                height=_max_line_count(wrapped_row_values),
            )

        elapsed = time.time() - start
        if elapsed > 10:
            self.bell()
            self.notify("Log data complete")

    #
    # methods to support go to find/next/prev search functions
    #

    def action_find(self) -> None:
        self.app.push_screen(
            ModalInputDialog(
                "Find:",
                initial=self.current_search_string,
            ),
            self.save_search_string_and_move_to_next
        )

    def action_find_next(self) -> None:
        if self.current_search_string:
            self.move_to_next_search_line()
        elif self.current_jump:
            self.jump(self.current_jump)
        else:
            self.bell()

    def action_find_prev(self) -> None:
        if self.current_search_string:
            self.move_to_prev_search_line()
        elif self.current_jump:
            self.jump(-self.current_jump)
        else:
            self.bell()

    def get_current_cursor_line_index(self) -> int:
        dt: DataTable = self.query_one(DataTable)
        return dt.cursor_row

    def get_current_cursor_timestamp(self) -> datetime:
        dt: DataTable = self.query_one(DataTable)
        current_rec = self.merged_log_lines_table[dt.cursor_row]
        timestamp_str = current_rec.timestamp
        if timestamp_str:
            return self.timestamp_validator.convert_time_str(timestamp_str)
        return None

    def save_search_string_and_move_to_next(self, search_str) -> None:
        if not search_str:
            return

        self.current_search_string = search_str
        self.move_to_next_search_line()
        self.current_jump = None

    def _move_to_relative_search_line(self, move_delta: int, limit: int) -> None:
        search_string = self.current_search_string.lower()

        cur_line_number = self.get_current_cursor_line_index() + move_delta
        while cur_line_number != limit:
            row = self.merged_log_lines_table[cur_line_number]

            # see if any log line at this row contains the search string
            if any(
                    search_string in getattr(row, fname).lower()
                    for fname in self.log_file_names
            ):
                self.move_cursor_to_line_number(cur_line_number)
                break

            # move on to the next line
            cur_line_number += move_delta
        else:
            self.bell()

    def move_to_next_search_line(self) -> None:
        if not self.current_search_string:
            self.bell()
            return
        self._move_to_relative_search_line(1, len(self.merged_log_lines_table))

    def move_to_prev_search_line(self) -> None:
        if not self.current_search_string:
            self.bell()
            return
        self._move_to_relative_search_line(-1, -1)

    #
    # methods to support go to line function
    #

    def action_goto_line(self) -> None:
        self.app.push_screen(
            ModalInputDialog("Go to line:", validator=Integer(minimum=1)),
            self.move_cursor_to_line_number_1_based
        )

    def move_cursor_to_line_number(self, line_number: int) -> None:
        if line_number >= len(self.merged_log_lines_table):
            line_number = len(self.merged_log_lines_table) - 1
        elif line_number < 0:
            line_number = 0

        dt_widget: DataTable = self.query_one(DataTable)
        dt_widget.move_cursor(row=line_number, animate=False)

    def move_cursor_to_line_number_1_based(self, line_number_str: str) -> None:
        # convert 1-based line number to 0-based
        line_number = int(line_number_str) - 1
        self.move_cursor_to_line_number(line_number)

    #
    # methods to support go to timestamp function
    #

    def action_goto_timestamp(self) -> None:
        self.app.push_screen(
            ModalInputDialog(
                "Go to timestamp:",
                initial=self.current_goto_timestamp_string,
                validator=self.timestamp_validator,
            ),
            self.move_cursor_to_timestamp
        )

    def move_cursor_to_timestamp(self, timestamp_str: str) -> None:
        self.current_goto_timestamp_string = timestamp_str

        # normalize input string to timestamps in merged log lines table
        target_timestamp = self.timestamp_validator.convert_time_str(timestamp_str)
        target_timestamp_str = target_timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:23]

        current_row_time = self.get_current_cursor_timestamp()
        cur_line_number = self.get_current_cursor_line_index()

        if current_row_time == target_timestamp:
            return

        if current_row_time < target_timestamp:
            while cur_line_number < len(self.merged_log_lines_table) - 1:
                if self.merged_log_lines_table[cur_line_number].timestamp >= target_timestamp_str:
                    break
                cur_line_number += 1
        else:
            while cur_line_number > 0:
                if self.merged_log_lines_table[cur_line_number].timestamp <= target_timestamp_str:
                    break
                cur_line_number -= 1

        self.move_cursor_to_line_number(cur_line_number)

    #
    # methods to support jumping
    #

    def jump(self, j: Jump):
        if j is None:
            self.app.bell()
            return

        current_line = self.get_current_cursor_line_index()

        if j.units == "l":
            # jump by 'n' lines
            self.move_cursor_to_line_number(current_line + j.qty)

        else:
            # jump by time interval
            current_time = self.get_current_cursor_timestamp()
            if current_time is not None:
                to_timestamp = (current_time + j.delta_time).strftime("%Y-%m-%d %H:%M:%S.%f")[:23]
                self.move_cursor_to_timestamp(to_timestamp)
            else:
                self.app.bell()

    def save_jump_and_jump(self, s: str):
        new_jump = Jump.from_string(s)
        if new_jump is None:
            self.app.bell()
            return

        self.current_jump = new_jump
        self.jump(self.current_jump)
        self.current_search_string = ""

    def action_jump(self):
        self.app.push_screen(
            ModalJumpDialog(
                r"Jump (#\[lsmhd]):",
                initial=self.current_jump.as_string() if self.current_jump else "",
            ),
            self.save_jump_and_jump
        )

    #
    # methods to support help/about
    #

    def action_help_about(self) -> None:
        from logmerger.about import text

        self.app.push_screen(
            ModalAboutDialog(content=text)
        )
