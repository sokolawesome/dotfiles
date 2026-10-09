"""Console helpers shared by the scripts in this directory."""

from collections.abc import Callable

from rich.console import Console, RenderableType
from rich.markup import escape
from rich.panel import Panel
from rich.prompt import Confirm
from rich.table import Table

console = Console()

QUESTION = "bold cyan"
SUCCESS = "bold green"
WARNING = "yellow"
FAILURE = "red"
DIM = "dim"

INTERRUPTED = 130


def plain_table() -> Table:
    return Table(box=None, pad_edge=False, show_edge=False, show_header=False)


def show_panel(content: RenderableType, title: str, border: str = "cyan") -> None:
    console.print(Panel(content, title=title, border_style=border, padding=(0, 1)))


def print_error(message: str) -> None:
    console.print(f"[{FAILURE}]error:[/] {escape(message)}")


def print_cancelled() -> None:
    console.print(f"[{WARNING}]cancelled[/]")


def confirm(question: str) -> bool:
    return Confirm.ask(f"[{QUESTION}]{question}[/]", default=False, console=console)


def plural(count: int, word: str) -> str:
    return f"{count} {word}" if count == 1 else f"{count} {word}s"


def run_cli(main: Callable[[], int]) -> None:
    try:
        code = main()
    except (KeyboardInterrupt, EOFError):
        console.print()
        print_cancelled()
        code = INTERRUPTED
    raise SystemExit(code)
