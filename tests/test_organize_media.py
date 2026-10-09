import io

import pytest
from conftest import load_module

organize_media = load_module("organize_media")

SHREK = "Shrek (2001) [tvdbid-12345]"
BLUE_BOX = "Blue Box (2024) [tvdbid-429934]"


def answer(monkeypatch, *lines):
    monkeypatch.setattr("sys.stdin", io.StringIO("".join(f"{line}\n" for line in lines)))


def tree(root):
    return sorted(str(path.relative_to(root)) for path in root.rglob("*"))


@pytest.mark.parametrize(
    ("spec", "expected"),
    [
        ("5", ["05"]),
        ("0", ["00"]),
        ("007", ["07"]),
        ("12", ["12"]),
        ("0-2", ["00", "01", "02"]),
        ("10-10", ["10"]),
        ("9-11", ["09", "10", "11"]),
    ],
)
def test_season_range(spec, expected):
    assert organize_media.parse_season_range(spec) == expected


@pytest.mark.parametrize("spec", ["", "abc", "1-", "-1", "3-1", "1-2-3", "1.5"])
def test_season_range_rejects(spec):
    with pytest.raises(organize_media.OrganizeMediaError):
        organize_media.parse_season_range(spec)


def test_cli_creates_a_movie(tmp_path, monkeypatch):
    answer(monkeypatch, "y")

    code = organize_media.main(["-t", "movie", "-n", "Shrek", "-y", "2001", "-i", "12345", str(tmp_path)])

    assert code == 0
    assert tree(tmp_path) == [SHREK]


def test_cli_creates_a_show_with_an_id_per_season(tmp_path, monkeypatch):
    answer(monkeypatch, "y")

    code = organize_media.main(
        ["-t", "show", "-n", "Blue Box", "-y", "2024", "-i", "429934,430001,430002", "-s", "1-2", str(tmp_path)]
    )

    assert code == 0
    assert tree(tmp_path) == [
        BLUE_BOX,
        f"{BLUE_BOX}/Season 01 [tvdbid-430001]",
        f"{BLUE_BOX}/Season 02 [tvdbid-430002]",
    ]


def test_cli_creates_season_zero_for_specials(tmp_path, monkeypatch):
    answer(monkeypatch, "y")

    organize_media.main(["-t", "show", "-n", "Blue Box", "-y", "2024", "-i", "429934,430000", "-s", "0", str(tmp_path)])

    assert f"{BLUE_BOX}/Season 00 [tvdbid-430000]" in tree(tmp_path)


@pytest.mark.parametrize(
    ("ids", "seasons", "message"),
    [
        ("429934", "1-2", "0 season ids given but 2 seasons requested"),
        ("429934,430001", "1-2", "1 season ids given but 2 seasons requested"),
        ("429934,430001,430002,430003", "1-2", "3 season ids given but 2 seasons requested"),
        ("", "1", "tvdb id is empty"),
    ],
)
def test_cli_needs_exactly_one_id_per_season(tmp_path, capsys, ids, seasons, message):
    code = organize_media.main(["-t", "show", "-n", "Blue Box", "-y", "2024", "-i", ids, "-s", seasons, str(tmp_path)])

    assert code == 1
    assert message in capsys.readouterr().out
    assert tree(tmp_path) == []


@pytest.mark.parametrize(
    ("arguments", "message"),
    [
        (["-t", "movie", "-n", "Shrek", "-y", "2001", "-i", "1,2"], "a movie takes one tvdb id"),
        (["-t", "show", "-n", "Blue Box", "-y", "2024", "-i", "1"], "seasons are required"),
        (["-t", "show", "-n", "Blue Box", "-y", "2024", "-i", "1,2", "-s", "3-1"], "start must be <= end"),
        (["-n", "Shrek", "-y", "2001", "-i", "1"], "type must be one of"),
        (["-t", "movie", "-y", "2001", "-i", "1"], "name is required"),
        (["-t", "movie", "-n", "Shrek", "-i", "1"], "year is required"),
    ],
)
def test_cli_rejects_incomplete_input(tmp_path, capsys, arguments, message):
    code = organize_media.main([*arguments, str(tmp_path)])

    assert code == 1
    assert message in capsys.readouterr().out
    assert tree(tmp_path) == []


def test_declining_creates_nothing(tmp_path, monkeypatch, capsys):
    answer(monkeypatch, "n")

    code = organize_media.main(["-t", "movie", "-n", "Shrek", "-y", "2001", "-i", "12345", str(tmp_path)])

    assert code == 1
    assert "cancelled" in capsys.readouterr().out
    assert tree(tmp_path) == []


def test_existing_directories_are_kept(tmp_path, monkeypatch, capsys):
    (tmp_path / SHREK).mkdir()
    (tmp_path / SHREK / "Shrek.mkv").write_text("movie")
    answer(monkeypatch, "y")

    code = organize_media.main(["-t", "movie", "-n", "Shrek", "-y", "2001", "-i", "12345", str(tmp_path)])

    assert code == 0
    assert "exists" in capsys.readouterr().out
    assert (tmp_path / SHREK / "Shrek.mkv").read_text() == "movie"


def test_missing_root_is_reported(tmp_path, capsys):
    code = organize_media.main(["-t", "movie", "-n", "Shrek", "-y", "2001", "-i", "1", str(tmp_path / "nope")])

    assert code == 1
    assert "is not a directory" in capsys.readouterr().out


def test_errors_show_bracketed_paths_without_backslashes(tmp_path, capsys):
    show = tmp_path / BLUE_BOX
    show.mkdir()

    organize_media.main(["--add-season", "-n", "Nothing", "-s", "1", "-i", "1", str(show)])

    out = capsys.readouterr().out.replace("\n", "")
    assert "[tvdbid-429934]" in out
    assert "\\[" not in out


def test_add_season_inside_a_show(tmp_path, monkeypatch):
    show = tmp_path / BLUE_BOX
    show.mkdir()
    answer(monkeypatch, "y")

    code = organize_media.main(["--add-season", "-s", "3-4", "-i", "430003,430004", str(show)])

    assert code == 0
    assert tree(tmp_path) == [
        BLUE_BOX,
        f"{BLUE_BOX}/Season 03 [tvdbid-430003]",
        f"{BLUE_BOX}/Season 04 [tvdbid-430004]",
    ]


def test_add_season_finds_the_only_show_in_a_library(tmp_path, monkeypatch):
    (tmp_path / BLUE_BOX).mkdir()
    (tmp_path / "notes").mkdir()
    answer(monkeypatch, "y")

    code = organize_media.main(["--add-season", "-s", "3", "-i", "430003", str(tmp_path)])

    assert code == 0
    assert (tmp_path / BLUE_BOX / "Season 03 [tvdbid-430003]").is_dir()


@pytest.mark.parametrize("name", ["blue box", "box"])
def test_add_season_picks_a_show_by_name(tmp_path, monkeypatch, name):
    (tmp_path / BLUE_BOX).mkdir()
    (tmp_path / "Show Two (2019) [tvdbid-777]").mkdir()
    answer(monkeypatch, "y")

    code = organize_media.main(["--add-season", "-n", name, "-s", "3", "-i", "430003", str(tmp_path)])

    assert code == 0
    assert (tmp_path / BLUE_BOX / "Season 03 [tvdbid-430003]").is_dir()


def test_add_season_prefers_an_exact_name(tmp_path, monkeypatch):
    (tmp_path / "Blue (2020) [tvdbid-1]").mkdir()
    (tmp_path / BLUE_BOX).mkdir()
    answer(monkeypatch, "y")

    organize_media.main(["--add-season", "-n", "blue", "-s", "1", "-i", "2", str(tmp_path)])

    assert (tmp_path / "Blue (2020) [tvdbid-1]" / "Season 01 [tvdbid-2]").is_dir()


@pytest.mark.parametrize(
    ("arguments", "message"),
    [
        (["-n", "show"], "matches 2 shows"),
        ([], "2 shows in"),
        (["-n", "nothing"], "no show directory called 'nothing'"),
    ],
)
def test_add_season_refuses_to_guess(tmp_path, capsys, arguments, message):
    (tmp_path / "Show One (2020) [tvdbid-1]").mkdir()
    (tmp_path / "Show Two (2019) [tvdbid-2]").mkdir()

    code = organize_media.main(["--add-season", *arguments, "-s", "1", "-i", "5", str(tmp_path)])

    assert code == 1
    assert message in capsys.readouterr().out
    assert tree(tmp_path) == ["Show One (2020) [tvdbid-1]", "Show Two (2019) [tvdbid-2]"]


@pytest.mark.parametrize(
    ("arguments", "message"),
    [
        (["-s", "1-2", "-i", "430001"], "every season needs its own tvdb id"),
        (["-s", "1"], "--add-season needs -s/--seasons and -i/--id"),
        (["-i", "1"], "--add-season needs -s/--seasons and -i/--id"),
    ],
)
def test_add_season_needs_seasons_and_their_ids(tmp_path, capsys, arguments, message):
    show = tmp_path / BLUE_BOX
    show.mkdir()

    code = organize_media.main(["--add-season", *arguments, str(show)])

    assert code == 1
    assert message in capsys.readouterr().out
    assert tree(tmp_path) == [BLUE_BOX]


def test_guided_movie(tmp_path, monkeypatch):
    answer(monkeypatch, "1", "Shrek", "2001", "12345", "y")

    code = organize_media.main([str(tmp_path)])

    assert code == 0
    assert tree(tmp_path) == [SHREK]


def test_guided_mode_defaults_to_a_movie(tmp_path, monkeypatch):
    answer(monkeypatch, "", "Shrek", "2001", "12345", "y")

    organize_media.main([str(tmp_path)])

    assert tree(tmp_path) == [SHREK]


def test_guided_show_asks_an_id_for_each_season(tmp_path, monkeypatch):
    answer(monkeypatch, "show", "Blue Box", "2024", "429934", "1-2", "430001", "430002", "y")

    code = organize_media.main([str(tmp_path)])

    assert code == 0
    assert tree(tmp_path) == [
        BLUE_BOX,
        f"{BLUE_BOX}/Season 01 [tvdbid-430001]",
        f"{BLUE_BOX}/Season 02 [tvdbid-430002]",
    ]


def test_guided_mode_asks_again_for_an_empty_answer(tmp_path, monkeypatch, capsys):
    answer(monkeypatch, "2", "", "Blue Box", "2024", "429934", "1", "", "430001", "y")

    code = organize_media.main([str(tmp_path)])

    assert code == 0
    assert capsys.readouterr().out.count("an answer is required") == 2
    assert (tmp_path / BLUE_BOX / "Season 01 [tvdbid-430001]").is_dir()


def test_guided_mode_asks_again_for_an_unknown_type(tmp_path, monkeypatch, capsys):
    answer(monkeypatch, "film", "m", "Shrek", "2001", "12345", "y")

    code = organize_media.main([str(tmp_path)])

    assert code == 0
    assert "pick movie, show or add season" in capsys.readouterr().out
    assert tree(tmp_path) == [SHREK]


def test_guided_mode_declined_creates_nothing(tmp_path, monkeypatch):
    answer(monkeypatch, "1", "Shrek", "2001", "12345", "n")

    code = organize_media.main([str(tmp_path)])

    assert code == 1
    assert tree(tmp_path) == []


def test_guided_add_season_inside_a_show(tmp_path, monkeypatch, capsys):
    show = tmp_path / BLUE_BOX
    show.mkdir()
    answer(monkeypatch, "3", "3", "430003", "y")

    code = organize_media.main([str(show)])

    assert code == 0
    assert "inside" in capsys.readouterr().out
    assert (show / "Season 03 [tvdbid-430003]").is_dir()


@pytest.mark.parametrize("choice", ["2", "two"])
def test_guided_add_season_picks_a_show_by_number_or_name(tmp_path, monkeypatch, choice):
    (tmp_path / BLUE_BOX).mkdir()
    (tmp_path / "Show Two (2019) [tvdbid-777]").mkdir()
    answer(monkeypatch, "3", choice, "1", "778001", "y")

    code = organize_media.main([str(tmp_path)])

    assert code == 0
    assert (tmp_path / "Show Two (2019) [tvdbid-777]" / "Season 01 [tvdbid-778001]").is_dir()


def test_guided_add_season_asks_again_for_a_bad_pick(tmp_path, monkeypatch, capsys):
    for index in range(12):
        (tmp_path / f"Show {index:02d} (2024) [tvdbid-{index}]").mkdir()
    answer(monkeypatch, "3", "11", "show", "nothing", "Show 11", "1", "500", "y")

    code = organize_media.main([str(tmp_path)])

    out = capsys.readouterr().out
    assert code == 0
    assert "and 2 more" in out
    assert "pick a number between 1 and 10" in out
    assert "matches 12 shows" in out
    assert "no show by that name" in out
    assert (tmp_path / "Show 11 (2024) [tvdbid-11]" / "Season 01 [tvdbid-500]").is_dir()
