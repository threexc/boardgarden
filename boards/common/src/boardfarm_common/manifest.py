from pathlib import Path

import yaml


def load_board(board_dir: str | Path) -> dict:
    """Load board.yaml manifest from a board directory."""
    path = Path(board_dir) / "board.yaml"
    with path.open() as f:
        return yaml.safe_load(f)
