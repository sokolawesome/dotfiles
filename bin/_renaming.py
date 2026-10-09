"""Preview, check and apply a batch of file renames inside one directory."""

from dataclasses import dataclass
from pathlib import Path

from _common import (
    DIM,
    FAILURE,
    QUESTION,
    SUCCESS,
    WARNING,
    confirm,
    console,
    plain_table,
    plural,
    print_cancelled,
    print_error,
    show_panel,
)
from rich.markup import escape
from rich.table import Table


@dataclass(frozen=True)
class Rename:
    source: Path
    target: str

    @property
    def settled(self) -> bool:
        return self.target == self.source.name

    @property
    def target_path(self) -> Path:
        return self.source.with_name(self.target)


def pad(digits: str | int, width: int) -> str:
    return f"{int(digits):0{width}d}"


def find_collisions(renames: list[Rename]) -> list[tuple[str, Path, Path]]:
    claimed: dict[str, Path] = {}
    collisions = []
    for rename in renames:
        previous = claimed.setdefault(rename.target, rename.source)
        if previous is not rename.source:
            collisions.append((rename.target, previous, rename.source))
    return collisions


def order_renames(
    pending: list[Rename], existing: set[str]
) -> tuple[list[Rename], list[Rename]]:
    occupied = set(existing)
    waiting = list(pending)
    ordered: list[Rename] = []
    while waiting:
        ready = [rename for rename in waiting if rename.target not in occupied]
        if not ready:
            break
        for rename in ready:
            occupied.discard(rename.source.name)
            occupied.add(rename.target)
        ordered += ready
        waiting = [rename for rename in waiting if rename not in ready]
    return ordered, waiting


def build_preview(renames: list[Rename]) -> Table:
    table = plain_table()
    table.add_column(overflow="ellipsis")
    table.add_column(justify="center", width=1)
    table.add_column(overflow="ellipsis")
    for rename in renames:
        if rename.settled:
            table.add_row(escape(rename.source.name), "·", f"[{DIM}]unchanged[/]")
        else:
            table.add_row(
                escape(rename.source.name),
                "→",
                f"[{SUCCESS}]{escape(rename.target)}[/]",
            )
    return table


def build_skipped(skipped: list[Path]) -> Table:
    table = plain_table()
    table.add_column(overflow="ellipsis")
    for path in skipped:
        table.add_row(f"[{WARNING}]{escape(path.name)}[/]")
    return table


def show_preview(renames: list[Rename], skipped: list[Path]) -> None:
    show_panel(build_preview(renames), "preview")
    if skipped:
        show_panel(build_skipped(skipped), "skipped", WARNING)
    settled = sum(1 for rename in renames if rename.settled)
    summary = f"{len(renames)} files"
    if settled:
        summary += f", {settled} already named"
    if skipped:
        summary += f", {len(skipped)} skipped"
    console.print(f"[{QUESTION}]{summary}[/]\n")


def show_collisions(collisions: list[tuple[str, Path, Path]]) -> None:
    print_error("two files resolve to the same name")
    for target, first, second in collisions:
        console.print(
            f"  [{FAILURE}]{escape(target)}[/] from [dim]{escape(first.name)}[/] and [dim]{escape(second.name)}[/]"
        )


def show_blocked(blocked: list[Rename]) -> None:
    print_error("these names are taken by files that would not move")
    for rename in blocked:
        console.print(
            f"  [{FAILURE}]{escape(rename.target)}[/] wanted by [dim]{escape(rename.source.name)}[/]"
        )


def apply_renames(renames: list[Rename]) -> int:
    failures = 0
    for rename in renames:
        try:
            if rename.target_path.exists():
                raise FileExistsError(f"{rename.target} already exists")
            rename.source.rename(rename.target_path)
        except OSError as error:
            console.print(
                f"  [{FAILURE}]x[/] {escape(rename.source.name)}: {escape(str(error))}"
            )
            failures += 1
        else:
            console.print(
                f"  [{SUCCESS}]+[/] {escape(rename.source.name)} [dim]->[/] {escape(rename.target)}"
            )
    return failures


def rename_all(directory: Path, renames: list[Rename], skipped: list[Path]) -> int:
    pending = [rename for rename in renames if not rename.settled]
    if not pending:
        console.print(
            f"[{SUCCESS}]nothing to rename[/], {plural(len(renames), 'file')} already named"
        )
        return 0

    show_preview(renames, skipped)

    collisions = find_collisions(renames)
    if collisions:
        show_collisions(collisions)
        return 1

    ordered, blocked = order_renames(
        pending, {path.name for path in directory.iterdir()}
    )
    if blocked:
        show_blocked(blocked)
        return 1

    if not confirm("proceed?"):
        print_cancelled()
        return 1

    failures = apply_renames(ordered)
    if failures:
        console.print(f"\n[{FAILURE}]done with {plural(failures, 'error')}[/]")
        return 1
    console.print(f"\n[{SUCCESS}]done - {plural(len(ordered), 'file')} renamed[/]")
    return 0
