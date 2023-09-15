import textwrap
import types

import littletable as lt
from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import DataTable, Footer


class InteractiveLogMergeViewerApp(App):
    """
    Class to display merged results using textual TUI.
    """

    BINDINGS = [
        Binding(key="q", action="quit", description="Quit"),
    ]

    def config(
            self,
            log_file_names: list[str],
            display_width: int,
            show_line_numbers: bool,
            merged_log_lines_table: lt.Table,
    ):
        self.log_file_names = log_file_names  # noqa
        self.merged_log_lines_table = merged_log_lines_table  # noqa
        self.display_width = display_width  # noqa
        self.show_line_numbers = show_line_numbers  # noqa

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
        width_per_file = int((screen_width - 25) * 0.94 // len(self.log_file_names))

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
