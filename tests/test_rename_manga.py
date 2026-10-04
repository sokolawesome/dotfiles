import pytest
from conftest import load_module

rename_manga = load_module("rename_manga")


@pytest.mark.parametrize(
    ("digits", "width", "expected"),
    [
        ("7", 2, "07"),
        ("0", 2, "00"),
        ("007", 2, "07"),
        ("12", 2, "12"),
        ("7", 3, "007"),
        ("0", 3, "000"),
        ("045", 3, "045"),
        ("999", 3, "999"),
        ("12345", 2, "12345"),
    ],
)
def test_pad(digits, width, expected):
    assert rename_manga.pad(digits, width) == expected


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("v01.cbz", "v01"),
        ("vol.1-2.cbz", "vol.1-2"),
        ("Vol 3 Extra.cbz", "Vol 3 Extra"),
        ("noextension", "noextension"),
        ("archive.tar.gz", "archive.tar"),
    ],
)
def test_strip_archive_suffix(name, expected):
    assert rename_manga.strip_archive_suffix(name) == expected


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("v01.cbz", ".cbz"),
        ("v01.cbr", ".cbr"),
        ("v01.CBZ", None),
        ("v01.zip", None),
        ("v01", None),
    ],
)
def test_archive_suffix(name, expected):
    assert rename_manga.archive_suffix(name) == expected


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("v9.cbz", ("v", "09")),
        ("vol.09.cbz", ("v", "09")),
        ("volume 9.cbz", ("v", "09")),
        ("Vol 12.cbz", ("v", "12")),
        ("VOLUME 3.cbz", ("v", "03")),
        ("v01.cbz", ("v", "01")),
        ("v 5.cbz", ("v", "05")),
        ("v007.cbz", ("v", "07")),
        ("v0.cbz", ("v", "00")),
        ("c3.cbz", ("c", "003")),
        ("ch.03.cbz", ("c", "003")),
        ("chapter 3.cbz", ("c", "003")),
        ("Ch 45.cbz", ("c", "045")),
        ("CHAPTER 7.cbz", ("c", "007")),
        ("c001.cbz", ("c", "001")),
        ("ch12.cbz", ("c", "012")),
        ("c0.cbz", ("c", "000")),
        ("c999.cbz", ("c", "999")),
        ("003.cbz", ("c", "003")),
        ("45.cbz", ("c", "045")),
        ("108.cbz", ("c", "108")),
        ("Ch.1080p.cbz", ("c", "1080")),
        ("vol.1-2.cbz", ("v", "01")),
        ("Vol 3 Extra.cbz", ("v", "03")),
        ("[v01].cbz", ("v", "01")),
        ("v01.cbr", ("v", "01")),
    ],
)
def test_parse_kind_and_number(name, expected):
    assert rename_manga.parse_kind_and_number(name) == expected


@pytest.mark.parametrize(
    "name",
    [
        "1000.cbz",
        "extra.cbz",
        "One Piece.cbz",
        "Series Title 2024.cbz",
        "One Piece 1050.cbz",
        "x264 2020.cbz",
        "cover.jpg",
    ],
)
def test_parse_kind_and_number_rejects(name):
    assert rename_manga.parse_kind_and_number(name) is None


def test_parse_kind_and_number_prefers_volume_over_chapter():
    assert rename_manga.parse_kind_and_number("Vol 3 Chapter 12.cbz") == ("v", "03")


def test_parse_kind_and_number_single_digit_bare_number():
    assert rename_manga.parse_kind_and_number("7.cbz") == ("c", "007")


@pytest.mark.parametrize(
    ("kind", "number", "suffix", "expected"),
    [
        ("v", "09", ".cbz", "09.cbz"),
        ("v", "09", ".cbr", "09.cbr"),
        ("c", "003", ".cbz", "c003.cbz"),
        ("c", "003", ".srt", "c003.srt"),
    ],
)
def test_target_name(kind, number, suffix, expected):
    assert rename_manga.target_name(kind, number, suffix) == expected


def test_scan_manga_files_only_depth_one(tmp_path):
    (tmp_path / "v01.cbz").write_text("x")
    (tmp_path / "notes.txt").write_text("x")
    (tmp_path / "v02.cbr").write_text("x")
    nested = tmp_path / "nested"
    nested.mkdir()
    (nested / "v03.cbz").write_text("x")

    found = rename_manga.scan_manga_files(tmp_path)

    assert [p.name for p in found] == ["v01.cbz", "v02.cbr"]


def test_classify_splits_matched_and_skipped(tmp_path):
    (tmp_path / "v01.cbz").write_text("x")
    (tmp_path / "extra.cbz").write_text("x")

    entries, skipped = rename_manga.classify(rename_manga.scan_manga_files(tmp_path))

    assert [(e.source.name, e.target) for e in entries] == [("v01.cbz", "01.cbz")]
    assert [p.name for p in skipped] == ["extra.cbz"]


def test_find_collisions_reports_both_sources(tmp_path):
    first = rename_manga.MangaFile(tmp_path / "v01.cbz", "v", "01", "01.cbz")
    second = rename_manga.MangaFile(tmp_path / "vol.1.cbz", "v", "01", "01.cbz")
    third = rename_manga.MangaFile(tmp_path / "c01.cbz", "c", "001", "c001.cbz")

    collisions = rename_manga.find_collisions([first, second, third])

    assert collisions == [("01.cbz", first.source, second.source)]


def test_find_collisions_ignores_three_digit_ranges(tmp_path):
    entries = [
        rename_manga.MangaFile(tmp_path / "c1.cbz", "c", "001", "c001.cbz"),
        rename_manga.MangaFile(tmp_path / "c2.cbz", "c", "002", "c002.cbz"),
    ]

    assert rename_manga.find_collisions(entries) == []


def test_main_dry_run_changes_nothing(tmp_path, capsys):
    (tmp_path / "v01.cbz").write_text("x")
    (tmp_path / "chapter 2.cbz").write_text("x")
    (tmp_path / "extra.cbz").write_text("x")

    code = rename_manga.main(["--dry-run", "--directory", str(tmp_path)])

    out = capsys.readouterr().out
    assert code == 0
    assert "v01.cbz" in out and "01.cbz" in out
    assert "c002.cbz" in out
    assert "extra.cbz" in out
    assert sorted(p.name for p in tmp_path.iterdir()) == [
        "chapter 2.cbz",
        "extra.cbz",
        "v01.cbz",
    ]


def test_main_aborts_on_collision_before_renaming(tmp_path, capsys):
    (tmp_path / "v01.cbz").write_text("x")
    (tmp_path / "vol.1.cbz").write_text("x")

    code = rename_manga.main(["--directory", str(tmp_path)])

    err = capsys.readouterr().out
    assert code == 1
    assert "01.cbz" in err
    assert sorted(p.name for p in tmp_path.iterdir()) == ["v01.cbz", "vol.1.cbz"]


def test_main_reports_empty_directory(tmp_path, capsys):
    code = rename_manga.main(["--directory", str(tmp_path)])

    assert code == 1
    assert "no manga files" in capsys.readouterr().out


def test_main_reports_when_nothing_parses(tmp_path, capsys):
    (tmp_path / "extra.cbz").write_text("x")

    code = rename_manga.main(["--directory", str(tmp_path)])

    assert code == 1
    assert "could not extract" in capsys.readouterr().out


def test_main_rejects_missing_directory(tmp_path, capsys):
    code = rename_manga.main(["--directory", str(tmp_path / "nope")])

    assert code == 1
    assert "not a directory" in capsys.readouterr().out


def test_apply_renames_moves_files_and_counts_failures(tmp_path, capsys):
    (tmp_path / "v01.cbz").write_text("x")
    good = rename_manga.MangaFile(tmp_path / "v01.cbz", "v", "01", "01.cbz")
    missing = rename_manga.MangaFile(tmp_path / "gone.cbz", "v", "02", "02.cbz")

    failures = rename_manga.apply_renames([good, missing])

    assert failures == 1
    assert (tmp_path / "01.cbz").exists()
    assert not (tmp_path / "v01.cbz").exists()


def test_write_undo_log_records_both_names(tmp_path):
    entry = rename_manga.MangaFile(tmp_path / "v01.cbz", "v", "01", "01.cbz")
    log = tmp_path / ".rename_manga.log"

    rename_manga.write_undo_log([entry], log)
    rename_manga.write_undo_log([entry], log)

    lines = log.read_text().splitlines()
    assert lines.count("v01.cbz\t01.cbz") == 2
    assert lines[0].startswith("# ")
    assert lines[2].startswith("# ")