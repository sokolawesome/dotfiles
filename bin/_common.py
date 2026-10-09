"""Console helpers shared by the scripts in this directory."""

import shutil
import subprocess
from collections.abc import Callable

from rich.console import Console, RenderableType
from rich.markup import escape
from rich.panel import Panel
from rich.table import Table
from rich.theme import Theme

THEME = Theme(
    {
        "question": "bold cyan",
        "success": "bold green",
        "warning": "yellow",
        "failure": "red",
        "changed": "bold yellow",
        "added": "green",
        "removed": "red",
        "name": "bold cyan",
    }
)

console = Console(theme=THEME)

INTERRUPTED = 130


def plain_table() -> Table:
    return Table(box=None, pad_edge=False, show_edge=False, show_header=False)


def show_panel(content: RenderableType, title: str, border: str = "cyan") -> None:
    console.print(Panel(content, title=title, border_style=border, padding=(0, 1)))


def print_error(message: str) -> None:
    console.print(f"[failure]error:[/] {escape(message)}")


def print_cancelled() -> None:
    console.print("[warning]cancelled[/]")


def plural(count: int, word: str) -> str:
    return f"{count} {word}" if count == 1 else f"{count} {word}s"


def notify(title: str, body: str) -> None:
    if shutil.which("notify-send"):
        subprocess.run(["notify-send", title, body], check=False)


def run_cli(main: Callable[[], int]) -> None:
    try:
        code = main()
    except (KeyboardInterrupt, EOFError):
        console.print()
        print_cancelled()
        code = INTERRUPTED
    raise SystemExit(code)
