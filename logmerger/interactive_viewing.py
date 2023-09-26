from functools import partial
import textwrap
import types

import littletable as lt
from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.validation import Integer
from textual.widgets import DataTable, Footer

from logmerger.tui.dialogs import ModalInputDialog, ModalAboutDialog
from logmerger.tui.validators import TimestampValidator


class InteractiveLogMergeViewerApp(App):
    """
    Class to display merged results using textual TUI.
    """
    TITLE = "logmerger"

    BINDINGS = [
        Binding(key="q", action="quit", description="Quit"),
        Binding(key="ctrl+d", action="toggle_dark", description="Toggle Dark Mode"),
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
        self.current_search_string: str = ""
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
    ) -> None:
        self.log_file_names = log_file_names
        self.merged_log_lines_table = merged_log_lines_table
        self.display_width = display_width
        self.show_line_numbers = show_line_numbers

    def compose(self) -> ComposeResult:
        yield DataTable()
        yield Footer()

    def on_mount(self) -> None:
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

        def max_line_count(sseq: list[str]) -> int:
            """
            The number of lines for this row is the maximum number of newlines
            in any value, plus 1.
            """
            return max(s.count("\n") for s in sseq) + 1

        line_ns: types.SimpleNamespace
        for line_ns in self.merged_log_lines_table:
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
                    if "\n" in cell_value or len(cell_value) > width_per_file:
                        cell_lines = (
                            "\n".join(textwrap.wrap(rvl, width_per_file))
                            for rvl in cell_value.splitlines()
                        )
                        wrapped_row_values.append("\n".join(cell_lines))
                    else:
                        wrapped_row_values.append(cell_value)
            else:
                # no need to wrap any values in this row
                wrapped_row_values = row_values

            display_table.add_row(
                Text(wrapped_row_values[0], justify="right")
                if self.show_line_numbers else wrapped_row_values[0],
                *wrapped_row_values[1:],
                height=max_line_count(wrapped_row_values))

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
        self.move_to_next_search_line()

    def action_find_prev(self) -> None:
        self.move_to_prev_search_line()

    def get_current_cursor_line(self) -> int:
        dt: DataTable = self.query_one(DataTable)
        return dt.cursor_row

    def save_search_string_and_move_to_next(self, search_str) -> None:
        if not search_str:
            return

        self.current_search_string = search_str
        self.move_to_next_search_line()

    def _move_to_relative_search_line(self, move_delta: int, limit: int) -> None:
        search_string = self.current_search_string.lower()

        cur_line_number = self.get_current_cursor_line() + move_delta
        while cur_line_number != limit:
            row = self.merged_log_lines_table[cur_line_number]

            # see if any log line at this row contains the search string
            if any(
                    search_string in getattr(row, fname).lower()
                    for fname in self.log_file_names
            ):
                self.move_cursor_to_line_number(str(cur_line_number + 1))
                break

            # move on to the next line
            cur_line_number += move_delta
        else:
            self.bell()

    def move_to_next_search_line(self) -> None:
        self._move_to_relative_search_line(1, len(self.merged_log_lines_table))

    def move_to_prev_search_line(self) -> None:
        self._move_to_relative_search_line(-1, -1)

    #
    # methods to support go to line function
    #

    def action_goto_line(self) -> None:
        self.app.push_screen(
            ModalInputDialog("Go to line:", validator=Integer(minimum=1)),
            self.move_cursor_to_line_number
        )

    def move_cursor_to_line_number(self, line_number_str: str) -> None:
        # convert 1-based line number to 0-based
        line_number = int(line_number_str) - 1

        dt_widget: DataTable = self.query_one(DataTable)
        dt_widget.move_cursor(row=line_number, animate=False)

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
        ts = self.timestamp_validator.convert_time_str(timestamp_str)
        timestamp_str = ts.strftime("%Y-%m-%d %H:%M:%S.%f")[:23]

        line_for_timestamp = next(
            (
                i for i, row in enumerate(self.merged_log_lines_table, start=1)
                if row.timestamp >= timestamp_str
            ),
            len(self.merged_log_lines_table)
        )
        self.move_cursor_to_line_number(str(line_for_timestamp))

    #
    # methods to support help/about
    #

    def action_help_about(self) -> None:
        from logmerger.about import text

        self.app.push_screen(
            ModalAboutDialog(content=text)
        )
