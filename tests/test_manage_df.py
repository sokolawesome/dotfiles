import pathlib

import pytest
from conftest import load_module

manage_df = load_module("manage_df")

ACTIONS = manage_df.ACTIONS


@pytest.mark.parametrize(
    ("name", "flag", "verb"),
    [
        ("stow", "", "stowing"),
        ("restow", "-R", "restowing"),
        ("unstow", "-D", "unstowing"),
        ("dry-run", "-n", "dry-run"),
    ],
)
def test_action_flags_match_the_fish_version(name, flag, verb):
    assert ACTIONS[name].flag == flag
    assert ACTIONS[name].verb == verb


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("home", str(pathlib.Path.home())),
        ("config", str(pathlib.Path.home() / ".config")),
        ("bin", str(pathlib.Path.home() / "bin")),
        ("agents", str(pathlib.Path.home() / ".agents")),
    ],
)
def test_package_targets_match_the_fish_version(name, expected):
    assert str(manage_df.PACKAGES[name]) == expected


def test_stow_command_shape():
    command = manage_df.stow_command(ACTIONS["restow"], pathlib.Path("/t"), "bin", False)

    assert command == ["stow", "--no-folding", "-R", "-t", "/t", "bin"]


def test_stow_command_without_a_flag():
    command = manage_df.stow_command(ACTIONS["stow"], pathlib.Path("/t"), "config", False)

    assert command == ["stow", "--no-folding", "-t", "/t", "config"]


def test_stow_command_with_verbose():
    command = manage_df.stow_command(ACTIONS["stow"], pathlib.Path("/t"), "config", True)

    assert "-v" in command


@pytest.mark.parametrize(
    ("requested", "expected"),
    [
        ([], ["home", "config", "bin", "agents"]),
        (["bin"], ["bin"]),
        (["agents", "config"], ["config", "agents"]),
    ],
)
def test_selected_packages(requested, expected):
    assert manage_df.selected_packages(requested) == expected


def test_selected_packages_rejects_an_unknown_name():
    with pytest.raises(manage_df.ManageError) as error:
        manage_df.selected_packages(["nope"])

    assert "unknown package(s): nope" in str(error.value)


def test_restow_and_delete_are_mutually_exclusive(capsys):
    with pytest.raises(SystemExit) as exit_info:
        manage_df.main(["-R", "-D"])

    assert exit_info.value.code == 2
    assert "not allowed with" in capsys.readouterr().err


def test_restow_and_dry_run_are_mutually_exclusive(capsys):
    with pytest.raises(SystemExit) as exit_info:
        manage_df.main(["-R", "-n"])

    assert exit_info.value.code == 2


def test_find_stow_fails_when_absent(monkeypatch):
    monkeypatch.setattr(manage_df.shutil, "which", lambda name: None)

    with pytest.raises(manage_df.ManageError) as error:
        manage_df.find_stow()

    assert "gnu stow not found" in str(error.value)


def test_find_stow_returns_the_path():
    assert manage_df.find_stow().endswith("stow")


def test_ensure_target_creates_nested_parents(tmp_path):
    target = tmp_path / "a" / "b"

    manage_df.ensure_target(target)

    assert target.is_dir()


def test_ensure_target_never_creates_bin_inside_bin(tmp_path):
    target = tmp_path / "bin"

    manage_df.ensure_target(target)

    assert target.is_dir()
    assert not (target / "bin").exists()


def test_run_package_reports_a_missing_source(tmp_path, monkeypatch):
    monkeypatch.setattr(manage_df, "PACKAGES", {"config": tmp_path / "config"})
    monkeypatch.setenv("DOTFILES_PATH", str(tmp_path / "empty-repo"))

    result = manage_df.run_package("config", ACTIONS["stow"], False)

    assert result.outcome == "missing"
    assert not (tmp_path / "config").exists()


def test_run_package_marks_a_failure(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    (repo / "config").mkdir(parents=True)
    monkeypatch.setattr(manage_df, "PACKAGES", {"config": tmp_path / "target"})
    monkeypatch.setenv("DOTFILES_PATH", str(repo))

    class Finished:
        returncode = 1
        stdout = ""
        stderr = "stow: cannot stow"

    monkeypatch.setattr(manage_df.subprocess, "run", lambda command, **kwargs: Finished())

    result = manage_df.run_package("config", ACTIONS["stow"], False)

    assert result.outcome == "failed"
    assert "cannot stow" in result.detail


def test_run_package_succeeds(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    (repo / "bin").mkdir(parents=True)
    monkeypatch.setattr(manage_df, "PACKAGES", {"bin": tmp_path / "target" / "bin"})
    monkeypatch.setenv("DOTFILES_PATH", str(repo))

    class Finished:
        returncode = 0
        stdout = ""
        stderr = ""

    monkeypatch.setattr(manage_df.subprocess, "run", lambda command, **kwargs: Finished())

    result = manage_df.run_package("bin", ACTIONS["stow"], False)

    assert result.outcome == "done"
    assert (tmp_path / "target" / "bin").is_dir()


def test_main_reports_an_unknown_package(capsys):
    code = manage_df.main(["-p", "nope"])

    assert code == 1
    assert "unknown package" in capsys.readouterr().out


def test_main_reports_a_missing_stow(monkeypatch, capsys):
    monkeypatch.setattr(manage_df.shutil, "which", lambda name: None)

    code = manage_df.main([])

    assert code == 1
    assert "gnu stow not found" in capsys.readouterr().out


def test_main_runs_only_the_requested_packages(monkeypatch, capsys):
    seen = []
    monkeypatch.setattr(manage_df.shutil, "which", lambda name: "/usr/bin/stow")
    monkeypatch.setattr(manage_df, "run_package", lambda p, a, v: seen.append(p) or manage_df.Result(p, pathlib.Path("/t"), "done"))

    code = manage_df.main(["-p", "bin"])

    assert code == 0
    assert seen == ["bin"]


def test_main_returns_one_on_failure(monkeypatch, capsys):
    monkeypatch.setattr(manage_df.shutil, "which", lambda name: "/usr/bin/stow")
    monkeypatch.setattr(
        manage_df,
        "run_package",
        lambda p, a, v: manage_df.Result(p, pathlib.Path("/t"), "failed", "boom"),
    )

    code = manage_df.main(["-p", "bin"])

    assert code == 1
    assert "failed" in capsys.readouterr().out


def test_report_renders_without_crashing(capsys):
    rows = [manage_df.Result("bin", pathlib.Path("/t/bin"), "done"), manage_df.Result("agents", pathlib.Path("/t/.agents"), "missing")]

    code = manage_df.report(ACTIONS["stow"], rows, False)

    assert code == 0
    out = capsys.readouterr().out
    assert "bin" in out and "agents" in out


def test_report_shows_detail_when_verbose(capsys):
    rows = [manage_df.Result("bin", pathlib.Path("/t/bin"), "done", "LINK: thing")]

    manage_df.report(ACTIONS["stow"], rows, True)

    out = capsys.readouterr().out
    assert "LINK: thing" in out
    assert "stow output" in out