# AGENTS.md

Personal dotfiles for Arch Linux with Hyprland, and for macOS with AeroSpace. `bin/manage_df` links each top-level directory into place with GNU stow.

- `config/` goes to `~/.config`.
- `home/` goes to `~`.
- `bin/` goes to `~/.local/bin`. It holds the Python CLI tools that the rules below are about.
- `homelab/` holds the qBittorrent on-finish hook.
- `agents/` and `claude/` go to `~/.agents` and `~/.claude`.
- `other/` holds the package, group and service lists that `bin/backup_system_state` writes.

## Checks
You **must** run all four from the repo root before you finish. They must pass with 0 errors:

```fish
ruff check .
ruff format --check .
ty check
python -m pytest -q
```

- Run `ruff format .` to fix formatting.
- ty reads `ty.toml`. Zed runs the same ty as its Python language server.
- You **must** fix a type error in the code. Never silence it with `# ty: ignore`, `# type: ignore`, `cast` or a config change.

## Scripts
- Put a script in `bin/<snake_case_name>`, with no extension, `#!/usr/bin/env python3`, the executable bit and a one-line module docstring.
- You **must** add every new script to `include` in `ty.toml`. ty skips files without `.py` unless they are listed there, and it does not warn. Ruff picks them up through `extend-include` in `ruff.toml`.
- Put code shared by several scripts in `bin/_<name>.py`.
- Use `_common.py` for output and `_prompts.py` for every question to the user. Do not add a second way to print or prompt.
- Follow the existing script shape: `build_parser()` with `RichHelpFormatter`, `main(argv: list[str] | None = None) -> int`, and `run_cli(main)` under `if __name__ == "__main__"`.
- Write user-facing text in lowercase.
- You **must** use only the standard library, `rich`, `rich-argparse` and `prompt_toolkit`. Never use pip, uv or a virtualenv.
- Add a fish completion for every new script in `config/fish/completions/<name>.fish`, in the same shape as the existing ones.

## Tests
- Test a script in `tests/test_<name>.py`, loading it with `load_module("<name>")` from `conftest.py`.
- Test a shared `bin/_<name>.py` module in `tests/test_<name>.py` by importing it directly.
- Name a test after the behaviour it checks, such as `test_existing_files_can_be_skipped`.
- Separate arrange, act and assert with blank lines.
- Test against real files in `tmp_path`.
- Feed prompt answers through stdin with `answer(monkeypatch, *lines)` from `conftest.py`. Do not write another stdin helper.
- Skip a test when an external tool it needs is missing, with `pytest.mark.skipif`.
- You **must** monkeypatch standard modules by dotted string, such as `monkeypatch.setattr("subprocess.Popen", ...)`. The call may happen inside a shared module, so patching an attribute on the script module misses it.
