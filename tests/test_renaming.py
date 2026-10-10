import io

import pytest

import _renaming
from _renaming import Rename


def answer(monkeypatch, line):
    monkeypatch.setattr("sys.stdin", io.StringIO(f"{line}\n"))


def files(directory):
    return {path.name: path.read_text() for path in directory.iterdir()}


def make(directory, **contents):
    for name, content in contents.items():
        (directory / name).write_text(content)


def renames(directory, *pairs):
    return [Rename(directory / source, target) for source, target in pairs]


def test_order_moves_the_highest_file_first_when_shifting_up(tmp_path):
    pending = renames(tmp_path, ("E1", "E2"), ("E2", "E3"))

    ordered, blocked = _renaming.order_renames(pending, {"E1", "E2"})

    assert [rename.target for rename in ordered] == ["E3", "E2"]
    assert blocked == []


def test_order_moves_the_lowest_file_first_when_shifting_down(tmp_path):
    pending = renames(tmp_path, ("E2", "E1"), ("E3", "E2"))

    ordered, blocked = _renaming.order_renames(pending, {"E2", "E3"})

    assert [rename.target for rename in ordered] == ["E1", "E2"]
    assert blocked == []


def test_order_blocks_a_swap(tmp_path):
    pending = renames(tmp_path, ("a", "b"), ("b", "a"))

    ordered, blocked = _renaming.order_renames(pending, {"a", "b"})

    assert ordered == []
    assert blocked == pending


def test_rename_all_renames_after_a_yes(tmp_path, monkeypatch, capsys):
    make(tmp_path, **{"Show - 05.mkv": "five"})
    answer(monkeypatch, "y")

    code = _renaming.rename_all(
        tmp_path, renames(tmp_path, ("Show - 05.mkv", "S01E05.mkv")), []
    )

    assert code == 0
    assert "done - 1 file renamed" in capsys.readouterr().out
    assert files(tmp_path) == {"S01E05.mkv": "five"}


def test_rename_all_changes_nothing_after_a_no(tmp_path, monkeypatch, capsys):
    make(tmp_path, **{"Show - 05.mkv": "five"})
    answer(monkeypatch, "n")

    code = _renaming.rename_all(
        tmp_path, renames(tmp_path, ("Show - 05.mkv", "S01E05.mkv")), []
    )

    assert code == 1
    assert "cancelled" in capsys.readouterr().out
    assert files(tmp_path) == {"Show - 05.mkv": "five"}


def test_rename_all_shows_the_plan_before_asking(tmp_path, monkeypatch, capsys):
    make(tmp_path, **{"Show - 05.mkv": "", "S01E06.mkv": "", "extra.mkv": ""})
    answer(monkeypatch, "n")

    _renaming.rename_all(
        tmp_path,
        renames(
            tmp_path, ("Show - 05.mkv", "S01E05.mkv"), ("S01E06.mkv", "S01E06.mkv")
        ),
        [tmp_path / "extra.mkv"],
    )

    rows = [
        " ".join(line.strip("│ ").split())
        for line in capsys.readouterr().out.splitlines()
    ]
    assert "Show - 05.mkv → S01E05.mkv" in rows
    assert "S01E06.mkv · unchanged" in rows
    assert "extra.mkv" in rows
    assert "2 files, 1 already named, 1 skipped" in rows


def test_rename_all_stops_early_when_everything_is_named(tmp_path, capsys):
    make(tmp_path, **{"S01E01.mkv": "", "S01E02.mkv": ""})

    code = _renaming.rename_all(
        tmp_path,
        renames(tmp_path, ("S01E01.mkv", "S01E01.mkv"), ("S01E02.mkv", "S01E02.mkv")),
        [],
    )

    out = capsys.readouterr().out
    assert code == 0
    assert "nothing to rename, 2 files already named" in out
    assert "?" not in out


def test_rename_all_refuses_two_files_with_one_target(tmp_path, capsys):
    make(tmp_path, **{"Show - 05.mkv": "a", "Show [05].mkv": "b"})

    code = _renaming.rename_all(
        tmp_path,
        renames(
            tmp_path, ("Show - 05.mkv", "S01E05.mkv"), ("Show [05].mkv", "S01E05.mkv")
        ),
        [],
    )

    out = capsys.readouterr().out
    assert code == 1
    assert "two files resolve to the same name" in out
    assert files(tmp_path) == {"Show - 05.mkv": "a", "Show [05].mkv": "b"}


def test_rename_all_refuses_a_name_held_by_a_file_that_stays(tmp_path, capsys):
    make(tmp_path, **{"Show - 05.mkv": "new", "S01E05.mkv": "old"})

    code = _renaming.rename_all(
        tmp_path, renames(tmp_path, ("Show - 05.mkv", "S01E05.mkv")), []
    )

    assert code == 1
    assert "would not move" in capsys.readouterr().out
    assert files(tmp_path) == {"Show - 05.mkv": "new", "S01E05.mkv": "old"}


@pytest.mark.parametrize("step", [1, -1])
def test_rename_all_shifts_a_run_of_files_without_losing_any(
    tmp_path, monkeypatch, step
):
    make(tmp_path, E2="two", E3="three", E4="four")
    answer(monkeypatch, "y")
    pending = renames(tmp_path, *((f"E{n}", f"E{n + step}") for n in (2, 3, 4)))

    code = _renaming.rename_all(tmp_path, pending, [])

    assert code == 0
    assert files(tmp_path) == {
        f"E{2 + step}": "two",
        f"E{3 + step}": "three",
        f"E{4 + step}": "four",
    }


def test_rename_all_returns_one_when_a_rename_fails(tmp_path, monkeypatch, capsys):
    make(tmp_path, **{"a.mkv": "a"})
    answer(monkeypatch, "y")
    pending = renames(tmp_path, ("a.mkv", "S01E01.mkv"), ("gone.mkv", "S01E02.mkv"))

    code = _renaming.rename_all(tmp_path, pending, [])

    assert code == 1
    assert "done with 1 error" in capsys.readouterr().out
    assert files(tmp_path) == {"S01E01.mkv": "a"}


def test_apply_never_overwrites_a_file_that_appeared_after_the_check(tmp_path):
    make(tmp_path, **{"b.mkv": "b", "taken.mkv": "keep"})

    failures = _renaming.apply_renames(renames(tmp_path, ("b.mkv", "taken.mkv")))

    assert failures == 1
    assert files(tmp_path) == {"b.mkv": "b", "taken.mkv": "keep"}


def test_unticked_renames_stay_put_on_a_terminal(tmp_path, monkeypatch):
    make(tmp_path, **{"a.mkv": "a", "b.mkv": "b"})
    pending = renames(tmp_path, ("a.mkv", "S01E01.mkv"), ("b.mkv", "S01E02.mkv"))
    monkeypatch.setattr(_renaming, "interactive", lambda: True)
    monkeypatch.setattr(_renaming, "choose_many", lambda *args, **kwargs: [pending[1]])
    answer(monkeypatch, "y")

    code = _renaming.rename_all(tmp_path, pending, [])

    assert code == 0
    assert files(tmp_path) == {"a.mkv": "a", "S01E02.mkv": "b"}


def test_unticking_a_file_keeps_its_name_taken(tmp_path, monkeypatch, capsys):
    make(tmp_path, **{"S01E02.mkv": "a", "b.mkv": "b"})
    pending = renames(tmp_path, ("S01E02.mkv", "S01E01.mkv"), ("b.mkv", "S01E02.mkv"))
    monkeypatch.setattr(_renaming, "interactive", lambda: True)
    monkeypatch.setattr(_renaming, "choose_many", lambda *args, **kwargs: [pending[1]])

    code = _renaming.rename_all(tmp_path, pending, [])

    assert code == 1
    assert "two files resolve to the same name" in capsys.readouterr().out
    assert files(tmp_path) == {"S01E02.mkv": "a", "b.mkv": "b"}
