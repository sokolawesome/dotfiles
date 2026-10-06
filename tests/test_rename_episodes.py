import io

import pytest
from conftest import load_module

rename_episodes = load_module("rename_episodes")


@pytest.mark.parametrize(
    ("digits", "width", "expected"),
    [
        ("5", 2, "05"),
        ("0", 2, "00"),
        ("007", 2, "07"),
        ("100", 2, "100"),
        ("345", 2, "345"),
    ],
)
def test_pad(digits, width, expected):
    assert rename_episodes.pad(digits, width) == expected


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("Show.S01E02.mkv", "Show.S01E02"),
        ("Show.S01.E02.mkv", "Show.S01.E02"),
        ("noextension", "noextension"),
    ],
)
def test_strip_extension(name, expected):
    assert rename_episodes.strip_extension(name) == expected


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("Show.S01E01.mkv", "Show S01E01"),
        ("Show Name S01E01", "Show Name S01E01"),
        ("Show_S01E01", "Show S01E01"),
        ("Show.S01E01", "Show"),
    ],
)
def test_normalize_name(name, expected):
    assert rename_episodes.normalize_name(name) == expected


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("Show 1080p WEB-DL", "Show"),
        ("Show [1080p] WEB-DL", "Show"),
        ("Show (x265 10bit)", "Show"),
        ("Show x265", "Show"),
        ("Show Bluray", "Show"),
        ("Show 1920x1080", "Show"),
        ("Show Name", "Show Name"),
    ],
)
def test_strip_quality_tags(name, expected):
    assert rename_episodes.strip_quality_tags(name) == expected


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("Show.S01.E02.mkv", ("01", "02")),
        ("Show.S01E02.mkv", ("01", "02")),
        ("Show.S01.E02.1080p.WEB-DL.x264.mkv", ("01", "02")),
        ("Show.1080p.S01E03.mkv", ("01", "03")),
        ("Show s02e08.mkv", ("02", "08")),
        ("Show.S01E100.mkv", ("01", "100")),
        ("Show.S12E345.mkv", ("12", "345")),
        ("Show.01x02.mkv", ("01", "02")),
        ("Show.1x2.mkv", ("01", "02")),
        ("Show - 05.mkv", ("00", "05")),
        ("Show - 105.mkv", ("00", "105")),
        ("[Group] Show - 05 [1080p].mkv", ("00", "05")),
        ("5 - Show.mkv", ("00", "05")),
        ("Season 2 - 03.mkv", ("00", "03")),
        ("Show [05].mkv", ("00", "05")),
        ("Show.05.mkv", ("00", "05")),
        ("Show.01.1080p.mkv", ("00", "01")),
        ("Show Name 07.mkv", ("00", "07")),
        ("Show.7.mkv", ("00", "07")),
    ],
)
def test_match_number(name, expected):
    assert rename_episodes.match_number(name) == expected


@pytest.mark.parametrize(
    "name",
    [
        "random.mkv",
        "Show.2024.1080p.mkv",
        "Show.Name.E07.mkv",
        "Show.E05.mkv",
        "Show.abc.mkv",
        "Show.S01E02",
    ],
)
def test_match_number_rejects(name):
    assert rename_episodes.match_number(name) is None


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("Show.S01E01.mkv", ".mkv"),
        ("Show.S01E01.mp4", ".mp4"),
        ("Show.S01E01.avi", ".avi"),
        ("Show.S01E01.mka", ".mka"),
        ("Show.S01E01.flac", ".flac"),
        ("Show.S01E01.ac3", ".ac3"),
        ("Show.S01E01.eac3", ".eac3"),
        ("Show.S01E01.aac", ".aac"),
        ("Show.S01E01.ass", ".ass"),
        ("Show.S01E01.srt", ".srt"),
        ("Show.S01E01.vtt", ".vtt"),
        ("Show.S01E01.sub", ".sub"),
        ("Show.S01E01.en.srt", ".en.srt"),
        ("Show.S01E01.eng.srt", ".eng.srt"),
        ("Show.S01E01.en.flac", ".en.flac"),
        ("Show.S01E01.eng.flac", ".eng.flac"),
        ("Show.S01E01.EN.srt", ".en.srt"),
        ("Show.Name.1080p.S01E01.srt", ".srt"),
        ("Episode.05.srt", ".srt"),
        ("Show.S01E01.srt.mkv", ".mkv"),
        ("S01E22.rus.anilibria.ass", ".rus.anilibria.ass"),
        ("S01E23.rus.anilibria.ass", ".rus.anilibria.ass"),
        ("S01E24.eng.subhd.ass", ".eng.subhd.ass"),
        ("S01E01.RUS.AniLibria.ass", ".rus.AniLibria.ass"),
        ("S01E01.rus.anilibria.srt", ".rus.anilibria.srt"),
        ("S01E01.rus.1080p.ass", ".rus.ass"),
        ("notes.txt", ""),
        ("Show.S01E01", ""),
    ],
)
def test_target_suffix(name, expected):
    assert rename_episodes.target_suffix(name) == expected


@pytest.mark.parametrize(
    ("directory_name", "expected"),
    [
        ("Season 1", "01"),
        ("Season 12", "12"),
        ("Season.03", "03"),
        ("Season_4", "04"),
        ("season-10", "10"),
        ("Show Name", None),
        ("Seasonning", None),
    ],
)
def test_detect_season(directory_name, expected):
    assert rename_episodes.detect_season(directory_name) == expected


def test_scan_media_files_only_depth_one(tmp_path):
    (tmp_path / "Show.S01E01.mkv").write_text("x")
    (tmp_path / "Show.S01E01.srt").write_text("x")
    (tmp_path / "notes.txt").write_text("x")
    (tmp_path / "poster.jpg").write_text("x")
    nested = tmp_path / "extras"
    nested.mkdir()
    (nested / "Show.S01E02.mkv").write_text("x")

    found = rename_episodes.scan_media_files(tmp_path)

    assert [p.name for p in found] == ["Show.S01E01.mkv", "Show.S01E01.srt"]


def make_episode(tmp_path, source, season, number, target):
    return rename_episodes.Episode(tmp_path / source, season, number, target)


def test_classify_applies_season_to_absolute_numbers(tmp_path):
    (tmp_path / "Show - 05.mkv").write_text("x")

    episodes, skipped = rename_episodes.classify([tmp_path / "Show - 05.mkv"], "02", 0)

    assert [e.target for e in episodes] == ["S02E05.mkv"]
    assert skipped == []


def test_classify_keeps_explicit_season(tmp_path):
    (tmp_path / "Show.S01E02.mkv").write_text("x")

    episodes, _ = rename_episodes.classify([tmp_path / "Show.S01E02.mkv"], "02", 0)

    assert [e.target for e in episodes] == ["S01E02.mkv"]


def test_classify_applies_positive_offset(tmp_path):
    (tmp_path / "Show - 01.mkv").write_text("x")

    episodes, _ = rename_episodes.classify([tmp_path / "Show - 01.mkv"], "01", 12)

    assert [e.target for e in episodes] == ["S01E13.mkv"]


def test_classify_absolute_subtracts_the_offset(tmp_path):
    (tmp_path / "Show - 101.mkv").write_text("x")
    (tmp_path / "Show - 112.mkv").write_text("x")
    paths = [tmp_path / "Show - 101.mkv", tmp_path / "Show - 112.mkv"]

    episodes, _ = rename_episodes.classify(paths, "01", -100)

    assert [e.target for e in episodes] == ["S01E01.mkv", "S01E12.mkv"]


def test_classify_absolute_keeps_explicit_season_numbers(tmp_path):
    (tmp_path / "Show.S02E101.mkv").write_text("x")

    episodes, _ = rename_episodes.classify([tmp_path / "Show.S02E101.mkv"], "01", -100)

    assert [e.target for e in episodes] == ["S02E01.mkv"]


def test_classify_skips_numbers_below_one(tmp_path):
    (tmp_path / "Show - 05.mkv").write_text("x")

    episodes, skipped = rename_episodes.classify([tmp_path / "Show - 05.mkv"], "01", -100)

    assert episodes == []
    assert [p.name for p in skipped] == ["Show - 05.mkv"]


def test_classify_never_writes_a_negative_episode(tmp_path):
    (tmp_path / "Show - 05.mkv").write_text("x")

    episodes, _ = rename_episodes.classify([tmp_path / "Show - 05.mkv"], "01", -6)

    assert episodes == []


def test_find_collisions_reports_both_sources(tmp_path):
    first = make_episode(tmp_path, "Show - 05.mkv", "01", "05", "S01E05.mkv")
    second = make_episode(tmp_path, "Show [05].mkv", "01", "05", "S01E05.mkv")

    assert rename_episodes.find_collisions([first, second]) == [
        ("S01E05.mkv", first.source, second.source)
    ]


def test_find_collisions_ignores_different_seasons(tmp_path):
    entries = [
        make_episode(tmp_path, "a.mkv", "01", "05", "S01E05.mkv"),
        make_episode(tmp_path, "b.mkv", "02", "05", "S02E05.mkv"),
    ]

    assert rename_episodes.find_collisions(entries) == []


def build_folder(tmp_path, name="Season 1"):
    folder = tmp_path / name
    folder.mkdir()
    return folder


def test_main_detects_season_from_the_folder(tmp_path, capsys):
    folder = build_folder(tmp_path)
    (folder / "Show - 05.mkv").write_text("x")

    code = rename_episodes.main(["--dry-run", "--directory", str(folder)])

    out = capsys.readouterr().out
    assert code == 0
    assert "detected season 01" in out
    assert "S01E05.mkv" in out


def test_main_season_flag_beats_detection(tmp_path, capsys):
    folder = build_folder(tmp_path)
    (folder / "Show - 05.mkv").write_text("x")

    code = rename_episodes.main(["--dry-run", "--season", "3", "--directory", str(folder)])

    out = capsys.readouterr().out
    assert code == 0
    assert "detected season" not in out
    assert "S03E05.mkv" in out


def test_main_errors_when_season_cannot_be_detected(tmp_path, capsys):
    folder = build_folder(tmp_path, "Show Name")
    (folder / "Show - 05.mkv").write_text("x")

    code = rename_episodes.main(["--dry-run", "--directory", str(folder)])

    err = capsys.readouterr().out
    assert code == 1
    assert "could not detect season" in err
    assert "use -s/--season" in err


def test_main_absolute_mode(tmp_path, capsys):
    folder = build_folder(tmp_path)
    for number in (101, 102, 103):
        (folder / f"Show - {number}.mkv").write_text("x")
    paths = sorted(folder.iterdir())

    episodes, _ = rename_episodes.classify(paths, "01", -100)

    assert [e.target for e in episodes] == ["S01E01.mkv", "S01E02.mkv", "S01E03.mkv"]


def test_main_dry_run_changes_nothing(tmp_path, capsys):
    folder = build_folder(tmp_path)
    (folder / "Show - 05.mkv").write_text("x")
    (folder / "Show.S01E02.mkv").write_text("x")
    (folder / "notes.txt").write_text("x")

    code = rename_episodes.main(["--dry-run", "--directory", str(folder)])

    out = capsys.readouterr().out
    assert code == 0
    assert "S01E05.mkv" in out
    assert "S01E02.mkv" in out
    assert sorted(p.name for p in folder.iterdir()) == [
        "Show - 05.mkv",
        "Show.S01E02.mkv",
        "notes.txt",
    ]


def test_main_aborts_on_collision(tmp_path, capsys):
    folder = build_folder(tmp_path)
    (folder / "Show - 05.mkv").write_text("x")
    (folder / "Show [05].mkv").write_text("x")

    code = rename_episodes.main(["--directory", str(folder)])

    err = capsys.readouterr().out
    assert code == 1
    assert "S01E05.mkv" in err
    assert sorted(p.name for p in folder.iterdir()) == ["Show - 05.mkv", "Show [05].mkv"]


def test_main_reports_empty_directory(tmp_path, capsys):
    folder = build_folder(tmp_path)

    code = rename_episodes.main(["--directory", str(folder)])

    assert code == 1
    assert "no media files" in capsys.readouterr().out


def test_apply_renames_moves_files_and_counts_failures(tmp_path, capsys):
    (tmp_path / "Show - 05.mkv").write_text("x")
    good = make_episode(tmp_path, "Show - 05.mkv", "01", "05", "S01E05.mkv")
    missing = make_episode(tmp_path, "gone.mkv", "01", "06", "S01E06.mkv")

    failures = rename_episodes.apply_renames([good, missing])

    assert failures == 1
    assert (tmp_path / "S01E05.mkv").exists()


def test_plural_switches_on_count():
    assert rename_episodes.plural(1, "file") == "1 file"
    assert rename_episodes.plural(0, "file") == "0 files"
    assert rename_episodes.plural(4, "file") == "4 files"


def test_settled_marks_already_named_episodes(tmp_path):
    settled = make_episode(tmp_path, "S01E01.mkv", "01", "1", "S01E01.mkv")
    moved = make_episode(tmp_path, "Show - 1.mkv", "01", "1", "S01E01.mkv")

    assert settled.settled
    assert not moved.settled


def test_main_exits_early_when_everything_is_named(tmp_path, capsys):
    folder = build_folder(tmp_path)
    (folder / "S01E01.mkv").write_text("x")
    (folder / "S01E02.mkv").write_text("x")

    code = rename_episodes.main(["--directory", str(folder)])

    out = capsys.readouterr().out
    assert code == 0
    assert "nothing to rename" in out
    assert "2 files already named" in out
    assert "proceed?" not in out
    assert sorted(p.name for p in folder.iterdir()) == ["S01E01.mkv", "S01E02.mkv"]


def test_main_early_exit_uses_singular_for_one_file(tmp_path, capsys):
    folder = build_folder(tmp_path)
    (folder / "S01E01.mkv").write_text("x")

    rename_episodes.main(["--directory", str(folder)])

    assert "1 file already named" in capsys.readouterr().out


def test_main_renames_only_the_pending_episodes(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("y\n"))
    folder = build_folder(tmp_path)
    (folder / "S01E01.mkv").write_text("x")
    (folder / "Show - 07.mkv").write_text("x")

    code = rename_episodes.main(["--directory", str(folder)])

    out = capsys.readouterr().out
    assert code == 0
    assert "done - 1 file renamed" in out
    assert sorted(p.name for p in folder.iterdir()) == ["S01E01.mkv", "S01E07.mkv"]


def test_main_dry_run_reports_nothing_to_rename(tmp_path, capsys):
    folder = build_folder(tmp_path)
    (folder / "S01E03.mkv").write_text("x")

    code = rename_episodes.main(["--dry-run", "--directory", str(folder)])

    out = capsys.readouterr().out
    assert code == 0
    assert "nothing to rename" in out


@pytest.mark.parametrize(
    ("stem", "expected"),
    [
        ("S01E22.rus.anilibria", ".rus.anilibria"),
        ("S01E22.rus", ".rus"),
        ("S01E22.mkv", ""),
        ("S01E22", ""),
        ("S01E22.rus.anilibria.forced", ".rus.anilibria.forced"),
        ("S01E22.1080p.rus", ".rus"),
        ("Show.Name.1080p.S01E01", ""),
        ("S01E22.netflix.eng", ".eng"),
        ("S01E22.netflix.rus.anilibria", ".rus.anilibria"),
        ("S01E22.rus.1080p", ".rus"),
        ("S01E01.RUS.AniLibria", ".rus.AniLibria"),
        ("S01E22.ru.anilibria", ".ru.anilibria"),
        ("S01E22.en.subhd", ".en.subhd"),
        ("S01E22.spa", ".spa"),
        ("S01E22.jpn", ".jpn"),
        ("S01E22.es", ".es"),
        ("S01E22.ja", ".ja"),
        ("S01E01.rus.720p.anilibria", ".rus"),
        ("S01E01.Netflix.rus.anilibria", ".rus.anilibria"),
        ("Show.S01E01.Netflix", ""),
    ],
)
def test_trailing_tags(stem, expected):
    assert rename_episodes.trailing_tags(stem) == expected


def test_subtitle_language_and_group_survive_rename(tmp_path):
    (tmp_path / "Show.S01E22.rus.anilibria.ass").write_text("x")
    (tmp_path / "Show.S01E22.mkv").write_text("x")

    episodes, _ = rename_episodes.classify(
        sorted(tmp_path.iterdir()), "01", 0
    )

    assert sorted(e.target for e in episodes) == [
        "S01E22.mkv",
        "S01E22.rus.anilibria.ass",
    ]


def test_language_after_group_drops_the_group(tmp_path):
    (tmp_path / "Show.S01E22.netflix.eng.ass").write_text("x")

    episodes, _ = rename_episodes.classify([tmp_path / "Show.S01E22.netflix.eng.ass"], "01", 0)

    assert episodes[0].target == "S01E22.eng.ass"


def test_subtitle_with_tags_is_settled(tmp_path):
    episode = rename_episodes.Episode(
        tmp_path / "S01E22.rus.anilibria.ass", "01", "22", "S01E22.rus.anilibria.ass"
    )

    assert episode.settled


def test_main_treats_missing_stdin_as_cancelled(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO(""))
    folder = build_folder(tmp_path)
    (folder / "Show - 05.mkv").write_text("x")

    code = rename_episodes.main(["--directory", str(folder)])

    out = capsys.readouterr().out
    assert code == 130
    assert "cancelled" in out
    assert sorted(p.name for p in folder.iterdir()) == ["Show - 05.mkv"]
