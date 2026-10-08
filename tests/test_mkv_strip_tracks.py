import io
import json
import pathlib

import pytest
from conftest import load_module

mkv = load_module("mkv_strip_tracks")

AUDIO = mkv.AUDIO
SUBTITLES = mkv.SUBTITLES


def track(kind, track_id, language="en", name="", codec="A_AAC", alias=""):
    return mkv.Track(kind, track_id, language, alias, name, codec)


def scan(path, tracks=(), error=""):
    return mkv.FileScan(pathlib.Path(path) if path else None, tuple(tracks), error)


def payload(*tracks):
    entries = []
    for t in tracks:
        properties = {"codec_id": t.codec, "language": t.alias or t.language}
        if t.language != "und":
            properties["language_ietf"] = t.language
        if t.name:
            properties["track_name"] = t.name
        entries.append({"id": t.track_id, "type": t.kind, "properties": properties})
    return json.dumps({"tracks": entries})


def test_language_of_uses_iso_code_as_identity():
    assert mkv.language_of({"language_ietf": "en", "language": "eng"}) == ("eng", "en")


def test_language_of_uses_iso_code_when_ietf_is_absent():
    assert mkv.language_of({"language": "eng"}) == ("eng", "eng")


def test_language_of_defaults_to_und():
    assert mkv.language_of({}) == ("und", "und")


def test_track_speaks_accepts_either_form():
    assert track(AUDIO, 1, "en", alias="eng").speaks("en")
    assert track(AUDIO, 1, "en", alias="eng").speaks("eng")
    assert not track(AUDIO, 1, "en", alias="eng").speaks("jpn")


def test_parse_tracks_reads_ids_and_names():
    tracks = mkv.parse_tracks(
        payload(
            track("video", 0, codec="V_MPEG4"),
            track(AUDIO, 1, "en", alias="eng"),
            track(SUBTITLES, 5, "ja", alias="jpn", name="Signs"),
        )
    )

    assert [t.track_id for t in tracks] == [0, 1, 5]
    assert tracks[2].name == "Signs"
    assert tracks[1].language == "eng"


def test_parse_tracks_replaces_pipes_in_names():
    assert mkv.parse_tracks(payload(track(AUDIO, 1, name="a|b")))[0].name == "a/b"


def test_parse_tracks_defaults_missing_ids():
    assert mkv.parse_tracks('{"tracks": [{"type": "audio"}]}')[0].track_id == -1


def test_scan_files_finds_mkv_in_a_directory(tmp_path):
    (tmp_path / "a.mkv").write_text("x")
    (tmp_path / "b.mp4").write_text("x")
    (tmp_path / "c.mkv").write_text("x")

    found = mkv.scan_files(tmp_path)

    assert [p.name for p in found] == ["a.mkv", "c.mkv"]


def test_scan_files_ignores_nested(tmp_path):
    (tmp_path / "a.mkv").write_text("x")
    nested = tmp_path / "sub"
    nested.mkdir()
    (nested / "b.mkv").write_text("x")

    assert [p.name for p in mkv.scan_files(tmp_path)] == ["a.mkv"]


def test_scan_files_rejects_a_non_directory(tmp_path):
    with pytest.raises(mkv.StripError) as error:
        mkv.scan_files(tmp_path / "gone")

    assert "not a directory" in str(error.value)


def test_union_of_groups_by_identity():
    scans = [
        scan(None, [track(AUDIO, 1, "en"), track(AUDIO, 2, "ja")]),
        scan(None, [track(AUDIO, 1, "en"), track(SUBTITLES, 3, "en")]),
    ]

    union = mkv.union_of(scans)

    assert set(union) == {
        mkv.Selection(AUDIO, "en"),
        mkv.Selection(AUDIO, "ja"),
        mkv.Selection(SUBTITLES, "en"),
    }


def test_union_of_merges_ietf_and_iso_forms_of_one_language():
    with_ietf = mkv.parse_tracks(
        '{"tracks": [{"id": 1, "type": "audio", "properties": {"language": "rus", "language_ietf": "ru"}}]}'
    )
    without_ietf = mkv.parse_tracks(
        '{"tracks": [{"id": 1, "type": "audio", "properties": {"language": "rus"}}]}'
    )
    scans = [scan("a", with_ietf), scan("b", without_ietf)]

    union = mkv.union_of(scans)

    assert union == [mkv.Selection(AUDIO, "rus")]
    assert mkv.presence_of(union[0], scans) == 2


def test_union_of_groups_named_tracks_by_language():
    scans = [scan(None, [track(AUDIO, 1, "en"), track(AUDIO, 2, "en", "Commentary")])]

    union = mkv.union_of(scans)

    assert union == [mkv.Selection(AUDIO, "en")]
    assert mkv.labels_for(union[0], scans) == ["unnamed", "Commentary"]


def test_union_of_keeps_every_audio_language():
    scans = [scan(None, [track(AUDIO, 1, "en"), track(AUDIO, 2, "de")])]

    assert mkv.union_of(scans) == [mkv.Selection(AUDIO, "en"), mkv.Selection(AUDIO, "de")]


def test_union_of_keeps_only_supported_subtitle_languages():
    scans = [scan(None, [track(SUBTITLES, 1, "en"), track(SUBTITLES, 2, "de")])]

    assert mkv.union_of(scans) == [mkv.Selection(SUBTITLES, "en")]


def test_union_of_ignores_video():
    assert mkv.union_of([scan(None, [track("video", 0)])]) == []


def test_presence_of_counts_files():
    scans = [
        scan("a", [track(AUDIO, 1, "en")]),
        scan("b", [track(AUDIO, 2, "en")]),
        scan("c", [track(AUDIO, 3, "ja")]),
    ]

    assert mkv.presence_of(mkv.Selection(AUDIO, "en"), scans) == 2


def test_matches_for_uses_identity_not_position():
    first = scan("a", [track(AUDIO, 1, "en"), track(AUDIO, 2, "ja")])
    second = scan("b", [track(AUDIO, 1, "ja"), track(AUDIO, 2, "en")])

    picks = mkv.matches_for(mkv.Selection(AUDIO, "en"), first)
    others = mkv.matches_for(mkv.Selection(AUDIO, "en"), second)

    assert [t.track_id for t in picks] == [1]
    assert [t.track_id for t in others] == [2]


def test_matches_for_rejects_the_wrong_language_across_layouts():
    target = scan("b", [track(AUDIO, 1, "ja"), track(AUDIO, 2, "en")])

    assert [t.track_id for t in mkv.matches_for(mkv.Selection(AUDIO, "en"), target)] == [2]


def test_matches_for_ignores_track_names():
    target = scan("a", [track(AUDIO, 1, "en"), track(AUDIO, 2, "en", "Commentary")])

    matched = mkv.matches_for(mkv.Selection(AUDIO, "en"), target)

    assert [t.track_id for t in matched] == [1, 2]


def test_matches_for_returns_nothing_when_absent():
    assert mkv.matches_for(mkv.Selection(AUDIO, "jpn"), scan("a", [track(AUDIO, 1, "en")])) == []


def test_resolve_picks_keeps_a_single_candidate():
    chosen = mkv.resolve_picks([mkv.Selection(AUDIO, "en")], scan("a", [track(AUDIO, 4, "en")]), False)

    assert [t.track_id for t in chosen] == [4]


def test_resolve_picks_keeps_every_candidate_without_asking():
    target = scan("a", [track(AUDIO, 1, "en"), track(AUDIO, 2, "en")])

    chosen = mkv.resolve_picks([mkv.Selection(AUDIO, "en")], target, False)

    assert [t.track_id for t in chosen] == [1, 2]


def test_resolve_picks_keeps_each_track_once():
    target = scan("a", [track(AUDIO, 1, "ja", alias="en")])
    selections = [mkv.Selection(AUDIO, "en"), mkv.Selection(AUDIO, "ja")]

    chosen = mkv.resolve_picks(selections, target, False)

    assert [t.track_id for t in chosen] == [1]


def test_resolve_picks_asks_for_each_ambiguous_file(monkeypatch, capsys):
    asked = []

    def fake_prompt(question=""):
        asked.append(question)
        return "2"

    monkeypatch.setattr(mkv, "Prompt", type("P", (), {"ask": staticmethod(fake_prompt)}))
    scans = [
        scan("a", [track(AUDIO, 1, "en"), track(AUDIO, 5, "en")]),
        scan("b", [track(AUDIO, 2, "en"), track(AUDIO, 9, "en")]),
    ]

    chosen = [mkv.resolve_picks([mkv.Selection(AUDIO, "en")], s, True) for s in scans]
    capsys.readouterr()

    assert len(asked) == 2
    assert [t.track_id for t in chosen[0]] == [5]
    assert [t.track_id for t in chosen[1]] == [9]


def test_resolve_picks_keeps_nothing_when_the_track_is_missing():
    target = scan("a", [track(AUDIO, 1, "ja")])

    chosen = mkv.resolve_picks([mkv.Selection(AUDIO, "en")], target, False)

    assert chosen == []


def test_resolve_picks_asks_for_a_replacement_when_the_track_is_missing(monkeypatch, capsys):
    monkeypatch.setattr(mkv, "Prompt", type("P", (), {"ask": staticmethod(lambda q="": "1")}))
    target = scan("a", [track(AUDIO, 7, "ja")])

    chosen = mkv.resolve_picks([mkv.Selection(AUDIO, "en")], target, True)
    capsys.readouterr()

    assert [t.track_id for t in chosen] == [7]


def test_resolve_picks_keeps_nothing_when_the_replacement_is_declined(monkeypatch, capsys):
    monkeypatch.setattr(mkv, "Prompt", type("P", (), {"ask": staticmethod(lambda q="": "none")}))
    target = scan("a", [track(AUDIO, 7, "ja")])

    chosen = mkv.resolve_picks([mkv.Selection(AUDIO, "en")], target, True)
    capsys.readouterr()

    assert chosen == []


def test_pick_from_candidates_honours_the_number(monkeypatch, capsys):
    monkeypatch.setattr(mkv, "Prompt", type("P", (), {"ask": staticmethod(lambda q="": "2")}))
    target = scan("a", [track(AUDIO, 1, "en"), track(AUDIO, 7, "en")])
    candidates = mkv.matches_for(mkv.Selection(AUDIO, "en"), target)

    result = mkv.pick_from_candidates(mkv.Selection(AUDIO, "en"), target, candidates)
    capsys.readouterr()

    assert [t.track_id for t in result] == [7]


def test_pick_from_candidates_keeps_all_on_request(monkeypatch, capsys):
    monkeypatch.setattr(mkv, "Prompt", type("P", (), {"ask": staticmethod(lambda q="": "all")}))
    target = scan("a", [track(AUDIO, 3, "en"), track(AUDIO, 7, "en")])
    candidates = mkv.matches_for(mkv.Selection(AUDIO, "en"), target)

    result = mkv.pick_from_candidates(mkv.Selection(AUDIO, "en"), target, candidates)
    capsys.readouterr()

    assert [t.track_id for t in result] == [3, 7]


def test_pick_from_available_returns_nothing_when_the_kind_is_absent(monkeypatch):
    monkeypatch.setattr(
        mkv,
        "Prompt",
        type("P", (), {"ask": staticmethod(lambda q="": pytest.fail("must not ask"))}),
    )

    result = mkv.pick_from_available(mkv.Selection(AUDIO, "en"), scan("a", [track(SUBTITLES, 1, "en")]))

    assert result == []


def test_pick_from_available_honours_the_number(monkeypatch, capsys):
    monkeypatch.setattr(mkv, "Prompt", type("P", (), {"ask": staticmethod(lambda q="": "2")}))
    target = scan("a", [track(AUDIO, 3, "ja"), track(AUDIO, 4, "fr")])

    result = mkv.pick_from_available(mkv.Selection(AUDIO, "en"), target)
    capsys.readouterr()

    assert [t.track_id for t in result] == [4]


def test_pick_from_available_keeps_nothing_on_request(monkeypatch, capsys):
    monkeypatch.setattr(mkv, "Prompt", type("P", (), {"ask": staticmethod(lambda q="": "none")}))
    target = scan("a", [track(AUDIO, 3, "ja")])

    result = mkv.pick_from_available(mkv.Selection(AUDIO, "en"), target)
    capsys.readouterr()

    assert result == []


def test_build_plan_records_missing():
    scans = [
        scan("a", [track(AUDIO, 1, "en")]),
        scan("b", [track(AUDIO, 1, "ja")]),
    ]

    plans = mkv.build_plan(scans, [mkv.Selection(AUDIO, "en")], False)

    assert plans[0].missing == ()
    assert plans[1].missing == (mkv.Selection(AUDIO, "en"),)


def test_build_plan_resolves_each_file_independently():
    scans = [
        scan("a", [track(AUDIO, 1, "en"), track(AUDIO, 2, "ja")]),
        scan("b", [track(AUDIO, 1, "ja"), track(AUDIO, 2, "en")]),
    ]

    plans = mkv.build_plan(scans, [mkv.Selection(AUDIO, "en")], False)

    assert [p.ids_for(AUDIO) for p in plans] == [[1], [2]]


def test_plan_table_groups_files_with_the_same_tracks(tmp_path, capsys):
    plans = [
        mkv.FilePlan(tmp_path / "a.mkv", (track(AUDIO, 1, "en"),), ()),
        mkv.FilePlan(tmp_path / "b.mkv", (track(AUDIO, 1, "en"),), ()),
    ]

    mkv.console.print(mkv.build_plan_table(plans))

    out = capsys.readouterr().out
    assert "2 files" in out
    assert "audio en unnamed" in out
    assert "a.mkv" not in out


def test_plan_table_names_a_lone_file(tmp_path, capsys):
    plans = [mkv.FilePlan(tmp_path / "a.mkv", (track(AUDIO, 1, "en"),), ())]

    mkv.console.print(mkv.build_plan_table(plans))

    out = capsys.readouterr().out
    assert "a.mkv" in out
    assert "2 files" not in out


def test_plan_table_marks_missing_languages(tmp_path, capsys):
    plan = mkv.FilePlan(tmp_path / "a.mkv", (), (mkv.Selection(AUDIO, "en"),))

    mkv.console.print(mkv.build_plan_table([plan]))

    out = capsys.readouterr().out
    assert "missing" in out
    assert "aud en" in out


def test_strip_command_uses_the_right_flag_per_kind():
    plan = mkv.FilePlan(pathlib.Path("a.mkv"), (track(AUDIO, 1), track(SUBTITLES, 4)), ())

    command = mkv.strip_command(plan, "mkvmerge")

    assert "--audio-tracks" in command
    assert "--subtitle-tracks" in command
    assert "--subtitles-tracks" not in command


def test_strip_command_leaves_an_unselected_kind_untouched():
    plan = mkv.FilePlan(pathlib.Path("a.mkv"), (track(AUDIO, 1),), ())

    command = mkv.strip_command(plan, "mkvmerge")

    assert "--subtitle-tracks" not in command
    assert "--no-subtitles" not in command


def test_strip_command_has_no_flags_when_nothing_is_kept():
    plan = mkv.FilePlan(pathlib.Path("a.mkv"), (), ())

    command = mkv.strip_command(plan, "mkvmerge")

    assert "--no-audio" not in command
    assert "--no-subtitles" not in command


def fake_process(returncode=0, stdout="", stderr=""):
    class Proc:
        def __init__(self):
            self.stdout = iter([stdout])
            self.stderr = io.StringIO(stderr)

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def wait(self):
            return returncode

    return Proc()


def test_strip_one_replaces_the_original(tmp_path, monkeypatch):
    source = tmp_path / "a.mkv"
    source.write_text("original")

    def fake_popen(command, **kwargs):
        temp = [part for part in command if part.endswith(".stripping.mkv")][0]
        (tmp_path / "a.stripping.mkv").write_text("stripped")
        return fake_process(0)

    monkeypatch.setattr(mkv.subprocess, "Popen", fake_popen)

    ok, detail = mkv.strip_one(mkv.FilePlan(source, (), ()), "mkvmerge")

    assert ok
    assert source.read_text() == "stripped"
    assert list(tmp_path.iterdir()) == [source]


def test_strip_one_keeps_the_original_on_failure(tmp_path, monkeypatch):
    source = tmp_path / "a.mkv"
    source.write_text("original")

    def fake_popen(command, **kwargs):
        temp = [part for part in command if part.endswith(".stripping.mkv")][0]
        (tmp_path / "a.stripping.mkv").write_text("half")
        return fake_process(2, stderr="boom\n")

    monkeypatch.setattr(mkv.subprocess, "Popen", fake_popen)

    ok, detail = mkv.strip_one(mkv.FilePlan(source, (), ()), "mkvmerge")

    assert not ok
    assert detail == "boom"
    assert source.read_text() == "original"
    assert list(tmp_path.iterdir()) == [source]


def test_strip_one_reports_missing_output(tmp_path, monkeypatch):
    source = tmp_path / "a.mkv"
    source.write_text("original")

    monkeypatch.setattr(mkv.subprocess, "Popen", lambda command, **kwargs: fake_process(0))

    ok, detail = mkv.strip_one(mkv.FilePlan(source, (), ()), "mkvmerge")

    assert not ok
    assert "no output" in detail
    assert source.read_text() == "original"


def test_find_mkvmerge_fails_when_absent(monkeypatch):
    monkeypatch.setattr(mkv.shutil, "which", lambda name: None)

    with pytest.raises(mkv.StripError) as error:
        mkv.find_mkvmerge()

    assert "mkvmerge not found" in str(error.value)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (1073741824, "1.00 GiB"),
        (1048576, "1.00 MiB"),
        (512, "512 B"),
        (0, "0 B"),
    ],
)
def test_format_size(value, expected):
    assert mkv.format_size(value) == expected


def test_size_of_ignores_missing_files(tmp_path):
    (tmp_path / "a").write_text("12345")

    assert mkv.size_of([tmp_path / "a", tmp_path / "gone"]) == 5


def test_probe_reports_unreadable_files(tmp_path, monkeypatch):
    monkeypatch.setattr(
        mkv.subprocess,
        "run",
        lambda command, **kwargs: type("F", (), {"returncode": 1, "stdout": "", "stderr": "bad file\n"})(),
    )

    result = mkv.probe(tmp_path / "x.mkv", "mkvmerge")

    assert result.error == "bad file"
    assert not result.readable()


def test_probe_reports_bad_json(tmp_path, monkeypatch):
    monkeypatch.setattr(
        mkv.subprocess,
        "run",
        lambda command, **kwargs: type("F", (), {"returncode": 0, "stdout": "not json", "stderr": ""})(),
    )

    result = mkv.probe(tmp_path / "x.mkv", "mkvmerge")

    assert "unreadable" in result.error


def test_main_declining_changes_nothing(tmp_path, monkeypatch, capsys):
    (tmp_path / "a.mkv").write_text("x")
    monkeypatch.setattr(mkv, "find_mkvmerge", lambda: "mkvmerge")
    monkeypatch.setattr(mkv, "choose_interactively", lambda scans, union: list(union))
    monkeypatch.setattr(mkv.Confirm, "ask", lambda *args, **kwargs: False)
    monkeypatch.setattr(
        mkv.subprocess,
        "run",
        lambda command, **kwargs: type("F", (), {"returncode": 0, "stdout": payload(track(AUDIO, 1, "en")), "stderr": ""})(),
    )

    code = mkv.main([str(tmp_path)])

    out = capsys.readouterr().out
    assert code == 1
    assert "cancelled" in out
    assert (tmp_path / "a.mkv").read_text() == "x"


def test_main_reports_no_mkv_files(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(mkv, "find_mkvmerge", lambda: "mkvmerge")

    code = mkv.main([str(tmp_path)])

    assert code == 1
    assert "no .mkv files" in capsys.readouterr().out


def test_main_reports_a_missing_mkvmerge(tmp_path, monkeypatch, capsys):
    (tmp_path / "a.mkv").write_text("x")
    monkeypatch.setattr(mkv.shutil, "which", lambda name: None)

    code = mkv.main([str(tmp_path)])

    assert code == 1
    assert "mkvmerge not found" in capsys.readouterr().out


def test_main_strips_when_confirmed(tmp_path, monkeypatch, capsys):
    source = tmp_path / "a.mkv"
    source.write_text("original")
    monkeypatch.setattr(mkv, "find_mkvmerge", lambda: "mkvmerge")
    monkeypatch.setattr(mkv, "choose_interactively", lambda scans, union: list(union))
    monkeypatch.setattr(mkv, "Confirm", type("C", (), {"ask": staticmethod(lambda *a, **k: True)}))
    monkeypatch.setattr(
        mkv.subprocess,
        "run",
        lambda command, **kwargs: type("F", (), {"returncode": 0, "stdout": payload(track(AUDIO, 1, "en")), "stderr": ""})(),
    )
    calls = []

    def fake_strip(plan, mkvmerge, report=None):
        calls.append(plan.path)
        source.write_text("stripped")
        return True, ""

    monkeypatch.setattr(mkv, "strip_one", fake_strip)

    code = mkv.main([str(tmp_path)])

    assert code == 0
    assert calls == [source]
    assert source.read_text() == "stripped"
    assert "done - 1 files stripped" in capsys.readouterr().out


def test_main_keeps_a_replacement_when_a_track_is_missing(tmp_path, monkeypatch, capsys):
    (tmp_path / "a.mkv").write_text("x")
    monkeypatch.setattr(mkv, "find_mkvmerge", lambda: "mkvmerge")
    monkeypatch.setattr(mkv, "choose_interactively", lambda scans, union: [mkv.Selection(AUDIO, "en")])
    monkeypatch.setattr(mkv, "Confirm", type("C", (), {"ask": staticmethod(lambda *a, **k: True)}))
    monkeypatch.setattr(mkv, "Prompt", type("P", (), {"ask": staticmethod(lambda q="": "1")}))
    monkeypatch.setattr(
        mkv,
        "probe",
        lambda path, mkvmerge: scan(path, (track(AUDIO, 1, "ja"),)),
    )
    stripped = []

    def fake_strip(plan, mkvmerge, report=None):
        stripped.append(plan)
        return True, ""

    monkeypatch.setattr(mkv, "strip_one", fake_strip)

    code = mkv.main([str(tmp_path)])

    assert code == 0
    assert [t.language for t in stripped[0].keep] == ["ja"]


def test_main_reports_an_unreadable_file(tmp_path, monkeypatch, capsys):
    (tmp_path / "a.mkv").write_text("x")
    (tmp_path / "b.mkv").write_text("x")
    monkeypatch.setattr(mkv, "find_mkvmerge", lambda: "mkvmerge")

    def fake_probe(path, mkvmerge):
        if path.name == "a.mkv":
            return scan(path, (), "broken")
        return scan(path, (track(AUDIO, 1, "en"),))

    monkeypatch.setattr(mkv, "probe", fake_probe)
    monkeypatch.setattr(mkv, "choose_interactively", lambda scans, union: list(union))
    monkeypatch.setattr(mkv.Confirm, "ask", lambda *args, **kwargs: False)

    code = mkv.main([str(tmp_path)])

    out = capsys.readouterr().out
    assert code == 1
    assert "unreadable" in out
    assert "broken" in out


def test_main_handles_ctrl_c(monkeypatch, capsys):
    def boom():
        raise KeyboardInterrupt

    monkeypatch.setattr(mkv, "find_mkvmerge", boom)

    code = mkv.main(["."])

    assert code == 130
    assert "cancelled" in capsys.readouterr().out

def test_read_progress_parses_carriage_returns(monkeypatch):
    seen = []
    stream = iter(["Progress: 0%\rProgress: 40%\rProgress: 100%\r\n"])

    mkv.read_progress(stream, seen.append)

    assert seen == [0, 40, 100]


def test_read_progress_ignores_other_output():
    seen = []
    stream = iter(["mkvmerge v102.0\nThe file has been opened for writing.\n"])

    mkv.read_progress(stream, seen.append)

    assert seen == []


def test_strip_one_reports_progress(tmp_path, monkeypatch):
    source = tmp_path / "a.mkv"
    source.write_text("x")
    seen = []

    def fake_popen(command, **kwargs):
        (tmp_path / "a.stripping.mkv").write_text("y")
        return fake_process(0, stdout="Progress: 12%\rProgress: 88%\r")

    monkeypatch.setattr(mkv.subprocess, "Popen", fake_popen)

    ok, _ = mkv.strip_one(mkv.FilePlan(source, (), ()), "mkvmerge", seen.append)

    assert ok
    assert seen == [12, 88]


def fake_progress(made):
    class Progress:
        def __init__(self, *args, **kwargs):
            self.tasks = []
            made.append(self)

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def add_task(self, description, total=None):
            self.tasks.append(description)
            return len(self.tasks)

        def update(self, task, **kwargs):
            pass

        def remove_task(self, task):
            pass

        def advance(self, task):
            pass

    return Progress


def test_strip_all_shows_one_bar_for_a_single_file(tmp_path, monkeypatch):
    made = []
    monkeypatch.setattr(mkv, "Progress", fake_progress(made))
    monkeypatch.setattr(mkv, "strip_one", lambda plan, mkvmerge, report=None: (True, ""))
    plan = mkv.FilePlan(tmp_path / "a.mkv", (), ())

    mkv.strip_all([plan], "mkvmerge")

    assert made[0].tasks == ["a.mkv"]


def test_strip_all_shows_the_overall_bar_for_several_files(tmp_path, monkeypatch):
    made = []
    monkeypatch.setattr(mkv, "Progress", fake_progress(made))
    monkeypatch.setattr(mkv, "strip_one", lambda plan, mkvmerge, report=None: (True, ""))
    plans = [mkv.FilePlan(tmp_path / "a.mkv", (), ()), mkv.FilePlan(tmp_path / "b.mkv", (), ())]

    mkv.strip_all(plans, "mkvmerge")

    assert made[0].tasks == ["stripping", "a.mkv", "b.mkv"]


def test_line_buffered_prefixes_stdbuf(monkeypatch):
    monkeypatch.setattr(mkv.shutil, "which", lambda name: "/usr/bin/stdbuf")

    assert mkv.line_buffered(["mkvmerge", "-o", "x"])[0] == "stdbuf"


def test_line_buffered_without_stdbuf(monkeypatch):
    monkeypatch.setattr(mkv.shutil, "which", lambda name: None)

    assert mkv.line_buffered(["mkvmerge"]) == ["mkvmerge"]
