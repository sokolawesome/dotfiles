"""Preview, check and apply a batch of file renames inside one directory."""

from dataclasses import dataclass
from pathlib import Path

from rich.markup import escape
from rich.table import Table

from _common import (
    console,
    plain_table,
    plural,
    print_cancelled,
    print_error,
    show_panel,
)
from _prompts import Option, choose_many, confirm, interactive


@dataclass(frozen=True)
class Rename:
    source: Path
    target: str
    destination: Path | None = None

    @property
    def settled(self) -> bool:
        return self.target_path == self.source

    @property
    def target_path(self) -> Path:
        return (self.destination or self.source.parent) / self.target

    @property
    def moved(self) -> bool:
        return self.target_path.parent != self.source.parent

    @property
    def label(self) -> str:
        return str(self.source.relative_to(self.target_path.parent, walk_up=True))

    def left_alone(self) -> "Rename":
        return Rename(self.source, self.source.name)


def pad(digits: str | int, width: int) -> str:
    return f"{int(digits):0{width}d}"


def find_collisions(renames: list[Rename]) -> list[tuple[Rename, Rename]]:
    claimed: dict[Path, Rename] = {}
    collisions = []
    for rename in renames:
        previous = claimed.setdefault(rename.target_path, rename)
        if previous is not rename:
            collisions.append((previous, rename))
    return collisions


def order_renames(
    pending: list[Rename], existing: set[Path]
) -> tuple[list[Rename], list[Rename]]:
    occupied = set(existing)
    waiting = list(pending)
    ordered: list[Rename] = []
    while waiting:
        ready = [rename for rename in waiting if rename.target_path not in occupied]
        if not ready:
            break
        for rename in ready:
            occupied.discard(rename.source)
            occupied.add(rename.target_path)
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
            table.add_row(escape(rename.label), "·", "[dim]unchanged[/]")
        else:
            table.add_row(
                escape(rename.label),
                "→",
                f"[success]{escape(rename.target)}[/]",
            )
    return table


def build_skipped(skipped: list[Path]) -> Table:
    table = plain_table()
    table.add_column(overflow="ellipsis")
    for path in skipped:
        table.add_row(f"[warning]{escape(path.name)}[/]")
    return table


def show_skipped(skipped: list[Path]) -> None:
    if skipped:
        show_panel(build_skipped(skipped), "skipped", "warning")


def show_preview(renames: list[Rename], skipped: list[Path]) -> None:
    show_panel(build_preview(renames), "preview")
    show_skipped(skipped)
    settled = sum(1 for rename in renames if rename.settled)
    summary = f"{len(renames)} files"
    if settled:
        summary += f", {settled} already named"
    if skipped:
        summary += f", {len(skipped)} skipped"
    console.print(f"[question]{summary}[/]\n")


def show_collisions(collisions: list[tuple[Rename, Rename]]) -> None:
    print_error("two files resolve to the same name")
    for first, second in collisions:
        console.print(
            f"  [failure]{escape(first.target)}[/] from [dim]{escape(first.label)}[/] and [dim]{escape(second.label)}[/]"
        )


def show_blocked(blocked: list[Rename]) -> None:
    print_error("these names are taken by files that would not move")
    for rename in blocked:
        console.print(
            f"  [failure]{escape(rename.target)}[/] wanted by [dim]{escape(rename.label)}[/]"
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
                f"  [failure]x[/] {escape(rename.label)}: {escape(str(error))}"
            )
            failures += 1
        else:
            console.print(
                f"  [success]+[/] {escape(rename.label)} [dim]->[/] {escape(rename.target)}"
            )
    return failures


def remove_emptied_folders(renames: list[Rename]) -> None:
    for rename in renames:
        if not rename.moved:
            continue
        destination = rename.target_path.parent
        folder = rename.source.parent
        while folder != destination and folder.is_relative_to(destination):
            try:
                folder.rmdir()
            except OSError:
                break
            console.print(f"  [dim]- removed empty {escape(folder.name)}/[/]")
            folder = folder.parent


def pick_renames(renames: list[Rename], skipped: list[Path]) -> list[Rename]:
    pending = [rename for rename in renames if not rename.settled]
    show_skipped(skipped)
    options = [Option(rename, (rename.label, "→", rename.target)) for rename in pending]
    chosen = choose_many(
        f"rename {plural(len(pending), 'file')}", options, pending, required=True
    )
    return [
        rename if rename.settled or rename in chosen else rename.left_alone()
        for rename in renames
    ]


def rename_all(directory: Path, renames: list[Rename], skipped: list[Path]) -> int:
    pending = [rename for rename in renames if not rename.settled]
    if not pending:
        console.print(
            f"[success]nothing to rename[/], {plural(len(renames), 'file')} already named"
        )
        return 0

    if interactive():
        renames = pick_renames(renames, skipped)
        pending = [rename for rename in renames if not rename.settled]
    else:
        show_preview(renames, skipped)

    collisions = find_collisions(renames)
    if collisions:
        show_collisions(collisions)
        return 1

    ordered, blocked = order_renames(pending, set(directory.iterdir()))
    if blocked:
        show_blocked(blocked)
        return 1

    if not confirm(f"rename {plural(len(ordered), 'file')}?"):
        print_cancelled()
        return 1

    failures = apply_renames(ordered)
    remove_emptied_folders(ordered)
    if failures:
        console.print(f"\n[failure]done with {plural(failures, 'error')}[/]")
        return 1
    console.print(f"\n[success]done - {plural(len(ordered), 'file')} renamed[/]")
    return 0
