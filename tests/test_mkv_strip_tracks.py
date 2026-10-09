import io
import json
import shutil
import subprocess

import pytest

from conftest import load_module

mkv = load_module("mkv_strip_tracks")

needs_tools = pytest.mark.skipif(
    shutil.which("mkvmerge") is None or shutil.which("ffmpeg") is None,
    reason="mkvmerge and ffmpeg are needed to build real mkv files",
)


@pytest.fixture(autouse=True)
def notifications(monkeypatch):
    sent = []
    monkeypatch.setattr(mkv, "notify", lambda title, body: sent.append(body))
    return sent


def answer(monkeypatch, *lines):
    monkeypatch.setattr("sys.stdin", io.StringIO("".join(f"{line}\n" for line in lines)))


def make_mkv(path, audio, subtitles):
    subtitle_file = path.with_suffix(".srt")
    subtitle_file.write_text("1\n00:00:00,000 --> 00:00:01,000\nhi\n")
    command = ["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "color=c=black:s=32x32:d=1"]
    for _ in audio:
        command += ["-f", "lavfi", "-i", "sine=d=1"]
    for _ in subtitles:
        command += ["-i", str(subtitle_file)]
    for index in range(1 + len(audio) + len(subtitles)):
        command += ["-map", str(index)]
    command += ["-c:v", "libx264", "-c:a", "aac", "-c:s", "srt"]
    for kind, streams in (("a", audio), ("s", subtitles)):
        for index, stream in enumerate(streams):
            language, _, title = stream.partition(":")
            command += [f"-metadata:s:{kind}:{index}", f"language={language}"]
            if title:
                command += [f"-metadata:s:{kind}:{index}", f"title={title}"]
    subprocess.run([*command, str(path)], check=True)
    subtitle_file.unlink()
    return path


def tracks_in(path):
    identified = json.loads(subprocess.run(["mkvmerge", "-J", str(path)], capture_output=True, text=True, check=True).stdout)
    return [
        (track["type"], track["properties"].get("language"), track["properties"].get("track_name", ""))
        for track in identified["tracks"]
        if track["type"] != "video"
    ]


@needs_tools
def test_keeps_only_the_picked_tracks(tmp_path, monkeypatch, capsys):
    movie = make_mkv(tmp_path / "a.mkv", audio=["eng", "jpn"], subtitles=["eng", "rus"])
    answer(monkeypatch, "1 3", "y")

    code = mkv.main([str(tmp_path)])

    out = capsys.readouterr().out
    assert code == 0
    assert "done - 1 files stripped" in out
    assert tracks_in(movie) == [("audio", "eng", ""), ("subtitles", "eng", "")]
    assert [path.name for path in tmp_path.iterdir()] == ["a.mkv"]


@needs_tools
def test_a_kind_you_did_not_pick_stays_untouched(tmp_path, monkeypatch):
    movie = make_mkv(tmp_path / "a.mkv", audio=["eng", "jpn"], subtitles=["eng", "rus"])
    answer(monkeypatch, "1", "y")

    mkv.main([str(tmp_path)])

    assert tracks_in(movie) == [("audio", "eng", ""), ("subtitles", "eng", ""), ("subtitles", "rus", "")]


@needs_tools
def test_answering_none_for_a_missing_language_removes_that_kind(tmp_path, monkeypatch):
    full = make_mkv(tmp_path / "a.mkv", audio=["eng", "jpn"], subtitles=["eng", "rus"])
    partial = make_mkv(tmp_path / "b.mkv", audio=["eng"], subtitles=["rus"])
    answer(monkeypatch, "1 3", "none", "y")

    mkv.main([str(tmp_path)])

    assert tracks_in(full) == [("audio", "eng", ""), ("subtitles", "eng", "")]
    assert tracks_in(partial) == [("audio", "eng", "")]


@needs_tools
def test_a_replacement_track_is_kept_for_a_missing_language(tmp_path, monkeypatch):
    make_mkv(tmp_path / "a.mkv", audio=["eng", "jpn"], subtitles=["eng", "rus"])
    partial = make_mkv(tmp_path / "b.mkv", audio=["eng", "jpn"], subtitles=["rus", "spa"])
    answer(monkeypatch, "1 3", "1", "y")

    mkv.main([str(tmp_path)])

    assert tracks_in(partial) == [("audio", "eng", ""), ("subtitles", "rus", "")]


@needs_tools
def test_two_tracks_in_one_language_ask_which_to_keep(tmp_path, monkeypatch):
    movie = make_mkv(tmp_path / "a.mkv", audio=["eng:Main", "eng:Commentary", "jpn"], subtitles=[])
    answer(monkeypatch, "1", "1", "y")

    mkv.main([str(tmp_path)])

    assert tracks_in(movie) == [("audio", "eng", "Main")]


@needs_tools
def test_a_file_that_already_has_only_the_picked_tracks_is_not_remuxed(tmp_path, monkeypatch, capsys):
    movie = make_mkv(tmp_path / "a.mkv", audio=["eng"], subtitles=["eng"])
    before = movie.stat().st_mtime_ns
    answer(monkeypatch, "all")

    code = mkv.main([str(tmp_path)])

    assert code == 0
    assert "nothing to strip" in capsys.readouterr().out
    assert movie.stat().st_mtime_ns == before


@needs_tools
def test_declining_changes_nothing(tmp_path, monkeypatch, capsys):
    movie = make_mkv(tmp_path / "a.mkv", audio=["eng", "jpn"], subtitles=[])
    answer(monkeypatch, "1", "n")

    code = mkv.main([str(tmp_path)])

    assert code == 1
    assert "cancelled" in capsys.readouterr().out
    assert len(tracks_in(movie)) == 2


@needs_tools
def test_an_unreadable_file_is_reported_and_the_rest_are_stripped(tmp_path, monkeypatch, capsys):
    movie = make_mkv(tmp_path / "a.mkv", audio=["eng", "jpn"], subtitles=[])
    (tmp_path / "broken.mkv").write_text("not a video")
    answer(monkeypatch, "1", "y")

    code = mkv.main([str(tmp_path)])

    out = capsys.readouterr().out
    assert code == 0
    assert "unreadable" in out
    assert "not a recognized media file" in out
    assert tracks_in(movie) == [("audio", "eng", "")]
    assert (tmp_path / "broken.mkv").read_text() == "not a video"


@needs_tools
def test_mkvmerge_warnings_still_replace_the_file(tmp_path):
    movie = make_mkv(tmp_path / "a.mkv", audio=["eng", "jpn"], subtitles=[])
    missing_track = mkv.Track(mkv.AUDIO, 9, "eng", "en", "", "A_AAC")

    ok, _ = mkv.strip_one(mkv.FilePlan(movie, (missing_track,), ()), "mkvmerge")

    assert ok
    assert [path.name for path in tmp_path.iterdir()] == ["a.mkv"]


@needs_tools
def test_a_file_mkvmerge_cannot_open_shows_its_reason(tmp_path):
    scan = mkv.probe(tmp_path / "gone.mkv", "mkvmerge")

    assert "could not be opened for reading" in scan.error


@needs_tools
def test_a_mkvmerge_error_shows_its_message_and_keeps_the_original(tmp_path):
    broken = tmp_path / "a.mkv"
    broken.write_text("not a video")

    ok, detail = mkv.strip_one(mkv.FilePlan(broken, (), ()), "mkvmerge")

    assert not ok
    assert detail.startswith("Error:")
    assert broken.read_text() == "not a video"
    assert [path.name for path in tmp_path.iterdir()] == ["a.mkv"]


def test_ctrl_c_during_a_mux_removes_the_half_written_file(tmp_path, monkeypatch):
    source = tmp_path / "a.mkv"
    source.write_text("original")
    killed = []

    class Interrupted:
        def __init__(self, command, **kwargs):
            (tmp_path / "a.stripping.mkv").write_text("half")

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        @property
        def stdout(self):
            raise KeyboardInterrupt

        def kill(self):
            killed.append(True)

        def wait(self):
            return -2

    monkeypatch.setattr(mkv.subprocess, "Popen", Interrupted)

    with pytest.raises(KeyboardInterrupt):
        mkv.strip_one(mkv.FilePlan(source, (), ()), "mkvmerge")

    assert killed == [True]
    assert [path.name for path in tmp_path.iterdir()] == ["a.mkv"]
    assert source.read_text() == "original"


def identify(*tracks):
    entries = [{"id": index, "type": kind, "properties": properties} for index, (kind, properties) in enumerate(tracks)]
    return json.dumps({"container": {"recognized": True}, "errors": [], "tracks": entries})


def test_a_language_with_and_without_its_ietf_tag_is_one_choice():
    tagged = mkv.FileScan(None, mkv.parse_tracks(identify(("audio", {"language": "rus", "language_ietf": "ru"}))))
    untagged = mkv.FileScan(None, mkv.parse_tracks(identify(("audio", {"language": "rus"}))))

    union = mkv.union_of([tagged, untagged])

    assert union == [mkv.Selection(mkv.AUDIO, "rus")]
    assert mkv.presence_of(union[0], [tagged, untagged]) == 2


def test_only_supported_subtitle_languages_are_offered():
    scan = mkv.FileScan(
        None,
        mkv.parse_tracks(
            identify(
                ("video", {}),
                ("audio", {"language": "fre"}),
                ("subtitles", {"language": "eng", "language_ietf": "en"}),
                ("subtitles", {"language": "fre", "language_ietf": "fr"}),
            )
        ),
    )

    assert mkv.union_of([scan]) == [mkv.Selection(mkv.AUDIO, "fre"), mkv.Selection(mkv.SUBTITLES, "eng")]


def test_a_track_without_a_language_counts_as_undetermined():
    (track,) = mkv.parse_tracks(identify(("audio", {})))

    assert track.language == "und"


def test_progress_is_read_from_carriage_return_updates():
    seen = []

    messages = mkv.read_progress(iter(["mkvmerge v102.0\n", "Progress: 40%\rProgress: 100%\rDone.\n"]), seen.append)

    assert seen == [40, 100]
    assert messages == ["mkvmerge v102.0", "Done."]


@pytest.mark.parametrize(
    ("messages", "expected"),
    [
        (["mkvmerge v102.0", "Error: no space left", "Multiplexing took 1 second."], "Error: no space left"),
        (["mkvmerge v102.0", "something went wrong"], "something went wrong"),
        ([], "mkvmerge exited 2"),
    ],
)
def test_failure_reason(messages, expected):
    assert mkv.failure_reason(messages, 2) == expected


def test_missing_mkvmerge_is_reported(tmp_path, monkeypatch, capsys):
    (tmp_path / "a.mkv").write_text("x")
    monkeypatch.setattr(mkv.shutil, "which", lambda name: None)

    code = mkv.main([str(tmp_path)])

    assert code == 1
    assert "mkvmerge not found" in capsys.readouterr().out


@pytest.mark.parametrize(
    ("names", "message"),
    [
        ((), "no .mkv files"),
        (("a.mp4",), "no .mkv files"),
    ],
)
def test_nothing_to_work_with_is_an_error(tmp_path, capsys, names, message):
    for name in names:
        (tmp_path / name).write_text("x")

    code = mkv.main([str(tmp_path)])

    assert code == 1
    assert message in capsys.readouterr().out


def test_a_missing_directory_is_an_error(tmp_path, capsys):
    code = mkv.main([str(tmp_path / "nope")])

    assert code == 1
    assert "not a directory" in capsys.readouterr().out


@needs_tools
def test_the_result_lists_every_file_with_a_total(tmp_path, monkeypatch, capsys, notifications):
    make_mkv(tmp_path / "a.mkv", audio=["eng", "jpn"], subtitles=[])
    make_mkv(tmp_path / "b.mkv", audio=["eng", "jpn"], subtitles=[])
    answer(monkeypatch, "1", "y")

    mkv.main([str(tmp_path)])

    first_cells = [line.strip("│ ").split(" ")[0] for line in capsys.readouterr().out.splitlines()]
    assert {"a.mkv", "b.mkv", "total"} <= set(first_cells)
    assert len(notifications) == 1
    assert notifications[0].startswith("done - 2 files stripped, saved ")


def test_sizes_format_in_binary_units():
    assert mkv.format_size(512) == "512 B"
    assert mkv.format_size(3 * 1024**2) == "3.00 MiB"
    assert mkv.format_size(-2 * 1024**3) == "-2.00 GiB"


def test_the_result_table_marks_a_failed_file(capsys):
    results = [
        mkv.StripResult(mkv.Path("a.mkv"), 3 * 1024**2, 1024**2),
        mkv.StripResult(mkv.Path("b.mkv"), 1024**2, 1024**2, "disk full"),
    ]

    mkv.console.print(mkv.build_result_table(results))

    rows = [" ".join(line.split()) for line in capsys.readouterr().out.splitlines()]
    assert "a.mkv 3.00 MiB 1.00 MiB 2.00 MiB" in rows
    assert "b.mkv 1.00 MiB failed" in rows
    assert "total 4.00 MiB 2.00 MiB 2.00 MiB" in rows
