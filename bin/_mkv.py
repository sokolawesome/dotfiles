"""Probe MKV files, pick their audio and subtitle tracks by language, run mkvtoolnix."""

import json
import re
import shutil
import subprocess
from collections import Counter
from collections.abc import Callable, Iterable
from dataclasses import dataclass, replace
from pathlib import Path

from rich.markup import escape
from rich.progress import BarColumn, Progress, TextColumn, TimeElapsedColumn
from rich.table import Table

from _common import console, plain_table, plural, show_panel
from _prompts import Option, choose_many

MKV_SUFFIX = ".mkv"
PROGRESS_LINE = re.compile(r"Progress:\s*(\d+)%")
AUDIO = "audio"
SUBTITLES = "subtitles"
SELECTABLE_TYPES = (AUDIO, SUBTITLES)
TOOL_FAILED = 2
MEBIBYTE = 1024**2
GIBIBYTE = 1024**3
SUPPORTED_SUBTITLE_LANGUAGES = (
    "en",
    "eng",
    "ja",
    "jpn",
    "ru",
    "rus",
    "es",
    "spa",
)


class MkvError(Exception):
    pass


@dataclass(frozen=True)
class Track:
    kind: str
    track_id: int
    language: str
    alias: str
    name: str
    codec: str

    @property
    def label(self) -> str:
        return self.name or "unnamed"

    def speaks(self, wanted: str) -> bool:
        return wanted in (self.language, self.alias)


@dataclass(frozen=True)
class FileScan:
    path: Path
    tracks: tuple[Track, ...]
    error: str = ""

    @property
    def readable(self) -> bool:
        return not self.error


@dataclass(frozen=True)
class Selection:
    kind: str
    language: str
    names: frozenset[str] | None = None


def find_tool(name: str) -> str:
    found = shutil.which(name)
    if found is None:
        raise MkvError(
            f"{name} not found, install with 'sudo pacman -S mkvtoolnix-cli'"
        )
    return found


def language_of(properties: dict) -> tuple[str, str]:
    ietf = (properties.get("language_ietf") or "").strip()
    full = (properties.get("language") or "").strip()
    if not ietf and not full:
        return ("und", "und")
    if not full:
        full = ietf
    if not ietf:
        ietf = full
    return (full.lower(), ietf.lower())


def parse_tracks(payload: str) -> tuple[Track, ...]:
    document = json.loads(payload)
    errors = document.get("errors") or []
    if errors:
        raise ValueError(errors[0].strip())
    if not document.get("container", {}).get("recognized"):
        raise ValueError("not a recognized media file")
    tracks = []
    for entry in document.get("tracks", []):
        properties = entry.get("properties", {})
        language, alias = language_of(properties)
        tracks.append(
            Track(
                kind=entry.get("type", ""),
                track_id=int(entry.get("id", -1)),
                language=language,
                alias=alias,
                name=(properties.get("track_name") or "").replace("|", "/"),
                codec=properties.get("codec_id", ""),
            )
        )
    return tuple(tracks)


def probe(path: Path, mkvmerge: str) -> FileScan:
    finished = subprocess.run(
        [mkvmerge, "-J", str(path)], capture_output=True, text=True, check=False
    )
    try:
        return FileScan(path, parse_tracks(finished.stdout))
    except (json.JSONDecodeError, TypeError, ValueError) as error:
        return FileScan(
            path, (), str(error) or f"mkvmerge exited {finished.returncode}"
        )


def probe_all(paths: list[Path], mkvmerge: str) -> list[FileScan]:
    scans = []
    with console.status("probing") as status:
        for index, path in enumerate(paths, start=1):
            status.update(f"probing {index}/{len(paths)} [dim]{escape(path.name)}[/]")
            scans.append(probe(path, mkvmerge))
    return scans


def scan_files(directory: Path) -> list[Path]:
    if not directory.is_dir():
        raise MkvError(f"not a directory: {directory}")
    return [
        p
        for p in sorted(directory.iterdir())
        if p.is_file() and p.suffix.lower() == MKV_SUFFIX
    ]


def supported_subtitle(track: Track) -> bool:
    return (
        track.language in SUPPORTED_SUBTITLE_LANGUAGES
        or track.alias in SUPPORTED_SUBTITLE_LANGUAGES
    )


def selectable(track: Track) -> bool:
    if track.kind == AUDIO:
        return True
    return track.kind == SUBTITLES and supported_subtitle(track)


def union_of(scans: list[FileScan]) -> list[Selection]:
    keys: dict[tuple[str, str], None] = {}
    for scan in scans:
        for track in scan.tracks:
            if selectable(track):
                keys.setdefault((track.kind, track.language), None)
    return [Selection(*key) for key in keys]


def matches_for(selection: Selection, scan: FileScan) -> list[Track]:
    return [
        track
        for track in scan.tracks
        if track.kind == selection.kind and track.speaks(selection.language)
    ]


def picked_for(selection: Selection, scan: FileScan) -> list[Track]:
    return [
        track
        for track in matches_for(selection, scan)
        if selection.names is None or track.name in selection.names
    ]


def presence_of(selection: Selection, scans: list[FileScan]) -> int:
    return sum(1 for scan in scans if matches_for(selection, scan))


def files_per_name(selection: Selection, scans: list[FileScan]) -> Counter[str]:
    return Counter(
        name
        for scan in scans
        for name in dict.fromkeys(track.name for track in matches_for(selection, scan))
    )


def labels_for(selection: Selection, scans: list[FileScan]) -> list[str]:
    return [name or "unnamed" for name in files_per_name(selection, scans)]


def narrowed_by_name(
    title: str, selection: Selection, scans: list[FileScan]
) -> Selection:
    counts = files_per_name(selection, scans)
    if len(counts) < 2:
        return selection
    options = [
        Option(name, (name or "unnamed",), plural(count, "file"))
        for name, count in counts.items()
    ]
    names = choose_many(
        f"{title}: {selection.kind} {selection.language}",
        options,
        required=True,
    )
    return replace(selection, names=frozenset(names))


def choose_interactively(
    title: str, scans: list[FileScan], union: list[Selection]
) -> list[Selection]:
    options = [
        Option(
            selection,
            (
                selection.kind,
                selection.language,
                ", ".join(labels_for(selection, scans)) or "unnamed",
            ),
            plural(presence_of(selection, scans), "file"),
        )
        for selection in union
    ]
    return [
        narrowed_by_name(title, selection, scans)
        for selection in choose_many(title, options)
    ]


def resolve_picks(
    selections: list[Selection],
    scan: FileScan,
    ask: bool,
) -> list[Track]:
    chosen = []
    for selection in selections:
        if matches_for(selection, scan):
            chosen.extend(picked_for(selection, scan))
        elif ask:
            chosen.extend(pick_from_available(selection, scan))
    unique = []
    seen = set()
    for track in chosen:
        if track.track_id not in seen:
            seen.add(track.track_id)
            unique.append(track)
    return unique


def pick_from_available(selection: Selection, scan: FileScan) -> list[Track]:
    available = [track for track in scan.tracks if track.kind == selection.kind]
    if not available:
        return []
    options = [
        Option(track, (track.language, track.label), track.codec) for track in available
    ]
    return choose_many(
        f"{scan.path.name}: no {selection.language} {selection.kind}, pick a replacement",
        options,
        border="failure",
    )


def line_buffered(command: list[str]) -> list[str]:
    if shutil.which("stdbuf"):
        return ["stdbuf", "-oL", *command]
    return command


def read_progress(stream: Iterable[str], report: Callable[[int], object]) -> list[str]:
    messages = []
    for line in stream:
        for chunk in line.replace("\r", "\n").split("\n"):
            match = PROGRESS_LINE.search(chunk)
            if match:
                report(int(match.group(1)))
            elif chunk.strip():
                messages.append(chunk.strip())
    return messages


def failure_reason(messages: list[str], code: int, program: str) -> str:
    errors = [message for message in messages if message.startswith("Error")]
    if errors:
        return errors[0]
    if messages:
        return messages[-1]
    return f"{program} exited {code}"


def run_with_progress(
    command: list[str], report: Callable[[int], object] | None = None
) -> str:
    process = subprocess.Popen(
        line_buffered(command),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    with process:
        try:
            messages = read_progress(
                process.stdout or [], report or (lambda percent: None)
            )
            code = process.wait()
        except BaseException:
            process.kill()
            process.wait()
            raise
    if code >= TOOL_FAILED:
        return failure_reason(messages, code, Path(command[0]).name)
    return ""


def progress_bars() -> Progress:
    return Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(complete_style="success", style="dim", finished_style="success"),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
        transient=True,
    )


def size_of(path: Path) -> int:
    try:
        return path.stat().st_size
    except OSError:
        return 0


def format_size(value: int) -> str:
    if value < 0:
        return f"-{format_size(-value)}"
    if value >= GIBIBYTE:
        return f"{value / GIBIBYTE:.2f} GiB"
    if value >= MEBIBYTE:
        return f"{value / MEBIBYTE:.2f} MiB"
    return f"{value} B"


def describe_missing(selections: Iterable[Selection]) -> str:
    return ", ".join(f"{s.kind[:3]} {s.language}" for s in selections)


def build_problem_table(scans: list[FileScan]) -> Table:
    table = plain_table()
    table.add_column(overflow="ellipsis")
    table.add_column(overflow="fold")
    for scan in scans:
        if scan.error:
            table.add_row(escape(scan.path.name), f"[failure]{escape(scan.error)}[/]")
    return table


def report_unreadable(scans: list[FileScan]) -> None:
    if any(not scan.readable for scan in scans):
        show_panel(build_problem_table(scans), "unreadable", "failure")
