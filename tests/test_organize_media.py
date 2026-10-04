import types

import pytest
from conftest import load_module

organize_media = load_module("organize_media")


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (0, "00"),
        (1, "01"),
        (5, "05"),
        (7, "07"),
        (12, "12"),
        (99, "99"),
        (100, "100"),
    ],
)
def test_pad_season(value, expected):
    assert organize_media.pad_season(value) == expected


@pytest.mark.parametrize(
    ("spec", "expected"),
    [
        ("5", ["05"]),
        ("1", ["01"]),
        ("0", ["00"]),
        ("12", ["12"]),
        ("007", ["07"]),
        ("0-3", ["00", "01", "02", "03"]),
        ("0-2", ["00", "01", "02"]),
        ("0-0", ["00"]),
        ("10-10", ["10"]),
        ("2-10", ["02", "03", "04", "05", "06", "07", "08", "09", "10"]),
    ],
)
def test_parse_season_range(spec, expected):
    assert organize_media.parse_season_range(spec) == expected


@pytest.mark.parametrize("spec", ["", "abc", "1-", "-1", "3-1", "1-2-3", "1.5", "a-b"])
def test_parse_season_range_rejects(spec):
    with pytest.raises(organize_media.OrganizeMediaError):
        organize_media.parse_season_range(spec)


@pytest.mark.parametrize(
    ("id_string", "content_type", "seasons", "expected"),
    [
        ("12345", "movie", [], ("12345", [])),
        ("111", "show", ["01"], ("111", [])),
        ("111", "show", ["01", "02"], ("111", [])),
        ("111,222", "show", ["01"], ("111", ["222"])),
    ],
)
def test_parse_tvdb_ids(id_string, content_type, seasons, expected):
    assert organize_media.parse_tvdb_ids(id_string, content_type, seasons) == expected


@pytest.mark.parametrize(
    ("id_string", "content_type", "seasons"),
    [
        ("", "movie", []),
        ("", "show", ["01"]),
        ("12345,67890", "movie", []),
        ("111,222", "show", ["01", "02"]),
        ("111,222,333", "show", ["01", "02", "03"]),
        ("111,222,333", "show", ["01"]),
    ],
)
def test_parse_tvdb_ids_rejects(id_string, content_type, seasons):
    with pytest.raises(organize_media.OrganizeMediaError):
        organize_media.parse_tvdb_ids(id_string, content_type, seasons)


def test_parse_tvdb_ids_reports_both_counts():
    with pytest.raises(organize_media.OrganizeMediaError) as error:
        organize_media.parse_tvdb_ids("111,222,333", "show", ["01"])

    assert "2 season ids" in str(error.value)
    assert "1 seasons" in str(error.value)


@pytest.mark.parametrize(
    ("index", "season_ids", "expected"),
    [
        (0, ["222"], "222"),
        (0, ["222", "333"], "222"),
        (1, ["222", "333"], "333"),
        (2, ["222", "333"], "111"),
        (0, [], "111"),
        (1, [], "111"),
    ],
)
def test_season_id_for(index, season_ids, expected):
    assert organize_media.season_id_for(index, season_ids, "111") == expected


def test_main_directory_for(tmp_path):
    result = organize_media.main_directory_for(tmp_path, "Shrek", "2001", "12345")

    assert result == tmp_path / "Shrek (2001) [tvdbid-12345]"


def test_season_directory_for(tmp_path):
    result = organize_media.season_directory_for(tmp_path / "Show (2020) [tvdbid-1]", "02", "222")

    assert result == tmp_path / "Show (2020) [tvdbid-1]" / "Season 02 [tvdbid-222]"


def test_build_show_plan_for_a_movie(tmp_path):
    plan = organize_media.build_show_plan(tmp_path, "movie", "Shrek", "2001", "12345", "")

    assert plan.main_directory == tmp_path / "Shrek (2001) [tvdbid-12345]"
    assert plan.seasons == ()
    assert plan.directories() == [tmp_path / "Shrek (2001) [tvdbid-12345]"]


def test_build_show_plan_for_a_show(tmp_path):
    plan = organize_media.build_show_plan(
        tmp_path, "show", "Blue Box", "2024", "429934,430001,430002", "1-2"
    )

    assert plan.show_id == "429934"
    assert [s.number for s in plan.seasons] == ["01", "02"]
    assert [s.directory.name for s in plan.seasons] == [
        "Season 01 [tvdbid-430001]",
        "Season 02 [tvdbid-430002]",
    ]


def test_build_show_plan_falls_back_to_the_show_id_for_seasons(tmp_path):
    plan = organize_media.build_show_plan(tmp_path, "show", "Blue Box", "2024", "429934", "1-3")

    assert [s.directory.name for s in plan.seasons] == [
        "Season 01 [tvdbid-429934]",
        "Season 02 [tvdbid-429934]",
        "Season 03 [tvdbid-429934]",
    ]


def test_build_show_plan_needs_seasons_for_a_show(tmp_path):
    with pytest.raises(organize_media.OrganizeMediaError) as error:
        organize_media.build_show_plan(tmp_path, "show", "Blue Box", "2024", "429934", "")

    assert "seasons are required" in str(error.value)


@pytest.mark.parametrize(
    ("content_type", "title", "year"),
    [
        ("film", "Shrek", "2001"),
        ("movie", "", "2001"),
        ("movie", "Shrek", ""),
    ],
)
def test_build_show_plan_rejects_missing_values(tmp_path, content_type, title, year):
    with pytest.raises(organize_media.OrganizeMediaError):
        organize_media.build_show_plan(tmp_path, content_type, title, year, "12345", "")


def test_find_show_directory(tmp_path):
    (tmp_path / "Blue Box (2024) [tvdbid-429934]").mkdir()

    found, year, show_id = organize_media.find_show_directory(tmp_path, "Blue Box")

    assert found == tmp_path / "Blue Box (2024) [tvdbid-429934]"
    assert year == "2024"
    assert show_id == "429934"


def test_find_show_directory_ignores_season_folders(tmp_path):
    (tmp_path / "Blue Box (2024) [tvdbid-429934]" / "Season 01 [tvdbid-1]").mkdir(parents=True)

    found, _, _ = organize_media.find_show_directory(tmp_path, "Blue Box")

    assert found.name == "Blue Box (2024) [tvdbid-429934]"


def test_find_show_directory_reports_a_missing_show(tmp_path):
    with pytest.raises(organize_media.OrganizeMediaError) as error:
        organize_media.find_show_directory(tmp_path, "Nothing")

    assert "no existing folder for 'Nothing'" in str(error.value)


def test_build_add_season_plan_uses_the_existing_show_id(tmp_path):
    (tmp_path / "Blue Box (2024) [tvdbid-429934]").mkdir()

    plan = organize_media.build_add_season_plan(tmp_path, "Blue Box", "3", "")

    assert plan.main_directory == tmp_path / "Blue Box (2024) [tvdbid-429934]"
    assert plan.seasons[0].directory.name == "Season 03 [tvdbid-429934]"


def test_build_add_season_plan_accepts_a_season_id(tmp_path):
    (tmp_path / "Blue Box (2024) [tvdbid-429934]").mkdir()

    plan = organize_media.build_add_season_plan(tmp_path, "Blue Box", "3", "430003")

    assert plan.seasons[0].directory.name == "Season 03 [tvdbid-430003]"


def test_create_directories_makes_the_tree(tmp_path, capsys):
    plan = organize_media.build_show_plan(tmp_path, "show", "Blue Box", "2024", "429934", "1-2")

    organize_media.create_directories(plan, dry_run=False)

    main_dir = tmp_path / "Blue Box (2024) [tvdbid-429934]"
    assert main_dir.is_dir()
    assert (main_dir / "Season 01 [tvdbid-429934]").is_dir()
    assert (main_dir / "Season 02 [tvdbid-429934]").is_dir()


def test_create_directories_dry_run_creates_nothing(tmp_path, capsys):
    plan = organize_media.build_show_plan(
        tmp_path, "show", "Blue Box", "2024", "429934", "1-2"
    )

    organize_media.create_directories(plan, dry_run=True)

    out = capsys.readouterr().out
    assert "would create" in out
    assert list(tmp_path.iterdir()) == []


def test_create_directories_is_repeatable(tmp_path, capsys):
    plan = organize_media.build_show_plan(tmp_path, "movie", "Shrek", "2001", "12345", "")

    organize_media.create_directories(plan, dry_run=False)
    organize_media.create_directories(plan, dry_run=False)

    assert "exists" in capsys.readouterr().out


def test_main_creates_a_movie(tmp_path, monkeypatch):
    monkeypatch.setattr(organize_media, "asks_yes", lambda question: True)
    code = organize_media.main(
        ["-t", "movie", "-n", "Shrek", "-y", "2001", "-i", "12345", "--root", str(tmp_path)]
    )

    assert code == 0
    assert (tmp_path / "Shrek (2001) [tvdbid-12345]").is_dir()


def test_main_creates_a_show_with_seasons(tmp_path, monkeypatch):
    monkeypatch.setattr(organize_media, "asks_yes", lambda question: True)
    code = organize_media.main(
        [
            "-t", "show", "-n", "Blue Box", "-y", "2024",
            "-i", "429934,430001,430002", "-s", "1-2",
            "--root", str(tmp_path),
        ]
    )

    assert code == 0
    main_dir = tmp_path / "Blue Box (2024) [tvdbid-429934]"
    assert (main_dir / "Season 01 [tvdbid-430001]").is_dir()
    assert (main_dir / "Season 02 [tvdbid-430002]").is_dir()


def test_main_leaves_nothing_behind_when_seasons_are_missing(tmp_path, capsys):
    code = organize_media.main(
        ["-t", "show", "-n", "Blue Box", "-y", "2024", "-i", "429934", "--root", str(tmp_path)]
    )

    assert code == 1
    assert "seasons are required" in capsys.readouterr().out
    assert list(tmp_path.iterdir()) == []


def test_main_reports_a_bad_id_count(tmp_path, capsys):
    code = organize_media.main(
        [
            "-t", "show", "-n", "Blue Box", "-y", "2024",
            "-i", "429934,430001", "-s", "1-3",
            "--root", str(tmp_path),
        ]
    )

    assert code == 1
    assert "season ids" in capsys.readouterr().out
    assert list(tmp_path.iterdir()) == []


def test_main_reports_a_bad_season_range(tmp_path, capsys):
    code = organize_media.main(
        ["-t", "show", "-n", "Blue Box", "-y", "2024", "-i", "1", "-s", "3-1", "--root", str(tmp_path)]
    )

    assert code == 1
    assert "start must be <= end" in capsys.readouterr().out
    assert list(tmp_path.iterdir()) == []


def test_main_dry_run_creates_nothing(tmp_path, monkeypatch):
    def refuse(question):
        raise AssertionError("dry run must not ask for confirmation")

    monkeypatch.setattr(organize_media, "asks_yes", refuse)
    code = organize_media.main(
        ["-t", "movie", "-n", "Shrek", "-y", "2001", "-i", "12345", "-d", "--root", str(tmp_path)]
    )

    assert code == 0
    assert list(tmp_path.iterdir()) == []


def test_main_add_season(tmp_path, monkeypatch):
    monkeypatch.setattr(organize_media, "asks_yes", lambda question: True)
    (tmp_path / "Blue Box (2024) [tvdbid-429934]").mkdir()

    code = organize_media.main(
        ["--add-season", "Blue Box", "3", "--season-id", "430003", "--root", str(tmp_path)]
    )

    assert code == 0
    assert (tmp_path / "Blue Box (2024) [tvdbid-429934]" / "Season 03 [tvdbid-430003]").is_dir()


def test_main_add_season_reports_a_missing_show(tmp_path, capsys):
    code = organize_media.main(["--add-season", "Nothing", "1", "--root", str(tmp_path)])

    assert code == 1
    assert "no existing folder" in capsys.readouterr().out


def test_main_rejects_a_missing_root(tmp_path, capsys):
    code = organize_media.main(
        ["-t", "movie", "-n", "Shrek", "-y", "2001", "-i", "1", "--root", str(tmp_path / "nope")]
    )

    assert code == 1
    assert "not a directory" in capsys.readouterr().out


def answers(monkeypatch, values, confirmations=()):
    replies = iter(values)
    monkeypatch.setattr(organize_media, "ask", lambda prompt, default="": next(replies) or default)
    if confirmations:
        decide = iter(confirmations)
        monkeypatch.setattr(organize_media, "asks_yes", lambda question: next(decide))


def test_guided_mode_asks_each_value(tmp_path, monkeypatch):
    answers(monkeypatch, ["movie", "Shrek", "2001", "12345"], [True])

    code = organize_media.main(["--root", str(tmp_path)])

    assert code == 0
    assert (tmp_path / "Shrek (2001) [tvdbid-12345]").is_dir()


def test_guided_mode_walks_the_seasons(tmp_path, monkeypatch):
    answers(monkeypatch, ["show", "Blue Box", "2024", "429934", "1-2", "430001", "430002", "n"], [True])

    code = organize_media.main(["--root", str(tmp_path)])

    main_dir = tmp_path / "Blue Box (2024) [tvdbid-429934]"
    assert code == 0
    assert (main_dir / "Season 01 [tvdbid-430001]").is_dir()
    assert (main_dir / "Season 02 [tvdbid-430002]").is_dir()


def test_guided_mode_defaults_a_season_id_to_the_show_id(tmp_path, monkeypatch):
    answers(monkeypatch, ["show", "Blue Box", "2024", "429934", "1-2", "", "", "n"], [True])

    code = organize_media.main(["--root", str(tmp_path)])

    main_dir = tmp_path / "Blue Box (2024) [tvdbid-429934]"
    assert code == 0
    assert (main_dir / "Season 01 [tvdbid-429934]").is_dir()
    assert (main_dir / "Season 02 [tvdbid-429934]").is_dir()


def test_output_keeps_the_tvdb_tags(tmp_path, monkeypatch, capsys):
    answers(monkeypatch, ["show", "space-bunny", "1998", "135234", "1-2", "5453", "45233", "n"], [True])

    organize_media.main(["--root", str(tmp_path)])

    out = capsys.readouterr().out
    assert "space-bunny (1998) [tvdbid-135234]" in out
    assert "Season 01 [tvdbid-5453]" in out
    assert "Season 02 [tvdbid-45233]" in out


def test_guided_mode_season_prompt_has_no_default(tmp_path, monkeypatch):
    shown = []

    def record(prompt, default=""):
        shown.append((prompt, default))
        if prompt.startswith("type"):
            return "2"
        if prompt.startswith("seasons"):
            return "1-2"
        return "x"

    monkeypatch.setattr(organize_media, "ask", record)
    monkeypatch.setattr(organize_media, "asks_yes", lambda question: False)

    organize_media.main(["--root", str(tmp_path)])

    season_prompts = [(p, d) for p, d in shown if p.startswith("tvdb id for season")]
    assert season_prompts == [("tvdb id for season 01", ""), ("tvdb id for season 02", "")]


def test_season_ids_fall_back_to_the_series_id_when_none_are_given(tmp_path, monkeypatch):
    monkeypatch.setattr(organize_media, "asks_yes", lambda question: True)

    code = organize_media.main(
        ["-t", "show", "-n", "foo", "-y", "2020", "-i", "33", "-s", "1-2", "--root", str(tmp_path)]
    )

    main_dir = tmp_path / "foo (2020) [tvdbid-33]"
    assert code == 0
    assert (main_dir / "Season 01 [tvdbid-33]").is_dir()
    assert (main_dir / "Season 02 [tvdbid-33]").is_dir()


def test_ask_rejects_an_empty_answer(monkeypatch, capsys):
    replies = iter(["", "   ", "Shrek"])

    monkeypatch.setattr(organize_media, "Prompt", types.SimpleNamespace(ask=lambda *a, **k: next(replies)))

    assert organize_media.ask("title") == "Shrek"
    assert capsys.readouterr().out.count("an answer is required") == 2


def test_ask_uses_a_default_when_given(monkeypatch):
    replies = iter([""])
    asked = []

    def fake_ask(prompt, **kwargs):
        asked.append(kwargs)
        return next(replies)

    monkeypatch.setattr(organize_media, "Prompt", types.SimpleNamespace(ask=fake_ask))

    organize_media.ask("add another season?", "n")

    assert asked == [{"default": "n", "console": organize_media.console}]


def test_guided_mode_adds_seasons_one_at_a_time(tmp_path, monkeypatch):
    answers(
        monkeypatch,
        ["show", "Blue Box", "2024", "429934", "1", "430001", "y", "2", "430002", "n"],
        [True, True],
    )

    code = organize_media.main(["--root", str(tmp_path)])

    main_dir = tmp_path / "Blue Box (2024) [tvdbid-429934]"
    assert code == 0
    assert (main_dir / "Season 01 [tvdbid-430001]").is_dir()
    assert (main_dir / "Season 02 [tvdbid-430002]").is_dir()


def test_guided_mode_stops_when_declined(tmp_path, monkeypatch):
    answers(monkeypatch, ["movie", "Shrek", "2001", "12345"], [False])

    code = organize_media.main(["--root", str(tmp_path)])

    assert code == 1
    assert list(tmp_path.iterdir()) == []


def test_guided_mode_asks_again_for_a_bad_type(tmp_path, monkeypatch, capsys):
    answers(monkeypatch, ["film", "1", "Shrek", "2001", "12345"], [True])

    code = organize_media.main(["--root", str(tmp_path)])

    assert code == 0
    assert "pick movie or show" in capsys.readouterr().out
    assert (tmp_path / "Shrek (2001) [tvdbid-12345]").is_dir()


def test_guided_mode_defaults_the_type_to_movie(tmp_path, monkeypatch):
    answers(monkeypatch, ["", "Shrek", "2001", "12345"], [True])

    code = organize_media.main(["--root", str(tmp_path)])

    assert code == 0
    assert (tmp_path / "Shrek (2001) [tvdbid-12345]").is_dir()