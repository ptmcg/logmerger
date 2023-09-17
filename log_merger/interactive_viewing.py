import textwrap
import types

import littletable as lt
from rich.text import Text
from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.validation import Validator, Integer, Function
from textual.widgets import Button, DataTable, Footer, Input, Label


class ModalInputDialog(ModalScreen[str]):
    """
    A modal dialog for getting a single input from the user.
    (cribbed from https://github.com/Textualize/frogmouth/blob/main/frogmouth/dialogs/input_dialog.py)
    """

    DEFAULT_CSS = """
    InputDialog {
        align: center middle;
    }

    InputDialog > Vertical {
        background: $panel;
        height: auto;
        width: auto;
        border: thick $primary;
    }

    InputDialog > Vertical > * {
        width: auto;
        height: auto;
    }

    InputDialog Input {
        width: 40;
        margin: 1;
    }

    InputDialog Label {
        margin-left: 2;
    }

    InputDialog Button {
        margin-right: 1;
    }

    InputDialog #buttons {
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
        Binding(key="l", action="goto_line", description="Go to line"),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.log_file_names: list[str] = []
        self.merged_log_lines_table: lt.Table = None
        self.display_width: int = 0
        self.show_line_numbers: bool = False

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

    # methods to support go to line function
    def action_goto_line(self):
        self.app.push_screen(
            ModalInputDialog("Go to line:", validator=Integer(minimum=1)),
            self.move_to_line
        )

    def move_to_line(self, line_str):
        # convert 1-based line number to 0-based
        line = int(line_str) - 1

        dt_widget: DataTable = self.query_one(DataTable)
        dt_widget.move_cursor(row=line, animate=False)
