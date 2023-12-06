"""Directory for externally managed models."""

from sys import path as sys_path
from sys import meta_path
from os.path import abspath, dirname, join
from importlib.abc import MetaPathFinder


class _CG_GNNImportHook(MetaPathFinder):
    """An import hook to detect if cg_gnn is trying to be imported."""

    def find_spec(self, fullname, path, target=None):
        """Add cg_gnn to the Python path when something tries to import it."""
        if fullname == f'{__name__}.cg_gnn':
            current_dir = dirname(abspath(__file__))
            cggnn_dir = join(current_dir, 'cg_gnn')
            if cggnn_dir not in sys_path:
                sys_path.insert(0, cggnn_dir)
        return None


meta_path.insert(0, _CG_GNNImportHook())
