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
def test_action_flags(name, flag, verb):
    assert ACTIONS[name].flag == flag
    assert ACTIONS[name].verb == verb


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("home", str(pathlib.Path.home())),
        ("config", str(pathlib.Path.home() / ".config")),
        ("bin", str(pathlib.Path.home() / "bin")),
        ("agents", str(pathlib.Path.home() / ".agents")),
        ("claude", str(pathlib.Path.home() / ".claude")),
    ],
)
def test_package_targets(name, expected):
    assert str(manage_df.PACKAGES[name]) == expected


def test_stow_command_shape():
    command = manage_df.stow_command(ACTIONS["restow"], pathlib.Path("/r"), pathlib.Path("/t"), "bin", False)

    assert command == ["stow", "--no-folding", "-R", "--dir", "/r", "-t", "/t", "bin"]


def test_stow_command_without_a_flag():
    command = manage_df.stow_command(ACTIONS["stow"], pathlib.Path("/r"), pathlib.Path("/t"), "config", False)

    assert command == ["stow", "--no-folding", "--dir", "/r", "-t", "/t", "config"]


def test_stow_command_with_verbose():
    command = manage_df.stow_command(ACTIONS["stow"], pathlib.Path("/r"), pathlib.Path("/t"), "config", True)

    assert "-v" in command


def test_stow_command_names_the_source_so_cwd_does_not_matter():
    command = manage_df.stow_command(ACTIONS["stow"], pathlib.Path("/repo"), pathlib.Path("/t"), "bin", False)

    assert "--dir" in command
    assert command[command.index("--dir") + 1] == "/repo"


@pytest.mark.parametrize(
    ("requested", "expected"),
    [
        ([], ["home", "config", "bin", "agents", "claude"]),
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


def test_find_stow_returns_the_path(monkeypatch):
    monkeypatch.setattr(manage_df.shutil, "which", lambda name: "/usr/bin/stow")

    assert manage_df.find_stow() == "/usr/bin/stow"


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

    result = manage_df.run_package(tmp_path / "empty-repo", "config", ACTIONS["stow"], False)

    assert result.outcome == "missing"
    assert not (tmp_path / "config").exists()


def test_run_package_marks_a_failure(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    (repo / "config").mkdir(parents=True)
    monkeypatch.setattr(manage_df, "PACKAGES", {"config": tmp_path / "target"})

    class Finished:
        returncode = 1
        stdout = ""
        stderr = "stow: cannot stow"

    monkeypatch.setattr(manage_df.subprocess, "run", lambda command, **kwargs: Finished())

    result = manage_df.run_package(repo, "config", ACTIONS["stow"], False)

    assert result.outcome == "failed"
    assert "cannot stow" in result.detail


def test_run_package_succeeds(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    (repo / "bin").mkdir(parents=True)
    monkeypatch.setattr(manage_df, "PACKAGES", {"bin": tmp_path / "target" / "bin"})

    class Finished:
        returncode = 0
        stdout = ""
        stderr = ""

    monkeypatch.setattr(manage_df.subprocess, "run", lambda command, **kwargs: Finished())

    result = manage_df.run_package(repo, "bin", ACTIONS["stow"], False)

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
    monkeypatch.setattr(manage_df, "run_package", lambda s, p, a, v: seen.append(p) or manage_df.Result(p, pathlib.Path("/t"), "done"))

    code = manage_df.main(["-p", "bin"])

    assert code == 0
    assert seen == ["bin"]


def test_main_returns_one_on_failure(monkeypatch, capsys):
    monkeypatch.setattr(manage_df.shutil, "which", lambda name: "/usr/bin/stow")
    monkeypatch.setattr(
        manage_df,
        "run_package",
        lambda s, p, a, v: manage_df.Result(p, pathlib.Path("/t"), "failed", "boom"),
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

def test_main_works_from_any_directory(tmp_path, monkeypatch):
    source = tmp_path / "repo"
    for name in ("home", "config", "bin", "agents"):
        (source / name).mkdir(parents=True)
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.setattr(manage_df.shutil, "which", lambda name: "/usr/bin/stow")
    monkeypatch.chdir(elsewhere)
    seen = {}

    def fake_run_package(src, package, action, verbose):
        seen["source"] = src
        return manage_df.Result(package, pathlib.Path("/t"), "done")

    monkeypatch.setattr(manage_df, "run_package", fake_run_package)

    code = manage_df.main(["--dotfiles", str(source)])

    assert code == 0
    assert seen["source"] == source


def test_main_rejects_a_bad_source(tmp_path, capsys):
    code = manage_df.main(["--dotfiles", str(tmp_path / "nope")])

    assert code == 1
    assert "not a directory" in capsys.readouterr().out


def test_source_defaults_to_the_script_parent(monkeypatch):
    monkeypatch.delenv("DOTFILES_PATH", raising=False)

    parsed = manage_df.build_parser().parse_args([])

    assert parsed.dotfiles == pathlib.Path(manage_df.__file__).resolve().parents[1]
