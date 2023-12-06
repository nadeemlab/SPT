"""Directory for externally managed models."""

from sys import path as sys_path
from sys import meta_path
from os.path import abspath, dirname, join
from importlib.abc import MetaPathFinder


class _CGModelImportHook(MetaPathFinder):
    """An import hook for if one of these externally manageed models is imported."""

    def find_spec(self, fullname, path, target=None):
        """Add the model to the Python path when something tries to import it."""
        for model in {'cg_gnn'}:
            _maybe_add_module_to_path(fullname, model)
        return None


def _maybe_add_module_to_path(fullname: str, model: str):
    """Add this module to the Python path if it's being imported."""
    if fullname == f'{__name__}.{model}':
        current_dir = dirname(abspath(__file__))
        model_dir = join(current_dir, model)
        if model_dir not in sys_path:
            sys_path.insert(0, model_dir)


meta_path.insert(0, _CGModelImportHook())
