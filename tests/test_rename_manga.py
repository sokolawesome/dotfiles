import io

import pytest
from conftest import load_module

rename_manga = load_module("rename_manga")


def answer(monkeypatch, line):
    monkeypatch.setattr("sys.stdin", io.StringIO(f"{line}\n"))


def library(tmp_path, *names):
    for name in names:
        (tmp_path / name).write_text(name)
    return tmp_path


def files(directory):
    return {path.name: path.read_text() for path in directory.iterdir() if path.is_file()}


def target(name):
    parsed = rename_manga.parse_kind_and_number(name)
    if parsed is None:
        return None
    return rename_manga.target_name(*parsed, rename_manga.archive_suffix(name))


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("Dandadan v01 (2022) (Digital) (1r0n).cbz", "01.cbz"),
        ("Dandadan 222 (2025) (Digital) (1r0n).cbz", "c222.cbz"),
        ("Dandadan 247.cbz", "c247.cbz"),
        ("Berserk (1989) 042.cbz", "c042.cbz"),
        ("One Piece 1050.cbz", "c1050.cbz"),
        ("One Piece 1050 (2022) (Digital).cbz", "c1050.cbz"),
        ("v9.cbz", "09.cbz"),
        ("vol.09.cbz", "09.cbz"),
        ("Volume 9.cbz", "09.cbz"),
        ("VOLUME 3.cbz", "03.cbz"),
        ("v 5.cbz", "05.cbz"),
        ("v007.cbz", "07.cbz"),
        ("[v01].cbz", "01.cbz"),
        ("vol.1-2.cbz", "01.cbz"),
        ("Vol 3 Extra.cbz", "03.cbz"),
        ("c3.cbz", "c003.cbz"),
        ("ch.03.cbz", "c003.cbz"),
        ("Chapter 3.cbz", "c003.cbz"),
        ("CH 45.cbz", "c045.cbz"),
        ("v01.cbr", "01.cbr"),
        ("v01.CBZ", "01.cbz"),
        ("01.cbz", "01.cbz"),
        ("14.cbz", "14.cbz"),
        ("7.cbz", "07.cbz"),
        ("c001.cbz", "c001.cbz"),
        ("c1050.cbz", "c1050.cbz"),
    ],
)
def test_target_name(name, expected):
    assert target(name) == expected


@pytest.mark.parametrize(
    "name",
    [
        "extra.cbz",
        "One Piece.cbz",
        "Series Title 2024.cbz",
        "Series Title 1999.cbz",
        "Series Title (2024).cbz",
        "x264 2020.cbz",
    ],
)
def test_no_number_found(name):
    assert target(name) is None


def test_renames_volumes_and_chapters(tmp_path, monkeypatch, capsys):
    library(
        tmp_path,
        "Dandadan v01 (2022) (Digital) (1r0n).cbz",
        "Dandadan 222 (2025) (Digital) (1r0n).cbz",
        "Dandadan 247.cbz",
    )
    answer(monkeypatch, "y")

    code = rename_manga.main([str(tmp_path)])

    assert code == 0
    assert files(tmp_path) == {
        "01.cbz": "Dandadan v01 (2022) (Digital) (1r0n).cbz",
        "c222.cbz": "Dandadan 222 (2025) (Digital) (1r0n).cbz",
        "c247.cbz": "Dandadan 247.cbz",
    }
    assert "done - 3 files renamed" in capsys.readouterr().out


def test_preview_lists_volumes_first_then_chapters_in_number_order(tmp_path, monkeypatch, capsys):
    library(tmp_path, "c1000.cbz", "Show 999.cbz", "Show v02.cbz", "Show v01.cbz")
    answer(monkeypatch, "n")

    rename_manga.main([str(tmp_path)])

    out = capsys.readouterr().out
    positions = [out.index(name) for name in ("Show v01.cbz", "Show v02.cbz", "Show 999.cbz", "c1000.cbz")]
    assert positions == sorted(positions)


def test_files_without_a_number_are_listed_and_left_alone(tmp_path, monkeypatch, capsys):
    library(tmp_path, "v01.cbz", "extra.cbz", "cover.jpg")
    answer(monkeypatch, "y")

    rename_manga.main([str(tmp_path)])

    assert "extra.cbz" in capsys.readouterr().out
    assert sorted(files(tmp_path)) == ["01.cbz", "cover.jpg", "extra.cbz"]


def test_two_files_for_one_volume_rename_nothing(tmp_path, capsys):
    library(tmp_path, "v01.cbz", "vol.1.cbz")

    code = rename_manga.main([str(tmp_path)])

    assert code == 1
    assert "two files resolve to the same name" in capsys.readouterr().out
    assert sorted(files(tmp_path)) == ["v01.cbz", "vol.1.cbz"]


def test_files_in_subfolders_are_ignored(tmp_path, monkeypatch):
    library(tmp_path, "v01.cbz")
    (tmp_path / "nested").mkdir()
    (tmp_path / "nested" / "v02.cbz").write_text("nested")
    answer(monkeypatch, "y")

    rename_manga.main([str(tmp_path)])

    assert list(files(tmp_path)) == ["01.cbz"]
    assert (tmp_path / "nested" / "v02.cbz").exists()


@pytest.mark.parametrize(
    ("names", "message"),
    [
        ((), "no manga files found"),
        (("cover.jpg",), "no manga files found"),
        (("extra.cbz",), "could not extract numbers"),
    ],
)
def test_nothing_to_work_with_is_an_error(tmp_path, capsys, names, message):
    library(tmp_path, *names)

    code = rename_manga.main([str(tmp_path)])

    assert code == 1
    assert message in capsys.readouterr().out


def test_a_missing_directory_is_an_error(tmp_path, capsys):
    code = rename_manga.main([str(tmp_path / "nope")])

    assert code == 1
    assert "is not a directory" in capsys.readouterr().out
