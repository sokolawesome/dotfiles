import json
from pathlib import Path

import pytest

import _mkv as mkv
from mkv_files import needs_tools


def identify(*tracks):
    entries = [
        {"id": index, "type": kind, "properties": properties}
        for index, (kind, properties) in enumerate(tracks)
    ]
    return json.dumps(
        {"container": {"recognized": True}, "errors": [], "tracks": entries}
    )


@needs_tools
def test_a_file_mkvmerge_cannot_open_shows_its_reason(tmp_path):
    scan = mkv.probe(tmp_path / "gone.mkv", "mkvmerge")

    assert "could not be opened for reading" in scan.error


def test_a_language_with_and_without_its_ietf_tag_is_one_choice():
    tagged = mkv.FileScan(
        Path("a.mkv"),
        mkv.parse_tracks(
            identify(("audio", {"language": "rus", "language_ietf": "ru"}))
        ),
    )
    untagged = mkv.FileScan(
        Path("b.mkv"), mkv.parse_tracks(identify(("audio", {"language": "rus"})))
    )

    union = mkv.union_of([tagged, untagged])

    assert union == [mkv.Selection(mkv.AUDIO, "rus")]
    assert mkv.presence_of(union[0], [tagged, untagged]) == 2


def test_only_supported_subtitle_languages_are_offered():
    scan = mkv.FileScan(
        Path("a.mkv"),
        mkv.parse_tracks(
            identify(
                ("video", {}),
                ("audio", {"language": "fre"}),
                ("subtitles", {"language": "eng", "language_ietf": "en"}),
                ("subtitles", {"language": "fre", "language_ietf": "fr"}),
            )
        ),
    )

    assert mkv.union_of([scan]) == [
        mkv.Selection(mkv.AUDIO, "fre"),
        mkv.Selection(mkv.SUBTITLES, "eng"),
    ]


def test_each_track_name_is_listed_with_its_formats():
    scans = [
        mkv.FileScan(
            Path(name),
            mkv.parse_tracks(
                identify(
                    (
                        "subtitles",
                        {"language": "rus", "track_name": "full", "codec_id": first},
                    ),
                    (
                        "subtitles",
                        {
                            "language": "rus",
                            "track_name": "forced",
                            "codec_id": "S_TEXT/ASS",
                        },
                    ),
                )
            ),
        )
        for name, first in (("a.mkv", "S_HDMV/PGS"), ("b.mkv", "S_TEXT/UTF8"))
    ]

    labels = mkv.labels_for(mkv.Selection(mkv.SUBTITLES, "rus"), scans)

    assert labels == ["full (pgs/srt)", "forced (ass)"]


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


def test_a_track_without_a_language_counts_as_undetermined():
    (track,) = mkv.parse_tracks(identify(("audio", {})))

    assert track.language == "und"


def test_progress_is_read_from_carriage_return_updates():
    seen = []

    messages = mkv.read_progress(
        iter(["mkvmerge v102.0\n", "Progress: 40%\rProgress: 100%\rDone.\n"]),
        seen.append,
    )

    assert seen == [40, 100]
    assert messages == ["mkvmerge v102.0", "Done."]


@pytest.mark.parametrize(
    ("messages", "expected"),
    [
        (
            ["mkvmerge v102.0", "Error: no space left", "Multiplexing took 1 second."],
            "Error: no space left",
        ),
        (["mkvmerge v102.0", "something went wrong"], "something went wrong"),
        ([], "mkvextract exited 2"),
    ],
)
def test_failure_reason(messages, expected):
    assert mkv.failure_reason(messages, 2, "mkvextract") == expected


def test_a_missing_tool_names_the_package(monkeypatch):
    monkeypatch.setattr(mkv.shutil, "which", lambda name: None)

    with pytest.raises(mkv.MkvError, match="mkvextract not found.*mkvtoolnix-cli"):
        mkv.find_tool("mkvextract")


def test_sizes_format_in_binary_units():
    assert mkv.format_size(512) == "512 B"
    assert mkv.format_size(3 * 1024**2) == "3.00 MiB"
    assert mkv.format_size(-2 * 1024**3) == "-2.00 GiB"
