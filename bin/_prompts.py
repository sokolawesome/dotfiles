"""Arrow key pickers on a terminal, typed answers when stdin is not a terminal."""

import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from prompt_toolkit import Application, prompt
from prompt_toolkit.completion import FuzzyCompleter, WordCompleter
from prompt_toolkit.data_structures import Point
from prompt_toolkit.document import Document
from prompt_toolkit.formatted_text import StyleAndTextTuples
from prompt_toolkit.key_binding import KeyBindings, KeyPressEvent
from prompt_toolkit.layout import HSplit, Layout, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.styles import Style
from prompt_toolkit.validation import ValidationError, Validator
from rich.markup import escape
from rich.prompt import Confirm, Prompt
from rich.table import Table

from _common import console, plain_table, show_panel

VISIBLE_ROWS = 15
SUMMARY_ROWS = 3
POINTER = "❯ "
NO_POINTER = "  "
CHECKED = "◉ "
UNCHECKED = "○ "

STYLE = Style.from_dict(
    {
        "question": "bold ansicyan",
        "pointer": "bold ansicyan",
        "checked": "ansigreen",
        "current": "bold",
        "hint": "ansibrightblack",
        "help": "ansibrightblack",
        "warning": "ansiyellow",
    }
)

MULTIPLE_HELP = "↑↓ move · space toggle · a all · enter confirm"
SINGLE_HELP = "↑↓ move · enter select"
REQUIRED_WARNING = "pick at least one"
REQUIRED_ANSWER = "an answer is required"


@dataclass(frozen=True)
class Option[T]:
    value: T
    columns: tuple[str, ...]
    hint: str = ""

    @property
    def text(self) -> str:
        return " ".join(column for column in self.columns if column)


def interactive() -> bool:
    return sys.stdin.isatty() and sys.stdout.isatty()


def aligned_rows[T](options: Sequence[Option[T]]) -> list[str]:
    widths = [
        max(len(column) for column in group)
        for group in zip(*(option.columns for option in options))
    ]
    return [
        "  ".join(column.ljust(width) for column, width in zip(option.columns, widths))
        for option in options
    ]


class Picker[T]:
    def __init__(
        self,
        title: str,
        options: Sequence[Option[T]],
        checked: set[int],
        multiple: bool,
        required: bool,
    ):
        self.title = title
        self.options = options
        self.rows = aligned_rows(options)
        self.checked = checked
        self.multiple = multiple
        self.required = required
        self.cursor = min(checked) if checked and not multiple else 0
        self.warning = ""

    def list_fragments(self) -> StyleAndTextTuples:
        fragments: StyleAndTextTuples = []
        for index, (option, row) in enumerate(zip(self.options, self.rows)):
            current = index == self.cursor
            fragments.append(("class:pointer", POINTER if current else NO_POINTER))
            if self.multiple:
                ticked = index in self.checked
                fragments.append(
                    (
                        "class:checked" if ticked else "",
                        CHECKED if ticked else UNCHECKED,
                    )
                )
            fragments.append(("class:current" if current else "", row))
            if option.hint:
                fragments.append(("class:hint", f"  {option.hint}"))
            fragments.append(("", "\n"))
        return fragments[:-1]

    def footer_fragments(self) -> StyleAndTextTuples:
        if self.warning:
            return [("class:warning", self.warning)]
        footer = MULTIPLE_HELP if self.multiple else SINGLE_HELP
        if len(self.options) > VISIBLE_ROWS:
            footer += f" · {self.cursor + 1}/{len(self.options)}"
        return [("class:help", footer)]

    def move(self, step: int) -> None:
        self.cursor = (self.cursor + step) % len(self.options)
        self.warning = ""

    def toggle(self) -> None:
        self.checked ^= {self.cursor}
        self.warning = ""

    def toggle_all(self) -> None:
        everything = set(range(len(self.options)))
        self.checked = set() if self.checked == everything else everything
        self.warning = ""

    def picked(self) -> list[int] | None:
        if not self.multiple:
            return [self.cursor]
        if self.required and not self.checked:
            self.warning = REQUIRED_WARNING
            return None
        return sorted(self.checked)

    def key_bindings(self) -> KeyBindings:
        bindings = KeyBindings()

        @bindings.add("up")
        @bindings.add("k")
        def _(event: KeyPressEvent) -> None:
            self.move(-1)

        @bindings.add("down")
        @bindings.add("j")
        def _(event: KeyPressEvent) -> None:
            self.move(1)

        @bindings.add("c-c")
        def _(event: KeyPressEvent) -> None:
            event.app.exit(exception=KeyboardInterrupt())

        @bindings.add("enter")
        def _(event: KeyPressEvent) -> None:
            picked = self.picked()
            if picked is not None:
                event.app.exit(result=picked)

        if self.multiple:

            @bindings.add("space")
            def _(event: KeyPressEvent) -> None:
                self.toggle()

            @bindings.add("a")
            def _(event: KeyPressEvent) -> None:
                self.toggle_all()

        return bindings

    def run(self) -> list[int]:
        rows = FormattedTextControl(
            self.list_fragments,
            focusable=True,
            show_cursor=False,
            get_cursor_position=lambda: Point(0, self.cursor),
        )
        layout = Layout(
            HSplit(
                [
                    Window(
                        FormattedTextControl([("class:question", self.title)]), height=1
                    ),
                    Window(rows, height=Dimension(max=VISIBLE_ROWS)),
                    Window(FormattedTextControl(self.footer_fragments), height=1),
                ]
            ),
            focused_element=rows,
        )
        application = Application(
            layout=layout,
            key_bindings=self.key_bindings(),
            style=STYLE,
            full_screen=False,
            erase_when_done=True,
        )
        return application.run()


def print_answer(title: str, answer: str) -> None:
    console.print(f"[question]{escape(title)}[/] {escape(answer)}")


def summary_of[T](picked: Sequence[Option[T]]) -> str:
    shown = ", ".join(option.text for option in picked[:SUMMARY_ROWS])
    hidden = len(picked) - SUMMARY_ROWS
    if hidden > 0:
        return f"{shown} and {hidden} more"
    return shown or "none"


def numbered_table[T](options: Sequence[Option[T]]) -> Table:
    table = plain_table()
    table.add_column(justify="right", width=4)
    for _ in options[0].columns:
        table.add_column(overflow="ellipsis")
    table.add_column(justify="right")
    for number, option in enumerate(options, start=1):
        table.add_row(
            str(number), *map(escape, option.columns), f"[dim]{escape(option.hint)}[/]"
        )
    return table


def typed_picks[T](
    options: Sequence[Option[T]], checked: set[int], required: bool
) -> list[int]:
    shortcuts = {"all": list(range(len(options))), "": sorted(checked)}
    if not required:
        shortcuts["none"] = []
    words = ", ".join(f"'{word}'" for word in shortcuts if word)
    while True:
        answer = (
            Prompt.ask(f"[question]pick[/] [dim](numbers, {words})[/]", console=console)
            .strip()
            .lower()
        )
        if answer in shortcuts:
            return shortcuts[answer]
        parts = answer.replace(",", " ").split()
        if parts and all(
            part.isdigit() and 1 <= int(part) <= len(options) for part in parts
        ):
            return [int(part) - 1 for part in parts]
        console.print(
            f"[failure]pick numbers between 1 and {len(options)}, or {words}[/]"
        )


def choose_many[T](
    title: str,
    options: Sequence[Option[T]],
    checked: Sequence[T] = (),
    required: bool = False,
    border: str = "cyan",
) -> list[T]:
    ticked = {index for index, option in enumerate(options) if option.value in checked}
    if interactive():
        picked = Picker(title, options, ticked, multiple=True, required=required).run()
        print_answer(title, summary_of([options[index] for index in picked]))
    else:
        show_panel(numbered_table(options), title, border)
        picked = typed_picks(options, ticked, required)
    return [options[index].value for index in picked]


def typed_choice[T](title: str, options: Sequence[Option[T]], default: int) -> int:
    names = [option.text for option in options]
    menu = "  ".join(
        f"[bold][{number}][/] {escape(name)}"
        for number, name in enumerate(names, start=1)
    )
    while True:
        answer = (
            Prompt.ask(
                f"[question]{escape(title)}[/]  {menu}",
                default=names[default],
                console=console,
            )
            .strip()
            .casefold()
        )
        if answer.isdigit() and 1 <= int(answer) <= len(names):
            return int(answer) - 1
        starting = [
            index
            for index, name in enumerate(names)
            if name.casefold().startswith(answer)
        ]
        exact = [index for index in starting if names[index].casefold() == answer]
        if exact or len(starting) == 1:
            return (exact or starting)[0]
        console.print(
            f"[failure]pick {escape(', '.join(names[:-1]))} or {escape(names[-1])}[/]"
        )


def choose_one[T](title: str, options: Sequence[Option[T]], default: int = 0) -> T:
    if interactive():
        [index] = Picker(title, options, {default}, multiple=False, required=True).run()
        print_answer(title, options[index].text)
    else:
        index = typed_choice(title, options, default)
    return options[index].value


class ProblemValidator(Validator):
    def __init__(self, problem: Callable[[str], str | None]):
        self.problem = problem

    def validate(self, document: Document) -> None:
        message = self.problem(document.text.strip())
        if message:
            raise ValidationError(message=message, cursor_position=len(document.text))


def ask_text(
    question: str,
    default: str = "",
    completions: Sequence[str] = (),
    check: Callable[[str], str | None] = lambda answer: None,
) -> str:
    def problem(answer: str) -> str | None:
        if not answer:
            return REQUIRED_ANSWER
        return check(answer)

    if interactive():
        completer = (
            FuzzyCompleter(WordCompleter(list(completions), sentence=True))
            if completions
            else None
        )
        return prompt(
            [("class:question", question), ("", " ")],
            default=default,
            completer=completer,
            complete_while_typing=True,
            validator=ProblemValidator(problem),
            validate_while_typing=False,
            style=STYLE,
        ).strip()

    while True:
        answer = Prompt.ask(
            f"[question]{escape(question)}[/]", default=default or None, console=console
        )
        answer = (answer or "").strip()
        message = problem(answer)
        if not message:
            return answer
        console.print(f"[failure]{escape(message)}[/]")


def confirm(question: str) -> bool:
    return Confirm.ask(
        f"[question]{escape(question)}[/]", default=False, console=console
    )
