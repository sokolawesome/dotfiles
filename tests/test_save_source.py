import pytest
import tomllib

from conftest import HOMELAB, load_module

save_source = load_module("save_source", HOMELAB)
SOURCE_FILE = save_source.SOURCE_FILE


def read(directory):
    return tomllib.loads((directory / SOURCE_FILE).read_text())


def hook(path, *options, hash_="abc123", name="Show"):
    return save_source.main(
        ["--hash", hash_, "--name", name, "--path", str(path), *options]
    )


def release(tmp_path, *files):
    root = tmp_path / "[Group] Show [Season 1 + Movie]"
    for name in files:
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).write_text(name)
    return root


def test_the_hook_writes_every_field_qbittorrent_passes(tmp_path):
    code = hook(
        tmp_path,
        "--tracker",
        "udp://tracker:7777",
        "--size",
        "3539545441",
        "--category",
        "anime",
        "--tags",
        "bd,dual audio",
        "--comment",
        "https://nyaa.si/view/1",
        name="[Group] Show & Co",
    )

    torrent = read(tmp_path)["torrent"]
    assert code == 0
    assert torrent["hash"] == "abc123"
    assert torrent["magnet"] == (
        "magnet:?xt=urn:btih:abc123&dn=%5BGroup%5D%20Show%20%26%20Co&xl=3539545441&tr=udp:%2F%2Ftracker:7777"
    )
    assert torrent["size"] == "3.30 GiB"
    assert torrent["category"] == "anime"
    assert torrent["tags"] == "bd,dual audio"
    assert torrent["comment"] == "https://nyaa.si/view/1"
    assert torrent["finished"]


def test_the_hook_leaves_out_empty_fields(tmp_path):
    hook(tmp_path, "--category", "", "--comment", "")

    assert set(read(tmp_path)["torrent"]) == {"name", "hash", "magnet", "finished"}


def test_every_folder_with_a_video_gets_the_torrent(tmp_path):
    root = release(
        tmp_path,
        "Season 1/Show - 01.mkv",
        "Movie/Show Movie.mkv",
        "Subs/Season 1/Show - 01.ass",
        "Audio/Show - 01.mka",
    )

    hook(root)

    marked = sorted(
        path.parent.relative_to(root).as_posix() for path in root.rglob(SOURCE_FILE)
    )
    assert marked == [".", "Movie", "Season 1"]
    assert read(root / "Movie")["torrent"] == read(root)["torrent"]


def test_a_second_run_rewrites_old_files_and_fills_missing_ones(tmp_path, capsys):
    root = release(tmp_path, "Season 1/Show - 01.mkv", "Movie/Show Movie.mkv")
    (root / SOURCE_FILE).write_text('[torrent]\nhash = "old"\n')

    hook(root)

    err = capsys.readouterr().err
    assert read(root)["torrent"]["hash"] == "abc123"
    assert f"updated: {root}" in err
    assert f"written: {root / 'Movie'}" in err
    assert f"written: {root / 'Season 1'}" in err


def test_the_same_data_twice_leaves_the_file_alone(tmp_path):
    torrent = {"name": "Show", "hash": "abc123"}
    save_source.write_torrent(tmp_path, torrent)

    assert save_source.write_torrent(tmp_path, torrent) == save_source.UNCHANGED


def test_a_missing_download_is_reported(tmp_path, capsys):
    code = hook(tmp_path / "gone")

    assert code == 1
    assert f"not found: {tmp_path / 'gone'}" in capsys.readouterr().err


def test_a_single_file_alone_in_its_folder_gets_the_torrent(tmp_path):
    folder = tmp_path / "[Judas] Shiboyugi 44"
    folder.mkdir()
    movie = folder / "[Judas] SHIBOYUGI Movie.mkv"
    movie.write_text("video")
    (folder / "[Judas] SHIBOYUGI Movie.en.ass").write_text("subs")

    code = hook(movie)

    assert code == 0
    assert read(folder)["torrent"]["hash"] == "abc123"


def test_a_single_file_in_a_shared_folder_is_left_alone(tmp_path, capsys):
    (tmp_path / "other release").mkdir()
    episode = tmp_path / "episode.mkv"
    episode.write_text("video")

    code = hook(episode)

    assert code == 1
    assert "single file in a folder with other downloads" in capsys.readouterr().err
    assert not (tmp_path / SOURCE_FILE).exists()


def test_a_single_file_next_to_another_video_is_left_alone(tmp_path):
    (tmp_path / "other.mkv").write_text("video")
    episode = tmp_path / "episode.mkv"
    episode.write_text("video")

    code = hook(episode)

    assert code == 1
    assert not (tmp_path / SOURCE_FILE).exists()


@pytest.mark.parametrize(
    ("size", "expected"),
    [
        (512, "512 B"),
        (1536, "1.50 KiB"),
        (3_539_545_441, "3.30 GiB"),
        (5 * 1024**5, "5120.00 TiB"),
    ],
)
def test_size_reads_in_the_largest_fitting_unit(size, expected):
    assert save_source.format_size(size) == expected
