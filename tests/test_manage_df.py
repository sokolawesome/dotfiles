import pathlib
import shutil

import pytest
from conftest import load_module

manage_df = load_module("manage_df")

needs_stow = pytest.mark.skipif(shutil.which("stow") is None, reason="gnu stow is not installed")


@pytest.fixture
def repo(tmp_path, monkeypatch):
    source = tmp_path / "dotfiles"
    (source / "bin").mkdir(parents=True)
    (source / "bin" / "tool").write_text("tool")
    (source / "config" / "app").mkdir(parents=True)
    (source / "config" / "app" / "settings.toml").write_text("settings")
    targets = {"bin": tmp_path / "home" / "bin", "config": tmp_path / "home" / ".config"}
    monkeypatch.setattr(manage_df, "PACKAGES", targets)
    return source, targets


def run(source, *flags):
    return manage_df.main([*flags, "--dotfiles", str(source)])


@needs_stow
def test_stow_links_every_package(repo):
    source, targets = repo

    code = run(source)

    assert code == 0
    assert (targets["bin"] / "tool").resolve() == source / "bin" / "tool"
    assert (targets["config"] / "app" / "settings.toml").resolve() == source / "config" / "app" / "settings.toml"


@needs_stow
def test_stow_creates_real_directories_instead_of_folding(repo):
    source, targets = repo

    run(source)

    assert not (targets["config"] / "app").is_symlink()


@needs_stow
def test_package_flag_limits_the_run(repo):
    source, targets = repo

    code = run(source, "-p", "bin")

    assert code == 0
    assert (targets["bin"] / "tool").is_symlink()
    assert not targets["config"].exists()


@needs_stow
def test_unstow_removes_the_links(repo):
    source, targets = repo
    run(source)

    code = run(source, "-D")

    assert code == 0
    assert not (targets["bin"] / "tool").exists()
    assert (source / "bin" / "tool").read_text() == "tool"


@needs_stow
def test_restow_links_a_file_added_after_the_first_stow(repo):
    source, targets = repo
    run(source)
    (source / "bin" / "new-tool").write_text("new")

    code = run(source, "-R")

    assert code == 0
    assert (targets["bin"] / "new-tool").is_symlink()


@needs_stow
def test_dry_run_on_a_missing_target_creates_nothing(repo, capsys):
    source, targets = repo

    code = run(source, "-n")

    out = capsys.readouterr().out
    assert code == 0
    assert "MKDIR" in out
    assert not targets["bin"].exists()


@needs_stow
def test_dry_run_on_an_existing_target_lists_each_link(repo, capsys):
    source, targets = repo
    targets["bin"].mkdir(parents=True)

    code = run(source, "-n", "-p", "bin")

    out = capsys.readouterr().out
    assert code == 0
    assert "LINK: tool" in out
    assert "simulation mode" not in out
    assert list(targets["bin"].iterdir()) == []


def test_unstow_with_a_missing_target_creates_nothing(repo):
    source, targets = repo

    code = run(source, "-D")

    assert code == 0
    assert not targets["bin"].exists()


@needs_stow
def test_verbose_shows_the_links_stow_made(repo, capsys):
    source, _ = repo

    run(source, "-v", "-p", "bin")

    assert "LINK: tool" in capsys.readouterr().out


@needs_stow
def test_a_conflicting_file_fails_the_package_and_stays_untouched(repo, capsys):
    source, targets = repo
    targets["bin"].mkdir(parents=True)
    (targets["bin"] / "tool").write_text("mine")

    code = run(source, "-p", "bin")

    out = capsys.readouterr().out
    assert code == 1
    assert "failed" in out
    assert "tool" in out
    assert (targets["bin"] / "tool").read_text() == "mine"


@needs_stow
def test_a_package_missing_from_the_repo_is_reported_and_skipped(repo, capsys):
    source, targets = repo
    shutil.rmtree(source / "config")

    code = run(source)

    assert code == 0
    assert "missing" in capsys.readouterr().out
    assert not targets["config"].exists()


def test_unknown_package_is_rejected(repo, capsys):
    source, _ = repo

    code = run(source, "-p", "nope")

    assert code == 1
    assert "unknown package(s): nope" in capsys.readouterr().out


def test_missing_stow_is_reported(repo, monkeypatch, capsys):
    source, _ = repo
    monkeypatch.setattr(manage_df.shutil, "which", lambda name: None)

    code = run(source)

    assert code == 1
    assert "gnu stow not found" in capsys.readouterr().out


def test_missing_dotfiles_directory_is_reported(tmp_path, capsys):
    code = manage_df.main(["--dotfiles", str(tmp_path / "nope")])

    assert code == 1
    assert "not a directory" in capsys.readouterr().out


def test_restow_and_delete_cannot_be_combined(capsys):
    with pytest.raises(SystemExit) as exit_info:
        manage_df.main(["-R", "-D"])

    assert exit_info.value.code == 2


def test_dotfiles_defaults_to_the_repo_holding_the_script(monkeypatch):
    monkeypatch.delenv("DOTFILES_PATH", raising=False)

    parsed = manage_df.build_parser().parse_args([])

    assert parsed.dotfiles == pathlib.Path(__file__).resolve().parents[1]
