import json
import shutil
import subprocess

import pytest

needs_tools = pytest.mark.skipif(
    shutil.which("mkvmerge") is None or shutil.which("ffmpeg") is None,
    reason="mkvmerge and ffmpeg are needed to build real mkv files",
)


def make_mkv(path, audio, subtitles):
    subtitle_file = path.with_suffix(".srt")
    subtitle_file.write_text("1\n00:00:00,000 --> 00:00:01,000\nhi\n")
    command = [
        "ffmpeg",
        "-v",
        "error",
        "-f",
        "lavfi",
        "-i",
        "color=c=black:s=32x32:d=1",
    ]
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
    identified = json.loads(
        subprocess.run(
            ["mkvmerge", "-J", str(path)], capture_output=True, text=True, check=True
        ).stdout
    )
    return [
        (
            track["type"],
            track["properties"].get("language"),
            track["properties"].get("track_name", ""),
        )
        for track in identified["tracks"]
        if track["type"] != "video"
    ]
