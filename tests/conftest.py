import importlib.machinery
import importlib.util
import pathlib

BIN = pathlib.Path(__file__).resolve().parents[1] / "bin"


def load_module(name):
    loader = importlib.machinery.SourceFileLoader(name, str(BIN / name))
    spec = importlib.util.spec_from_loader(name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module