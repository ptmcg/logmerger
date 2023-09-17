from datetime import datetime
import textwrap
import types

import littletable as lt
from rich.text import Text
from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.validation import Function, Integer, Validator, ValidationResult
from textual.widgets import Button, DataTable, Footer, Input, Label


class TimestampValidator(Validator):
    @staticmethod
    def convert_time_str(s: str) -> datetime:
        from .log_merger import VALID_INPUT_TIME_FORMATS, parse_time_using
        return parse_time_using(s, VALID_INPUT_TIME_FORMATS)

    def __init__(self, min_time=None, max_time=None):
        super().__init__("Invalid timestamp")
        self.min_time = self.convert_time_str(min_time) if min_time else datetime.min
        self.max_time = self.convert_time_str(max_time) if max_time else datetime.max

    def validate(self, value: str) -> ValidationResult:
        try:
            ts = self.convert_time_str(value)
            if not self.min_time <= ts <= self.max_time:
                message = {
                    (True, True): f"value must be between {self.min_time} and {self.max_time}",
                    (True, False): f"value must be greater than {self.min_time}",
                    (False, True): f"value must be less than {self.max_time}",
                }[self.min_time != datetime.min, self.max_time != datetime.max]
                raise ValueError(message)
        except ValueError as ve:
            return self.failure(str(ve).capitalize())
        else:
            return self.success()


class ModalInputDialog(ModalScreen[str]):
    """
    A modal dialog for getting a single input from the user.
    (cribbed from https://github.com/Textualize/frogmouth/blob/main/frogmouth/dialogs/input_dialog.py)
    """

    DEFAULT_CSS = """
    ModalInputDialog {
        align: center middle;
    }

    ModalInputDialog > Vertical {
        background: $panel;
        height: auto;
        width: auto;
        border: thick $primary;
    }

    ModalInputDialog > Vertical > * {
        width: auto;
        height: auto;
    }

    ModalInputDialog Input {
        width: 40;
        margin: 1;
    }

    ModalInputDialog Label {
        margin-left: 2;
    }

    ModalInputDialog Button {
        margin-right: 1;
    }

    ModalInputDialog #buttons {
        width: 100%;
        align-horizontal: right;
        padding-right: 1;
    }
    """
    """The default styling for the input dialog."""

    BINDINGS = [
        Binding("escape", "app.pop_screen", "", show=False),
    ]
    """Bindings for the dialog."""

    def __init__(
            self,
            prompt: str,
            initial: str | None = None,
            validator: Validator = None
    ) -> None:
        """Initialise the input dialog.

        Args:
            prompt: The prompt for the input.
            initial: The initial value for the input.
        """
        super().__init__()
        self._prompt = prompt
        """The prompt to display for the input."""
        self._initial = initial
        """The initial value to use for the input."""
        self._validator = validator or Function(function=lambda s: True)

    def compose(self) -> ComposeResult:
        """Compose the child widgets."""
        with Vertical():
            with Vertical(id="input"):
                yield Label(self._prompt)
                yield Input(
                    self._initial or "",
                    validators=[self._validator],
                )
            with Horizontal(id="buttons"):
                yield Button("OK", id="ok", variant="primary")
                yield Button("Cancel", id="cancel")

    def on_mount(self) -> None:
        """Set up the dialog once the DOM is ready."""
        self.query_one(Input).focus()

    @on(Button.Pressed, "#cancel")
    def cancel_input(self) -> None:
        """Cancel the input operation."""
        self.dismiss()

    @on(Input.Submitted)
    @on(Button.Pressed, "#ok")
    def accept_input(self) -> None:
        """Accept and return the input."""
        if ((value := self.query_one(Input).value.strip())
                and self._validator.validate(value).is_valid):
            self.dismiss(value)
        else:
            self.dismiss()


class InteractiveLogMergeViewerApp(App):
    """
    Class to display merged results using textual TUI.
    """

    BINDINGS = [
        Binding(key="q", action="quit", description="Quit"),
        Binding(key="f", action="find", description="Find"),
        Binding(key="n", action="find_next", description="Next"),
        Binding(key="p", action="find_prev", description="Prev"),
        Binding(key="l", action="goto_line", description="Go to line"),
        Binding(key="t", action="goto_timestamp", description="Go to timestamp"),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.log_file_names: list[str] = []
        self.merged_log_lines_table: lt.Table = None
        self.display_width: int = 0
        self.show_line_numbers: bool = False
        self.current_search_string: str = ""
        self.current_goto_timestamp_string: str = ""

    def config(
            self,
            log_file_names: list[str],
            display_width: int,
            show_line_numbers: bool,
            merged_log_lines_table: lt.Table,
    ):
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

        screen_width = self.display_width or self.size.width
        # guesstimate how much width each file will require
        timestamp_allowance = 25
        line_number_allowance = 8 if self.show_line_numbers else 0
        screen_width_for_files = screen_width - timestamp_allowance - line_number_allowance
        width_per_file = int(screen_width_for_files * 0.9 // len(self.log_file_names))

        def max_line_count(sseq: list[str]):
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
                display_table.add_row(
                    Text(wrapped_row_values[0], justify="right")
                    if self.show_line_numbers else wrapped_row_values[0],
                    *wrapped_row_values[1:],
                    height=max_line_count(wrapped_row_values))
            else:
                display_table.add_row(
                    Text(row_values[0], justify="right")
                    if self.show_line_numbers else row_values[0],
                    *row_values[1:],
                    height=max_line_count(row_values))

    #
    # methods to support go to find/next/prev search functions
    #

    def action_find(self):
        self.app.push_screen(
            ModalInputDialog(
                "Find:",
                initial=self.current_search_string,
            ),
            self.save_search_string_and_move_to_next
        )

    def action_find_next(self):
        self.move_to_next_search_line()

    def action_find_prev(self):
        self.move_to_prev_search_line()

    def get_current_cursor_line(self) -> int:
        dt: DataTable = self.query_one(DataTable)
        return dt.cursor_row

    def save_search_string_and_move_to_next(self, search_str):
        if not search_str:
            return

        self.current_search_string = search_str
        self.move_to_next_search_line()

    def _move_to_relative_search_line(self, move_delta: int, limit: int):
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

    def move_to_next_search_line(self):
        self._move_to_relative_search_line(1, len(self.merged_log_lines_table))

    def move_to_prev_search_line(self):
        self._move_to_relative_search_line(-1, -1)

    #
    # methods to support go to line function
    #

    def action_goto_line(self):
        self.app.push_screen(
            ModalInputDialog("Go to line:", validator=Integer(minimum=1)),
            self.move_cursor_to_line_number
        )

    def move_cursor_to_line_number(self, line_number_str):
        # convert 1-based line number to 0-based
        line_number = int(line_number_str) - 1

        dt_widget: DataTable = self.query_one(DataTable)
        dt_widget.move_cursor(row=line_number, animate=False)

    #
    # methods to support go to timestamp function
    #

    def action_goto_timestamp(self):
        self.app.push_screen(
            ModalInputDialog(
                "Go to timestamp:",
                initial=self.current_goto_timestamp_string,
                validator=TimestampValidator()
            ),
            self.move_cursor_to_timestamp
        )

    def move_cursor_to_timestamp(self, timestamp_str: str):
        self.current_goto_timestamp_string = timestamp_str

        # normalize input string to timestamps in merged log lines table
        ts = TimestampValidator.convert_time_str(timestamp_str)
        timestamp_str = ts.strftime("%Y-%m-%d %H:%M:%S.%f")[:23]

        line_for_timestamp = next(
            (
                i for i, row in enumerate(self.merged_log_lines_table, start=1)
                if row.timestamp >= timestamp_str
            ),
            len(self.merged_log_lines_table)
        )
        self.move_cursor_to_line_number(str(line_for_timestamp))
