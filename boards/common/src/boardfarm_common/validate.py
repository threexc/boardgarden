"""Validate board.yaml manifests against ``schema/board.schema.json``.

CLI:
    boardfarm-validate                # walks boards/*/board.yaml under cwd
    boardfarm-validate path/to/board.yaml [more.yaml ...]
"""

import argparse
import json
import sys
from importlib.resources import files
from pathlib import Path

import jsonschema

from boardfarm_common.loader import strategy_for
from boardfarm_common.manifest import load_board


def _schema() -> dict:
    return json.loads(files("boardfarm_common.schema").joinpath("board.schema.json").read_text())


def validate_manifest(manifest: dict) -> None:
    """Raise ``jsonschema.ValidationError`` if the manifest is invalid.

    Also confirms the referenced strategy family is registered.
    """
    jsonschema.validate(manifest, _schema())
    strategy_for(manifest)  # raises UnknownStrategy if unregistered


def _iter_board_yamls(root: Path):
    yield from sorted(root.glob("*/board.yaml"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate boardfarm board.yaml manifests")
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="board.yaml files (or board dirs). Default: boards/*/board.yaml under cwd.",
    )
    args = parser.parse_args(argv)

    targets: list[Path] = []
    if args.paths:
        for p in args.paths:
            targets.append(p if p.is_dir() else p.parent)
    else:
        targets = [p.parent for p in _iter_board_yamls(Path.cwd())]

    if not targets:
        print("no board.yaml files found", file=sys.stderr)
        return 2

    failures = 0
    for board_dir in targets:
        try:
            manifest = load_board(board_dir)
            validate_manifest(manifest)
        except Exception as exc:  # noqa: BLE001
            failures += 1
            print(f"FAIL  {board_dir}/board.yaml: {exc}", file=sys.stderr)
        else:
            print(f"ok    {board_dir}/board.yaml")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
