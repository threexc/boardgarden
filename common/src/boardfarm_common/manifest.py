"""Load and merge board.yaml manifests.

``inherits:`` in a board.yaml lists paths (relative to the board dir) to
defaults files. Files are deep-merged in order; the board.yaml wins.

``variants:`` maps a name to overrides describing another way to boot the same
board, usually for a different Yocto MACHINE (e.g. a mainline-kernel BSP that
TFTP-boots while the default flashes storage). A variant is deep-merged over
the base manifest.
"""

from copy import deepcopy
from pathlib import Path

import yaml


def _read_yaml(path: Path) -> dict:
    with path.open() as f:
        return yaml.safe_load(f) or {}


def _deep_merge(base: dict, over: dict) -> dict:
    """Recursively merge ``over`` into ``base``. Lists and scalars are replaced."""
    out = deepcopy(base)
    for k, v in over.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = deepcopy(v)
    return out


def load_board(board_dir: str | Path, variant: str | None = None) -> dict:
    """Load ``board.yaml`` from a board directory, applying ``inherits:`` defaults
    and, if given, the named ``variants:`` entry. The result has no ``variants``."""
    board_dir = Path(board_dir)
    board_yaml = _read_yaml(board_dir / "board.yaml")

    merged: dict = {}
    for rel in board_yaml.get("inherits", []):
        merged = _deep_merge(merged, _read_yaml((board_dir / rel).resolve()))
    merged = _deep_merge(merged, board_yaml)
    merged.pop("inherits", None)
    variants = merged.pop("variants", {})
    if variant is not None:
        merged = _deep_merge(merged, variants[variant])
    return merged


def board_variants(board_dir: str | Path) -> list[str]:
    """Names of the ``variants:`` declared in a board's ``board.yaml``."""
    return list(_read_yaml(Path(board_dir) / "board.yaml").get("variants", {}))
