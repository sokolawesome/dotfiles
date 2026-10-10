import io

import pytest

from conftest import load_module

rename_episodes = load_module("rename_episodes")


def answer(monkeypatch, line):
    monkeypatch.setattr("sys.stdin", io.StringIO(f"{line}\n"))


def season_folder(tmp_path, *names, folder="Season 1"):
    directory = tmp_path / folder
    directory.mkdir()
    for name in names:
        (directory / name).write_text(name)
    return directory


def files(directory):
    return {
        path.name: path.read_text() for path in directory.iterdir() if path.is_file()
    }


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("Show.S01.E02.mkv", ("01", "02")),
        ("Show.S01E02.mkv", ("01", "02")),
        ("Show.S01.E02.1080p.WEB-DL.x264.mkv", ("01", "02")),
        ("Show.1080p.S01E03.mkv", ("01", "03")),
        ("Show s02e08.mkv", ("02", "08")),
        ("Show S00E05.mkv", ("00", "05")),
        ("Show.S01E100.mkv", ("01", "100")),
        ("Show.01x02.mkv", ("01", "02")),
        ("Show.1x2.mkv", ("01", "02")),
        ("Show - 05.mkv", (None, "05")),
        ("Show - 105.mkv", (None, "105")),
        ("[Group] Show - 05 [1080p].mkv", (None, "05")),
        ("5 - Show.mkv", (None, "05")),
        ("Show [05].mkv", (None, "05")),
        ("Show.05.mkv", (None, "05")),
        ("Show.01.1080p.mkv", (None, "01")),
        ("Show_Name_07.mkv", (None, "07")),
        ("Show Name 07.mkv", (None, "07")),
        ("Show (x265 10bit) - 03.mkv", (None, "03")),
    ],
)
def test_episode_number(name, expected):
    assert rename_episodes.match_number(name) == expected


@pytest.mark.parametrize(
    "name",
    [
        "random.mkv",
        "Show.2024.1080p.mkv",
        "Show.Name.E07.mkv",
        "Show.abc.mkv",
        "Show 1920x1080.mkv",
    ],
)
def test_no_episode_number(name):
    assert rename_episodes.match_number(name) is None


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("Show.S01E01.mkv", ".mkv"),
        ("Show.S01E01.MKV", ".mkv"),
        ("Show.S01E01.mp4", ".mp4"),
        ("Show.S01E01.mka", ".mka"),
        ("Show.S01E01.srt", ".srt"),
        ("Show.S01E01.en.srt", ".en.srt"),
        ("Show.S01E01.EN.srt", ".en.srt"),
        ("Show.S01E01.eng.flac", ".eng.flac"),
        ("Show.Name.1080p.S01E01.srt", ".srt"),
        ("Show.S01E01.srt.mkv", ".mkv"),
        ("S01E22.rus.anilibria.ass", ".rus.anilibria.ass"),
        ("S01E22.rus.anilibria.forced.ass", ".rus.anilibria.forced.ass"),
        ("S01E01.RUS.AniLibria.ass", ".rus.AniLibria.ass"),
        ("S01E22.ru.anilibria.ass", ".ru.anilibria.ass"),
        ("S01E22.jpn.ass", ".jpn.ass"),
        ("S01E22.1080p.rus.ass", ".rus.ass"),
        ("S01E01.rus.1080p.ass", ".rus.ass"),
        ("S01E01.rus.720p.anilibria.ass", ".rus.ass"),
        ("S01E22.netflix.eng.ass", ".eng.ass"),
        ("S01E01.Netflix.rus.anilibria.ass", ".rus.anilibria.ass"),
        ("Show.S01E01.Netflix.ass", ".ass"),
        ("notes.txt", ""),
        ("Show.S01E01", ""),
    ],
)
def test_kept_suffix(name, expected):
    assert rename_episodes.target_suffix(name) == expected


@pytest.mark.parametrize(
    ("folder", "expected"),
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
def test_season_from_the_folder_name(folder, expected):
    assert rename_episodes.detect_season(folder) == expected


def test_renames_using_the_season_from_the_folder(tmp_path, monkeypatch, capsys):
    folder = season_folder(
        tmp_path, "Show - 05.mkv", "Show - 05.rus.anilibria.ass", folder="Season 2"
    )
    answer(monkeypatch, "y")

    code = rename_episodes.main([str(folder)])

    assert code == 0
    assert "detected season 02" in capsys.readouterr().out
    assert files(folder) == {
        "S02E05.mkv": "Show - 05.mkv",
        "S02E05.rus.anilibria.ass": "Show - 05.rus.anilibria.ass",
    }


def test_season_flag_beats_the_folder_name(tmp_path, monkeypatch, capsys):
    folder = season_folder(tmp_path, "Show - 05.mkv")
    answer(monkeypatch, "y")

    rename_episodes.main(["--season", "3", str(folder)])

    assert "detected season" not in capsys.readouterr().out
    assert list(files(folder)) == ["S03E05.mkv"]


def test_season_zero_from_the_flag(tmp_path, monkeypatch):
    folder = season_folder(tmp_path, "Show - 05.mkv", folder="Specials")
    answer(monkeypatch, "y")

    rename_episodes.main(["-s", "0", str(folder)])

    assert list(files(folder)) == ["S00E05.mkv"]


def test_a_special_tagged_in_the_name_stays_in_season_zero(tmp_path, monkeypatch):
    folder = season_folder(tmp_path, "Show S00E05.mkv")
    answer(monkeypatch, "y")

    rename_episodes.main([str(folder)])

    assert list(files(folder)) == ["S00E05.mkv"]


def test_a_season_in_the_file_name_beats_the_folder(tmp_path, monkeypatch):
    folder = season_folder(tmp_path, "Show.S02E07.mkv")
    answer(monkeypatch, "y")

    rename_episodes.main([str(folder)])

    assert list(files(folder)) == ["S02E07.mkv"]


def test_no_season_anywhere_is_an_error(tmp_path, capsys):
    folder = season_folder(tmp_path, "Show - 05.mkv", folder="Show Name")

    code = rename_episodes.main([str(folder)])

    out = capsys.readouterr().out
    assert code == 1
    assert "could not detect season" in out
    assert "use -s/--season" in out
    assert list(files(folder)) == ["Show - 05.mkv"]


def test_negative_offset_turns_absolute_numbers_into_season_numbers(
    tmp_path, monkeypatch
):
    folder = season_folder(
        tmp_path, "Show - 101.mkv", "Show - 102.mkv", "Show - 112.mkv"
    )
    answer(monkeypatch, "y")

    code = rename_episodes.main(["--offset", "-100", str(folder)])

    assert code == 0
    assert files(folder) == {
        "S01E01.mkv": "Show - 101.mkv",
        "S01E02.mkv": "Show - 102.mkv",
        "S01E12.mkv": "Show - 112.mkv",
    }


@pytest.mark.parametrize("offset", [1, -1])
def test_offset_on_named_files_moves_every_episode_without_overwriting(
    tmp_path, monkeypatch, offset
):
    folder = season_folder(tmp_path, "S01E02.mkv", "S01E03.mkv", "S01E04.mkv")
    answer(monkeypatch, "y")

    code = rename_episodes.main(["-o", str(offset), str(folder)])

    assert code == 0
    assert files(folder) == {
        f"S01E0{n + offset}.mkv": f"S01E0{n}.mkv" for n in (2, 3, 4)
    }


def test_files_below_episode_one_after_the_offset_are_skipped(tmp_path, monkeypatch):
    folder = season_folder(tmp_path, "Show - 05.mkv", "Show - 107.mkv")
    answer(monkeypatch, "y")

    rename_episodes.main(["-o", "-100", str(folder)])

    assert sorted(files(folder)) == ["S01E07.mkv", "Show - 05.mkv"]


def test_unrecognised_files_are_listed_and_left_alone(tmp_path, monkeypatch, capsys):
    folder = season_folder(
        tmp_path, "Show - 05.mkv", "trailer.mkv", "notes.txt", "poster.jpg"
    )
    answer(monkeypatch, "y")

    rename_episodes.main([str(folder)])

    assert "trailer.mkv" in capsys.readouterr().out
    assert sorted(files(folder)) == [
        "S01E05.mkv",
        "notes.txt",
        "poster.jpg",
        "trailer.mkv",
    ]


def test_files_in_subfolders_are_ignored(tmp_path, monkeypatch):
    folder = season_folder(tmp_path, "Show - 05.mkv")
    (folder / "extras").mkdir()
    (folder / "extras" / "Show - 06.mkv").write_text("extra")
    answer(monkeypatch, "y")

    rename_episodes.main([str(folder)])

    assert list(files(folder)) == ["S01E05.mkv"]
    assert (folder / "extras" / "Show - 06.mkv").exists()


@pytest.mark.parametrize(
    ("names", "message"),
    [
        ((), "no media files found"),
        (("notes.txt",), "no media files found"),
        (("trailer.mkv",), "could not extract episode numbers"),
    ],
)
def test_nothing_to_work_with_is_an_error(tmp_path, capsys, names, message):
    folder = season_folder(tmp_path, *names)

    code = rename_episodes.main([str(folder)])

    assert code == 1
    assert message in capsys.readouterr().out


def test_a_missing_directory_is_an_error(tmp_path, capsys):
    code = rename_episodes.main([str(tmp_path / "nope")])

    assert code == 1
    assert "is not a directory" in capsys.readouterr().out
