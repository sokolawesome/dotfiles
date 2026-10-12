import pytest

from conftest import answer, load_module
from mkv_files import make_mkv, needs_tools

mkv = load_module("mkv_extract_tracks")


@pytest.fixture(autouse=True)
def notifications(monkeypatch):
    sent = []
    monkeypatch.setattr(mkv, "notify", lambda title, body: sent.append(body))
    return sent


def names_in(directory):
    return sorted(path.name for path in directory.iterdir())


def track(kind="subtitles", track_id=3, language="rus", name="", codec="S_TEXT/ASS"):
    return mkv.Track(kind, track_id, language, language, name, codec)


@needs_tools
def test_extracts_picked_tracks_next_to_the_mkv(
    tmp_path, monkeypatch, capsys, notifications
):
    make_mkv(
        tmp_path / "Show 01.mkv",
        audio=["rus:AniLibria", "jpn"],
        subtitles=["rus:Crunchyroll", "eng"],
    )
    answer(monkeypatch, "1 3", "", "y")

    code = mkv.main([str(tmp_path)])

    assert code == 0
    assert names_in(tmp_path) == [
        "Show 01.mkv",
        "Show 01.rus.AniLibria.aac",
        "Show 01.rus.Crunchyroll.srt",
    ]
    assert (tmp_path / "Show 01.rus.Crunchyroll.srt").read_text().strip().endswith("hi")
    assert "done - 2 tracks extracted" in capsys.readouterr().out
    assert notifications[0].startswith("done - 2 tracks extracted, wrote ")


@needs_tools
def test_the_mkv_stays_untouched(tmp_path, monkeypatch):
    movie = make_mkv(tmp_path / "a.mkv", audio=["eng"], subtitles=["eng"])
    before = movie.read_bytes()
    answer(monkeypatch, "all", "", "y")

    mkv.main([str(tmp_path)])

    assert movie.read_bytes() == before
    assert names_in(tmp_path) == ["a.eng.aac", "a.eng.srt", "a.mkv"]


@needs_tools
def test_existing_files_can_be_skipped(tmp_path, monkeypatch, capsys):
    make_mkv(tmp_path / "a.mkv", audio=["eng"], subtitles=["eng"])
    (tmp_path / "a.eng.srt").write_text("mine")
    answer(monkeypatch, "all", "", "1", "y")

    code = mkv.main([str(tmp_path)])

    assert code == 0
    assert "already there" in capsys.readouterr().out
    assert (tmp_path / "a.eng.srt").read_text() == "mine"
    assert names_in(tmp_path) == ["a.eng.aac", "a.eng.srt", "a.mkv"]


@needs_tools
def test_existing_files_can_be_overwritten(tmp_path, monkeypatch):
    make_mkv(tmp_path / "a.mkv", audio=[], subtitles=["eng"])
    (tmp_path / "a.eng.srt").write_text("mine")
    answer(monkeypatch, "1", "", "2", "y")

    mkv.main([str(tmp_path)])

    assert (tmp_path / "a.eng.srt").read_text() != "mine"


@needs_tools
def test_cancelling_on_existing_files_writes_nothing(tmp_path, monkeypatch, capsys):
    make_mkv(tmp_path / "a.mkv", audio=["eng"], subtitles=["eng"])
    (tmp_path / "a.eng.srt").write_text("mine")
    answer(monkeypatch, "all", "", "3")

    code = mkv.main([str(tmp_path)])

    assert code == 1
    assert "cancelled" in capsys.readouterr().out
    assert names_in(tmp_path) == ["a.eng.srt", "a.mkv"]


@needs_tools
def test_skipping_every_track_has_nothing_to_extract(tmp_path, monkeypatch, capsys):
    make_mkv(tmp_path / "a.mkv", audio=[], subtitles=["eng"])
    (tmp_path / "a.eng.srt").write_text("mine")
    answer(monkeypatch, "1", "", "1")

    code = mkv.main([str(tmp_path)])

    assert code == 0
    assert "nothing to extract" in capsys.readouterr().out


@needs_tools
def test_two_unnamed_tracks_in_one_language_get_their_ids(tmp_path, monkeypatch):
    make_mkv(tmp_path / "a.mkv", audio=["rus", "rus"], subtitles=[])
    answer(monkeypatch, "1", "", "y")

    mkv.main([str(tmp_path)])

    assert names_in(tmp_path) == ["a.mkv", "a.rus.1.aac", "a.rus.2.aac"]


@needs_tools
def test_a_renamed_track_is_named_the_same_in_every_file(tmp_path, monkeypatch):
    make_mkv(tmp_path / "a.mkv", audio=[], subtitles=["rus:Full"])
    make_mkv(tmp_path / "b.mkv", audio=[], subtitles=["rus:Full"])
    answer(monkeypatch, "1", "1", "AniLibria", "y")

    mkv.main([str(tmp_path)])

    assert names_in(tmp_path) == [
        "a.mkv",
        "a.rus.AniLibria.srt",
        "b.mkv",
        "b.rus.AniLibria.srt",
    ]


@needs_tools
def test_an_unnamed_track_can_get_a_name(tmp_path, monkeypatch):
    make_mkv(tmp_path / "a.mkv", audio=[], subtitles=["eng"])
    answer(monkeypatch, "1", "1", "Signs", "y")

    mkv.main([str(tmp_path)])

    assert names_in(tmp_path) == ["a.eng.Signs.srt", "a.mkv"]


@needs_tools
def test_a_new_name_with_a_slash_is_asked_again(tmp_path, monkeypatch, capsys):
    make_mkv(tmp_path / "a.mkv", audio=[], subtitles=["eng"])
    answer(monkeypatch, "1", "1", "Dub/Sub", "Signs", "y")

    mkv.main([str(tmp_path)])

    assert "can't contain '/'" in capsys.readouterr().out
    assert names_in(tmp_path) == ["a.eng.Signs.srt", "a.mkv"]


@needs_tools
def test_declining_writes_nothing(tmp_path, monkeypatch, capsys):
    make_mkv(tmp_path / "a.mkv", audio=["eng"], subtitles=[])
    answer(monkeypatch, "1", "", "n")

    code = mkv.main([str(tmp_path)])

    assert code == 1
    assert "cancelled" in capsys.readouterr().out
    assert names_in(tmp_path) == ["a.mkv"]


@needs_tools
def test_a_mkvextract_error_leaves_no_files_behind(tmp_path):
    broken = tmp_path / "a.mkv"
    broken.write_text("not a video")
    plan = mkv.FilePlan(broken, (mkv.Output(track(), tmp_path / "a.rus.ass"),))

    result = mkv.extract_one(plan, "mkvextract")

    assert result.error
    assert names_in(tmp_path) == ["a.mkv"]


def test_ctrl_c_during_extraction_removes_the_half_written_files(tmp_path, monkeypatch):
    movie = tmp_path / "a.mkv"
    movie.write_text("original")
    plan = mkv.FilePlan(movie, (mkv.Output(track(), tmp_path / "a.rus.ass"),))

    class Interrupted:
        def __init__(self, command, **kwargs):
            (plan.temp_dir / "a.rus.ass").write_text("half")

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        @property
        def stdout(self):
            raise KeyboardInterrupt

        def kill(self):
            pass

        def wait(self):
            return -2

    monkeypatch.setattr("subprocess.Popen", Interrupted)

    with pytest.raises(KeyboardInterrupt):
        mkv.extract_one(plan, "mkvextract")

    assert names_in(tmp_path) == ["a.mkv"]


@pytest.mark.parametrize(
    ("codec", "extension"),
    [
        ("A_AAC/MPEG4/LC", "aac"),
        ("A_EAC3", "eac3"),
        ("A_OPUS", "opus"),
        ("S_TEXT/UTF8", "srt"),
        ("S_TEXT/ASS", "ass"),
        ("S_HDMV/PGS", "sup"),
        ("V_UNKNOWN", "bin"),
    ],
)
def test_the_extension_follows_the_codec(codec, extension):
    assert mkv.extension_for(codec) == extension


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("AniLibria", "Show.rus.AniLibria.ass"),
        ("", "Show.rus.ass"),
        ("Dub/Sub", "Show.rus.Dub-Sub.ass"),
    ],
)
def test_the_output_name(name, expected):
    (output,) = mkv.outputs_for(mkv.Path("Show.mkv"), [track(name=name)], {})

    assert output.path.name == expected


def test_dots_in_the_mkv_name_survive():
    (output,) = mkv.outputs_for(mkv.Path("Show.S01E01.mkv"), [track(name="Group")], {})

    assert output.path.name == "Show.S01E01.rus.Group.ass"


def test_a_new_name_replaces_the_track_name():
    original = track(name="Full")

    (output,) = mkv.outputs_for(
        mkv.Path("Show.mkv"), [original], {mkv.key_of(original): "AniLibria"}
    )

    assert output.path.name == "Show.rus.AniLibria.ass"


def test_missing_mkvextract_is_reported(tmp_path, monkeypatch, capsys):
    (tmp_path / "a.mkv").write_text("x")
    monkeypatch.setattr(
        "shutil.which", lambda name: None if name == "mkvextract" else name
    )

    code = mkv.main([str(tmp_path)])

    assert code == 1
    assert "mkvextract not found" in capsys.readouterr().out


def test_the_result_table_marks_a_failed_file(tmp_path, capsys):
    written = tmp_path / "a.rus.ass"
    written.write_bytes(b"x" * 1024**2)
    results = [
        mkv.ExtractResult(tmp_path / "a.mkv", (written,)),
        mkv.ExtractResult(tmp_path / "b.mkv", (), "disk full"),
    ]

    mkv.console.print(mkv.build_result_table(results))

    rows = [" ".join(line.split()) for line in capsys.readouterr().out.splitlines()]
    assert "a.mkv 1 1.00 MiB" in rows
    assert "b.mkv failed" in rows
    assert "total 1 1.00 MiB" in rows
