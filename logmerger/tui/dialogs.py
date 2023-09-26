from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.validation import Function, Validator
from textual.widgets import Button, Input, Label, MarkdownViewer


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
        value = self.query_one(Input).value.strip()
        if value and self._validator.validate(value).is_valid:
            self.dismiss(value)
        else:
            self.dismiss()


class ModalAboutDialog(ModalScreen[type(None)]):
    DEFAULT_CSS = """
    ModalAboutDialog {
        align: center middle;
        width: 80%;
        height: 80%;
    }

    ModalAboutDialog > Vertical {
        background: $panel;
        height: auto;
        width: auto;
        border: thick $primary;
    }

    ModalAboutDialog > Vertical > * {
        width: auto;
        height: auto;
    }

    ModalAboutDialog MarkdownViewer {
        align-horizontal: center;
        height: 24;
        width: 72;
    }

    ModalAboutDialog Button {
        margin-top: 1;
    }

    ModalAboutDialog #buttons {
        width: 100%;
        align-horizontal: center;
    }
    """
    """The default styling for the about dialog."""

    BINDINGS = [
        Binding("escape", "app.pop_screen", "", show=False),
        Binding("enter", "app.pop_screen", "", show=False),
    ]
    """Bindings for the dialog."""

    def __init__(
            self,
            content: str,
    ) -> None:
        """Initialise the input dialog.

        Args:
            content: The Markdown content.
        """
        super().__init__()
        self.content = content

    def compose(self) -> ComposeResult:
        """Compose the child widgets."""
        with Vertical():
            yield MarkdownViewer(
                self.content,
                show_table_of_contents=False,
            )
            with Horizontal(id="buttons"):
                yield Button("OK", id="ok", variant="primary")

    def on_mount(self) -> None:
        """Set up the dialog once the DOM is ready."""
        self.query_one(MarkdownViewer).focus()

    @on(Button.Pressed, "#ok")
    def ok_clicked(self) -> None:
        self.dismiss()
