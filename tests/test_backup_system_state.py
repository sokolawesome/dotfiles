import subprocess

import pytest
from conftest import load_module

backup_system_state = load_module("backup_system_state")

Outcome = backup_system_state.Outcome


def artifact(label, target, content):
    return backup_system_state.Artifact(label, target, content)


def test_run_text_returns_stdout():
    assert backup_system_state.run_text(["echo", "hello"], "echo") == "hello\n"


def test_run_text_reports_a_failure():
    with pytest.raises(backup_system_state.BackupError) as error:
        backup_system_state.run_text(["sh", "-c", "echo boom >&2; exit 3"], "probe")

    assert "probe failed: boom" in str(error.value)


def test_run_text_reports_a_missing_command():
    with pytest.raises(backup_system_state.BackupError):
        backup_system_state.run_text(["definitely-not-a-command"], "probe")


@pytest.mark.parametrize(
    ("output", "expected"),
    [
        ("7zip 26.03-1\nadw-gtk-theme 6.5-1\n", ["7zip", "adw-gtk-theme"]),
        ("one 1-1\n\ntwo 2-1\n", ["one", "two"]),
        ("", []),
    ],
)
def test_installed_packages_takes_the_first_column(output, expected, monkeypatch):
    monkeypatch.setattr(backup_system_state, "run_text", lambda command, label: output)

    assert backup_system_state.installed_packages(foreign=False) == expected


def test_installed_packages_ignores_the_version_column(monkeypatch):
    monkeypatch.setattr(
        backup_system_state, "run_text", lambda command, label: "7zip 26.03-1\n"
    )

    assert backup_system_state.installed_packages(foreign=False) == ["7zip"]


@pytest.mark.parametrize(
    ("all_names", "aur_names", "expected"),
    [
        (["a", "b", "c"], ["b"], ["a", "c"]),
        (["a", "b"], [], ["a", "b"]),
        (["a"], ["a"], []),
        ([], [], []),
    ],
)
def test_repo_packages_removes_foreign(all_names, aur_names, expected):
    assert backup_system_state.repo_packages(all_names, aur_names) == expected


def test_user_groups(monkeypatch):
    monkeypatch.setattr(backup_system_state, "run_text", lambda command, label: "wheel input docker\n")

    assert backup_system_state.user_groups() == ["docker", "input", "wheel"]


def test_enabled_services_labels_each_scope(monkeypatch):
    calls = []

    def fake(system_scope):
        calls.append(system_scope)
        return ["sshd.service"]

    monkeypatch.setattr(backup_system_state, "unit_files", fake)

    lines = backup_system_state.enabled_services()

    assert lines[0] == "# system services"
    assert "sshd.service" in lines
    assert "# user services" in lines
    assert len(calls) == 2


def test_unit_files_asks_systemctl(monkeypatch):
    seen = []

    class Finished:
        returncode = 0
        stdout = "sshd.service enabled\n\n"
        stderr = ""

    def fake_run(command, **kwargs):
        seen.append(command)
        return Finished()

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = backup_system_state.unit_files(system_scope=True)

    assert result == ["sshd.service"]
    assert seen[0] == ["systemctl", "list-unit-files", "--state=enabled", "--no-pager", "--no-legend"]


def test_unit_files_scopes_to_the_user(monkeypatch):
    seen = []

    class Finished:
        returncode = 0
        stdout = "pipewire.service enabled\n"
        stderr = ""

    monkeypatch.setattr(subprocess, "run", lambda command, **kwargs: seen.append(command) or Finished())

    backup_system_state.unit_files(system_scope=False)

    assert seen[0][:2] == ["systemctl", "--user"]


def test_unit_files_tolerates_a_missing_user_bus(monkeypatch):
    class Finished:
        returncode = 1
        stdout = ""
        stderr = "Failed to connect"

    monkeypatch.setattr(subprocess, "run", lambda command, **kwargs: Finished())

    assert backup_system_state.unit_files(system_scope=False) == []


@pytest.mark.parametrize(
    ("new", "old", "expected"),
    [
        ("a\nb\nc\n", "a\nb\n", (1, 0)),
        ("a\nb\n", "a\nb\nc\n", (0, 1)),
        ("a\nb\n", "a\nb\n", (0, 0)),
        ("", "a\nb\n", (0, 2)),
    ],
)
def test_count_changes(new, old, expected):
    assert backup_system_state.count_changes(new, old) == expected


def test_write_atomically_leaves_no_temporary(tmp_path):
    target = tmp_path / "list.txt"
    target.write_text("old\n")

    backup_system_state.write_atomically(target, "new\n")

    assert target.read_text() == "new\n"
    assert [p.name for p in tmp_path.iterdir()] == ["list.txt"]


def test_apply_creates_a_missing_file(tmp_path):
    target = tmp_path / "list.txt"

    result = backup_system_state.apply(artifact("list", target, "a\nb\n"), dry_run=False)

    assert result.outcome is Outcome.CREATED
    assert target.read_text() == "a\nb\n"


def test_apply_updates_a_changed_file(tmp_path):
    target = tmp_path / "list.txt"
    target.write_text("a\n")

    result = backup_system_state.apply(artifact("list", target, "a\nb\n"), dry_run=False)

    assert result.outcome is Outcome.UPDATED
    assert result.added == 1
    assert result.removed == 0
    assert target.read_text() == "a\nb\n"


def test_apply_leaves_an_identical_file_alone(tmp_path):
    target = tmp_path / "list.txt"
    target.write_text("a\nb\n")

    result = backup_system_state.apply(artifact("list", target, "a\nb\n"), dry_run=False)

    assert result.outcome is Outcome.UNCHANGED


def test_apply_does_not_touch_a_file_in_diff_mode(tmp_path):
    target = tmp_path / "list.txt"
    target.write_text("a\n")

    result = backup_system_state.apply(artifact("list", target, "a\nb\n"), dry_run=True)

    assert result.outcome is Outcome.UPDATED
    assert target.read_text() == "a\n"


def test_apply_does_not_create_a_file_in_diff_mode(tmp_path):
    target = tmp_path / "list.txt"

    result = backup_system_state.apply(artifact("list", target, "a\n"), dry_run=True)

    assert result.outcome is Outcome.CREATED
    assert not target.exists()


def test_apply_reports_a_write_failure(tmp_path):
    target = tmp_path / "missing" / "list.txt"

    result = backup_system_state.apply(artifact("list", target, "a\n"), dry_run=False)

    assert result.outcome is Outcome.FAILED


def test_a_failed_collector_never_reaches_the_target(tmp_path, monkeypatch):
    target = tmp_path / "other" / "pacman-packages.txt"
    target.parent.mkdir()
    target.write_text("keep-me\n")

    def boom(command, label):
        raise backup_system_state.BackupError("pacman -Qe failed: database lock")

    monkeypatch.setattr(backup_system_state, "run_text", boom)

    with pytest.raises(backup_system_state.BackupError):
        backup_system_state.collect(tmp_path)

    assert target.read_text() == "keep-me\n"


def test_collect_writes_all_four_files(tmp_path, monkeypatch):
    monkeypatch.setattr(
        backup_system_state,
        "installed_packages",
        lambda foreign: ["b", "a"] if foreign else ["keep-me", "keep-me", "b", "z-foreign"],
    )
    monkeypatch.setattr(backup_system_state, "user_groups", lambda: ["wheel"])
    monkeypatch.setattr(backup_system_state, "enabled_services", lambda: ["# system services", "sshd.service"])

    artifacts = backup_system_state.collect(tmp_path)

    assert [a.target.name for a in artifacts] == [
        "pacman-packages.txt",
        "yay-packages.txt",
        "user-groups.txt",
        "enabled-services.txt",
    ]
    assert artifacts[0].content == "keep-me\nz-foreign\n"


def test_collect_creates_the_other_directory(tmp_path, monkeypatch):
    monkeypatch.setattr(backup_system_state, "installed_packages", lambda foreign: [])
    monkeypatch.setattr(backup_system_state, "user_groups", lambda: [])
    monkeypatch.setattr(backup_system_state, "enabled_services", lambda: [])

    backup_system_state.collect(tmp_path)

    assert (tmp_path / "other").is_dir()


def test_main_creates_the_other_directory(tmp_path, monkeypatch):
    monkeypatch.setattr(backup_system_state, "installed_packages", lambda foreign: [] if foreign else ["a"])
    monkeypatch.setattr(backup_system_state, "user_groups", lambda: [])
    monkeypatch.setattr(backup_system_state, "enabled_services", lambda: [])

    code = backup_system_state.main(["--dotfiles", str(tmp_path)])

    assert code == 0
    assert (tmp_path / "other" / "pacman-packages.txt").read_text() == "a\n"


def test_main_reports_a_missing_repo(tmp_path, capsys):
    code = backup_system_state.main(["--dotfiles", str(tmp_path / "nope")])

    assert code == 1
    out = capsys.readouterr().out
    assert "not a directory" in out.replace("\n", " ")


def test_main_diff_writes_nothing(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(backup_system_state, "installed_packages", lambda foreign: ["a"])
    monkeypatch.setattr(backup_system_state, "user_groups", lambda: [])
    monkeypatch.setattr(backup_system_state, "enabled_services", lambda: [])
    (tmp_path / "other").mkdir()

    code = backup_system_state.main(["--diff", "--dotfiles", str(tmp_path)])

    assert code == 0
    assert "would change" in capsys.readouterr().out
    assert list((tmp_path / "other").iterdir()) == []


def test_main_writes_and_reports_unchanged_on_a_second_run(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(backup_system_state, "installed_packages", lambda foreign: ["a"])
    monkeypatch.setattr(backup_system_state, "user_groups", lambda: [])
    monkeypatch.setattr(backup_system_state, "enabled_services", lambda: [])
    (tmp_path / "other").mkdir()

    backup_system_state.main(["--dotfiles", str(tmp_path)])
    capsys.readouterr()
    code = backup_system_state.main(["--dotfiles", str(tmp_path)])

    assert code == 0
    assert "no changes" in capsys.readouterr().out


def test_main_reports_a_collector_failure(tmp_path, monkeypatch, capsys):
    def boom(command, label):
        raise backup_system_state.BackupError("pacman -Qe failed: exit 1")

    monkeypatch.setattr(backup_system_state, "run_text", boom)

    code = backup_system_state.main(["--dotfiles", str(tmp_path)])

    assert code == 1
    assert "pacman -Qe failed" in capsys.readouterr().out