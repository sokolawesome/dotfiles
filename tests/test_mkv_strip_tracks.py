import pytest

from conftest import answer, load_module
from mkv_files import make_mkv, needs_tools, tracks_in

mkv = load_module("mkv_strip_tracks")


@pytest.fixture(autouse=True)
def notifications(monkeypatch):
    sent = []
    monkeypatch.setattr(mkv, "notify", lambda title, body: sent.append(body))
    return sent


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

    assert tracks_in(movie) == [
        ("audio", "eng", ""),
        ("subtitles", "eng", ""),
        ("subtitles", "rus", ""),
    ]


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
    partial = make_mkv(
        tmp_path / "b.mkv", audio=["eng", "jpn"], subtitles=["rus", "spa"]
    )
    answer(monkeypatch, "1 3", "1", "y")

    mkv.main([str(tmp_path)])

    assert tracks_in(partial) == [("audio", "eng", ""), ("subtitles", "rus", "")]


@needs_tools
def test_two_tracks_in_one_language_ask_which_to_keep(tmp_path, monkeypatch):
    movie = make_mkv(
        tmp_path / "a.mkv", audio=["eng:Main", "eng:Commentary", "jpn"], subtitles=[]
    )
    answer(monkeypatch, "1", "1", "y")

    mkv.main([str(tmp_path)])

    assert tracks_in(movie) == [("audio", "eng", "Main")]


@needs_tools
def test_a_track_name_is_picked_once_for_every_file(tmp_path, monkeypatch):
    episodes = [
        make_mkv(tmp_path / f"{n}.mkv", audio=[], subtitles=["eng:Full", "eng:CC"])
        for n in (1, 2, 3)
    ]
    answer(monkeypatch, "1", "1", "y")

    mkv.main([str(tmp_path)])

    assert [tracks_in(episode) for episode in episodes] == [
        [("subtitles", "eng", "Full")]
    ] * 3


@needs_tools
def test_each_file_keeps_the_picked_name_it_has(tmp_path, monkeypatch):
    named = make_mkv(tmp_path / "a.mkv", audio=[], subtitles=["eng:Full", "eng:Signs"])
    unnamed = make_mkv(tmp_path / "b.mkv", audio=[], subtitles=["eng", "eng:Signs"])
    answer(monkeypatch, "1", "1 3", "y")

    mkv.main([str(tmp_path)])

    assert tracks_in(named) == [("subtitles", "eng", "Full")]
    assert tracks_in(unnamed) == [("subtitles", "eng", "")]


@needs_tools
def test_a_file_without_the_picked_name_asks_for_a_replacement(
    tmp_path, monkeypatch, capsys
):
    full = make_mkv(tmp_path / "a.mkv", audio=[], subtitles=["eng:Full"])
    other = make_mkv(tmp_path / "b.mkv", audio=[], subtitles=["eng:CC", "eng:Signs"])
    answer(monkeypatch, "1", "1", "1", "y")

    mkv.main([str(tmp_path)])

    assert "b.mkv: no Full in subtitles eng" in capsys.readouterr().out
    assert tracks_in(full) == [("subtitles", "eng", "Full")]
    assert tracks_in(other) == [("subtitles", "eng", "CC")]


@needs_tools
def test_answering_none_for_a_missing_name_drops_that_language(
    tmp_path, monkeypatch, capsys
):
    make_mkv(tmp_path / "a.mkv", audio=[], subtitles=["eng:Full"])
    signs_only = make_mkv(tmp_path / "b.mkv", audio=[], subtitles=["eng:Signs"])
    answer(monkeypatch, "1", "1", "none", "y")

    mkv.main([str(tmp_path)])

    assert "missing: sub eng" in capsys.readouterr().out
    assert tracks_in(signs_only) == []


@needs_tools
def test_a_file_that_already_has_only_the_picked_tracks_is_not_remuxed(
    tmp_path, monkeypatch, capsys
):
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
def test_an_unreadable_file_is_reported_and_the_rest_are_stripped(
    tmp_path, monkeypatch, capsys
):
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

    monkeypatch.setattr("subprocess.Popen", Interrupted)

    with pytest.raises(KeyboardInterrupt):
        mkv.strip_one(mkv.FilePlan(source, (), ()), "mkvmerge")

    assert killed == [True]
    assert [path.name for path in tmp_path.iterdir()] == ["a.mkv"]
    assert source.read_text() == "original"


def test_missing_mkvmerge_is_reported(tmp_path, monkeypatch, capsys):
    (tmp_path / "a.mkv").write_text("x")
    monkeypatch.setattr("shutil.which", lambda name: None)

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
def test_the_result_lists_every_file_with_a_total(
    tmp_path, monkeypatch, capsys, notifications
):
    make_mkv(tmp_path / "a.mkv", audio=["eng", "jpn"], subtitles=[])
    make_mkv(tmp_path / "b.mkv", audio=["eng", "jpn"], subtitles=[])
    answer(monkeypatch, "1", "y")

    mkv.main([str(tmp_path)])

    first_cells = [
        line.strip("│ ").split(" ")[0] for line in capsys.readouterr().out.splitlines()
    ]
    assert {"a.mkv", "b.mkv", "total"} <= set(first_cells)
    assert len(notifications) == 1
    assert notifications[0].startswith("done - 2 files stripped, saved ")


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
