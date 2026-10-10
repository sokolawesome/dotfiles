import pathlib
import subprocess

import pytest

from conftest import load_module

backup_system_state = load_module("backup_system_state")

SYSTEM_UNITS = (
    "systemctl",
    "list-unit-files",
    "--state=enabled",
    "--no-pager",
    "--no-legend",
)
USER_UNITS = (
    "systemctl",
    "--user",
    "list-unit-files",
    "--state=enabled",
    "--no-pager",
    "--no-legend",
)
SYSTEM = {
    ("pacman", "-Qqen"): "zsh\nbase\n",
    ("pacman", "-Qqem"): "yay-bin\n",
    ("groups",): "wheel docker\n",
    SYSTEM_UNITS: "sshd.service enabled disabled\n",
    USER_UNITS: "pipewire.service enabled enabled\n",
}


def fake_system(monkeypatch, failing=None):
    def run(command, **_options):
        key = tuple(command)
        if key == failing:
            return subprocess.CompletedProcess(
                command, 1, "", "Failed to connect to bus\n"
            )
        return subprocess.CompletedProcess(command, 0, SYSTEM[key], "")

    monkeypatch.setattr(backup_system_state.subprocess, "run", run)


def saved(dotfiles):
    return {path.name: path.read_text() for path in (dotfiles / "other").iterdir()}


def test_backup_writes_every_list(tmp_path, monkeypatch):
    fake_system(monkeypatch)

    code = backup_system_state.main(["--dotfiles", str(tmp_path)])

    assert code == 0
    assert saved(tmp_path) == {
        "pacman-packages.txt": "base\nzsh\n",
        "yay-packages.txt": "yay-bin\n",
        "user-groups.txt": "docker\nwheel\n",
        "enabled-services.txt": "# system services\nsshd.service\n\n# user services\npipewire.service\n",
    }


def test_a_second_run_reports_no_changes(tmp_path, monkeypatch, capsys):
    fake_system(monkeypatch)
    backup_system_state.main(["--dotfiles", str(tmp_path)])
    capsys.readouterr()

    code = backup_system_state.main(["--dotfiles", str(tmp_path)])

    assert code == 0
    assert "no changes" in capsys.readouterr().out


def test_backup_counts_added_and_removed_packages(tmp_path, monkeypatch, capsys):
    other = tmp_path / "other"
    other.mkdir()
    (other / "pacman-packages.txt").write_text("base\nvim\n")
    fake_system(monkeypatch)

    backup_system_state.main(["--dotfiles", str(tmp_path)])

    assert "1 added, 1 removed" in capsys.readouterr().out
    assert (other / "pacman-packages.txt").read_text() == "base\nzsh\n"


def test_a_failing_command_leaves_every_file_alone(tmp_path, monkeypatch, capsys):
    other = tmp_path / "other"
    other.mkdir()
    (other / "enabled-services.txt").write_text("keep me\n")
    (other / "pacman-packages.txt").write_text("keep me\n")
    fake_system(monkeypatch, failing=USER_UNITS)

    code = backup_system_state.main(["--dotfiles", str(tmp_path)])

    assert code == 1
    assert "Failed to connect to bus" in capsys.readouterr().out
    assert saved(tmp_path) == {
        "enabled-services.txt": "keep me\n",
        "pacman-packages.txt": "keep me\n",
    }


def test_a_missing_command_is_reported(tmp_path, monkeypatch, capsys):
    def run(command, **_options):
        raise FileNotFoundError(2, "No such file or directory", command[0])

    monkeypatch.setattr(backup_system_state.subprocess, "run", run)

    code = backup_system_state.main(["--dotfiles", str(tmp_path)])

    assert code == 1
    assert "No such file or directory" in capsys.readouterr().out


def test_a_write_failure_shows_the_reason(tmp_path, monkeypatch, capsys):
    (tmp_path / "other").write_text("a file where the directory should be")
    fake_system(monkeypatch)

    code = backup_system_state.main(["--dotfiles", str(tmp_path)])

    out = capsys.readouterr().out
    assert code == 1
    assert "could not be written" in out
    assert "File exists" in out


def test_writing_leaves_no_temporary_files(tmp_path, monkeypatch):
    fake_system(monkeypatch)

    backup_system_state.main(["--dotfiles", str(tmp_path)])

    assert sorted(saved(tmp_path)) == [
        "enabled-services.txt",
        "pacman-packages.txt",
        "user-groups.txt",
        "yay-packages.txt",
    ]


def test_a_missing_dotfiles_directory_is_reported(tmp_path, capsys):
    code = backup_system_state.main(["--dotfiles", str(tmp_path / "nope")])

    assert code == 1
    assert "not a directory" in capsys.readouterr().out


def test_dotfiles_defaults_to_the_repo_holding_the_script(monkeypatch):
    monkeypatch.delenv("DOTFILES_PATH", raising=False)

    parsed = backup_system_state.build_parser().parse_args([])

    assert parsed.dotfiles == pathlib.Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    ("script", "reason"),
    [
        ("echo boom >&2; exit 3", "failed: boom"),
        ("exit 3", "failed: exit 3"),
    ],
)
def test_run_text_explains_a_real_failure(script, reason):
    with pytest.raises(backup_system_state.BackupError) as error:
        backup_system_state.run_text(["sh", "-c", script])

    assert reason in str(error.value)


def test_changes_list_the_added_and_removed_names(tmp_path, monkeypatch, capsys):
    other = tmp_path / "other"
    other.mkdir()
    (other / "pacman-packages.txt").write_text("base\nvim\n")
    fake_system(monkeypatch)

    backup_system_state.main(["--dotfiles", str(tmp_path)])

    rows = [
        " ".join(line.strip("│ ").split())
        for line in capsys.readouterr().out.splitlines()
    ]
    assert "pacman packages + zsh" in rows
    assert "- vim" in rows


def test_a_new_file_is_not_listed_name_by_name(tmp_path, monkeypatch, capsys):
    fake_system(monkeypatch)

    backup_system_state.main(["--dotfiles", str(tmp_path)])

    out = capsys.readouterr().out
    assert "changes" not in out
    assert "+ zsh" not in out
