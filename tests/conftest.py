import importlib.machinery
import importlib.util
import io
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
BIN = ROOT / "bin"
HOMELAB = ROOT / "homelab"
os.environ["COLUMNS"] = "500"
sys.path.insert(0, str(BIN))


def load_module(name, directory=BIN):
    path = str(directory / name)
    loader = importlib.machinery.SourceFileLoader(name, path)
    spec = importlib.util.spec_from_loader(name, loader)
    if spec is None:
        raise ImportError(f"can't load {path}")
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def answer(monkeypatch, *lines):
    monkeypatch.setattr(
        "sys.stdin", io.StringIO("".join(f"{line}\n" for line in lines))
    )
