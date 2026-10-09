import _common
import pytest


def test_plural_switches_on_count():
    assert _common.plural(1, "file") == "1 file"
    assert _common.plural(0, "file") == "0 files"
    assert _common.plural(4, "file") == "4 files"


@pytest.mark.parametrize("interruption", [KeyboardInterrupt, EOFError])
def test_run_cli_exits_130_when_interrupted(interruption, capsys):
    def interrupted():
        raise interruption

    with pytest.raises(SystemExit) as exit_info:
        _common.run_cli(interrupted)

    assert exit_info.value.code == 130
    assert "cancelled" in capsys.readouterr().out


def test_run_cli_passes_the_exit_code_through():
    with pytest.raises(SystemExit) as exit_info:
        _common.run_cli(lambda: 3)

    assert exit_info.value.code == 3
