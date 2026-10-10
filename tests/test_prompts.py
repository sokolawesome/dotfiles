import io

import pytest
from prompt_toolkit.application import create_app_session
from prompt_toolkit.input import create_pipe_input
from prompt_toolkit.output import DummyOutput

import _prompts
from _prompts import Option, Picker

DOWN = "\x1b[B"
UP = "\x1b[A"
ENTER = "\r"
SPACE = " "
CTRL_C = "\x03"

OPTIONS = [
    Option("a", ("audio", "jpn")),
    Option("b", ("audio", "eng")),
    Option("c", ("subtitles", "eng")),
]


def press(keys, picker):
    with create_pipe_input() as pipe:
        pipe.send_text(keys)
        with create_app_session(input=pipe, output=DummyOutput()):
            return picker.run()


def answer(monkeypatch, *lines):
    monkeypatch.setattr(
        "sys.stdin", io.StringIO("".join(f"{line}\n" for line in lines))
    )


def checkbox(checked=(), required=False):
    return Picker("pick", OPTIONS, set(checked), multiple=True, required=required)


def select(default=0):
    return Picker("pick", OPTIONS, {default}, multiple=False, required=True)


def test_rows_line_up_in_columns():
    assert _prompts.aligned_rows(OPTIONS) == [
        "audio      jpn",
        "audio      eng",
        "subtitles  eng",
    ]


@pytest.mark.parametrize(
    ("count", "summary"),
    [
        (0, "none"),
        (2, "audio jpn, audio eng"),
        (5, "audio jpn, audio eng, subtitles eng and 2 more"),
    ],
)
def test_the_summary_names_three_picks_at_most(count, summary):
    assert _prompts.summary_of((OPTIONS * 2)[:count]) == summary


def test_space_ticks_the_row_under_the_cursor():
    assert press(SPACE + DOWN + DOWN + SPACE + ENTER, checkbox()) == [0, 2]


def test_space_unticks_a_ticked_row():
    assert press(DOWN + SPACE + ENTER, checkbox(checked={0, 1})) == [0]


def test_a_ticks_everything_then_nothing():
    assert press("a" + ENTER, checkbox()) == [0, 1, 2]
    assert press("aa" + ENTER, checkbox()) == []


def test_enter_with_nothing_ticked_waits_when_an_answer_is_required():
    assert press(ENTER + SPACE + ENTER, checkbox(required=True)) == [0]


def test_select_starts_on_the_default_and_wraps_around():
    assert press(ENTER, select(default=1)) == [1]
    assert press(UP + ENTER, select()) == [2]
    assert press("j" + ENTER, select()) == [1]


def test_ctrl_c_cancels():
    with pytest.raises(KeyboardInterrupt):
        press(CTRL_C, checkbox())


def test_typed_picks_take_numbers(monkeypatch):
    answer(monkeypatch, "3 1")

    assert _prompts.choose_many("pick", OPTIONS) == ["c", "a"]


@pytest.mark.parametrize(
    ("typed", "picked"), [("all", ["a", "b", "c"]), ("none", []), ("", ["b"])]
)
def test_typed_picks_take_words_and_default_to_the_ticked_rows(
    monkeypatch, typed, picked
):
    answer(monkeypatch, typed)

    assert _prompts.choose_many("pick", OPTIONS, checked=["b"]) == picked


def test_typed_picks_refuse_none_when_an_answer_is_required(monkeypatch, capsys):
    answer(monkeypatch, "none", "9", "2")

    assert _prompts.choose_many("pick", OPTIONS, required=True) == ["b"]
    assert capsys.readouterr().out.count("pick numbers between 1 and 3, or 'all'") == 2


@pytest.mark.parametrize(
    ("typed", "picked"), [("2", "b"), ("audio eng", "b"), ("s", "c"), ("", "a")]
)
def test_typed_choice_takes_a_number_a_name_or_a_unique_start(
    monkeypatch, typed, picked
):
    answer(monkeypatch, typed)

    assert _prompts.choose_one("pick", OPTIONS) == picked


def test_typed_choice_asks_again_for_an_ambiguous_start(monkeypatch, capsys):
    answer(monkeypatch, "audio", "1")

    assert _prompts.choose_one("pick", OPTIONS) == "a"
    assert "pick audio jpn, audio eng or subtitles eng" in capsys.readouterr().out


def test_typed_text_asks_until_the_check_passes(monkeypatch, capsys):
    answer(monkeypatch, "", "x", "42")

    answer_text = _prompts.ask_text(
        "year", check=lambda text: None if text.isdigit() else "digits only"
    )

    out = capsys.readouterr().out
    assert answer_text == "42"
    assert "an answer is required" in out
    assert "digits only" in out
