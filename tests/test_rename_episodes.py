import pytest

from conftest import answer, load_module

rename_episodes = load_module("rename_episodes")


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
        ("S01E01.rus.Dream Cast.mka", ".rus.Dream Cast.mka"),
        ("S01E01.rus.AniLibria-TV.mka", ".rus.AniLibria-TV.mka"),
        ("S01E01.rus.Кубик в Кубе.mka", ".rus.Кубик в Кубе.mka"),
        ("S01E01.rus.x264.mka", ".rus.mka"),
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
        ("S01", "01"),
        ("Show S2", "02"),
        ("Show.s03.1080p.WEB", "03"),
        ("Show_S04_Complete", "04"),
        ("Show.S05E01-E10", "05"),
        ("Shows 6", None),
        ("Mars7", None),
        ("S123", None),
        ("Show Name", None),
        ("Seasonning", None),
    ],
)
def test_season_from_the_folder_name(folder, expected):
    assert rename_episodes.detect_season(folder) == expected


@pytest.mark.parametrize(
    ("folders", "language", "name"),
    [
        (("RUS Sound", "AniLibria"), "rus", "AniLibria"),
        (("Rus Subs [Crunchyroll]",), "rus", "Crunchyroll"),
        (("ENG Subs", "Full"), "eng", "Full"),
        (("Субтитры", "Русские"), "rus", ""),
        (("Озвучка", "AniDUB"), "", "AniDUB"),
        (("Dream Cast",), "", "Dream Cast"),
        (("Subs",), "", ""),
        ((), "", ""),
    ],
)
def test_language_and_name_are_guessed_from_the_folders(folders, language, name):
    assert rename_episodes.guess_language(folders) == language
    assert rename_episodes.guess_name(folders) == name


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


def test_files_with_their_own_seasons_need_no_season_in_the_folder(
    tmp_path, monkeypatch, capsys
):
    folder = season_folder(
        tmp_path,
        "Show.S01E09.Pilot.Part.Two.1080p.mkv",
        "Show.S02E01.Some.Title.WEB-DL.mkv",
        "Show.s03.e04.mkv",
        folder="Show Name",
    )
    answer(monkeypatch, "y")

    code = rename_episodes.main([str(folder)])

    assert code == 0
    assert sorted(files(folder)) == ["S01E09.mkv", "S02E01.mkv", "S03E04.mkv"]
    assert "detected season" not in capsys.readouterr().out


def test_one_file_without_a_season_still_needs_the_folder_season(tmp_path, capsys):
    folder = season_folder(
        tmp_path, "Show.S01E01.mkv", "Show - 02.mkv", folder="Show Name"
    )

    code = rename_episodes.main([str(folder)])

    assert code == 1
    assert "could not detect season" in capsys.readouterr().out


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


def test_tracks_in_subfolders_move_next_to_the_episodes(tmp_path, monkeypatch):
    folder = season_folder(tmp_path, "Show - 05.mkv")
    dubs = folder / "RUS Sound" / "AniLibria"
    subs = folder / "RUS Subs"
    dubs.mkdir(parents=True)
    subs.mkdir()
    (dubs / "Show - 05.mka").write_text("dub")
    (subs / "Show - 05.ass").write_text("sub")
    answer(monkeypatch, "", "", "", "Crunchyroll", "y")

    code = rename_episodes.main([str(folder)])

    assert code == 0
    assert files(folder) == {
        "S01E05.mkv": "Show - 05.mkv",
        "S01E05.rus.AniLibria.mka": "dub",
        "S01E05.rus.Crunchyroll.ass": "sub",
    }
    assert [path.name for path in folder.iterdir() if path.is_dir()] == []


def test_untagged_tracks_next_to_the_episodes_ask_for_tags(tmp_path, monkeypatch):
    folder = season_folder(tmp_path, "Show - 05.mkv", "Show - 05.mka")
    answer(monkeypatch, "RUS", "Dream Cast", "y")

    rename_episodes.main([str(folder)])

    assert sorted(files(folder)) == ["S01E05.mkv", "S01E05.rus.Dream Cast.mka"]


def test_dubs_and_subs_in_one_folder_get_their_own_tags(tmp_path, monkeypatch, capsys):
    folder = season_folder(tmp_path, "Show - 05.mkv", "Show - 05.mka", "Show - 05.srt")
    answer(monkeypatch, "rus", "AniLibria", "eng", "Crunchyroll", "y")

    code = rename_episodes.main([str(folder)])

    out = capsys.readouterr().out
    assert code == 0
    assert "language for audio in Season 1" in out
    assert "language for subtitles in Season 1" in out
    assert sorted(files(folder)) == [
        "S01E05.eng.Crunchyroll.srt",
        "S01E05.mkv",
        "S01E05.rus.AniLibria.mka",
    ]


def test_a_track_name_can_be_left_out(tmp_path, monkeypatch):
    folder = season_folder(tmp_path, "Show - 05.mkv", "Show - 05.srt")
    answer(monkeypatch, "eng", "", "y")

    rename_episodes.main([str(folder)])

    assert sorted(files(folder)) == ["S01E05.eng.srt", "S01E05.mkv"]


def test_an_unknown_language_or_bad_name_is_asked_again(tmp_path, monkeypatch, capsys):
    folder = season_folder(tmp_path, "Show - 05.mka")
    answer(monkeypatch, "xx", "rus", "2x2", "AniLibria", "y")

    rename_episodes.main([str(folder)])

    out = capsys.readouterr().out
    assert "use one of" in out
    assert "use letters" in out
    assert list(files(folder)) == ["S01E05.rus.AniLibria.mka"]


def test_tagged_tracks_in_subfolders_move_without_questions(tmp_path, monkeypatch):
    folder = season_folder(tmp_path, "Show - 05.mkv")
    (folder / "Subs").mkdir()
    (folder / "Subs" / "Show - 05.rus.anilibria.ass").write_text("sub")
    answer(monkeypatch, "y")

    code = rename_episodes.main([str(folder)])

    assert code == 0
    assert sorted(files(folder)) == ["S01E05.mkv", "S01E05.rus.anilibria.ass"]


def test_tracks_in_hidden_folders_are_ignored(tmp_path, monkeypatch):
    folder = season_folder(tmp_path, "Show - 05.mkv")
    (folder / ".Show - 05.extracting").mkdir()
    (folder / ".Show - 05.extracting" / "Show - 05.mka").write_text("partial")
    answer(monkeypatch, "y")

    rename_episodes.main([str(folder)])

    assert list(files(folder)) == ["S01E05.mkv"]
    assert (folder / ".Show - 05.extracting" / "Show - 05.mka").exists()
