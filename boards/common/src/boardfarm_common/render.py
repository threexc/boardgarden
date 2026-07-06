"""Render labgrid client.yaml (or env.yaml for qemu) from a board manifest.

CLI:
    boardfarm-render                       # renders client.yaml for every boards/*/board.yaml under cwd
    boardfarm-render <board_dir> [...]     # renders only the given boards
    boardfarm-render --check               # non-destructive; exit 1 if any rendered output differs
"""

import argparse
import sys
from pathlib import Path

from jinja2 import Environment, PackageLoader, StrictUndefined

from boardfarm_common.manifest import load_board


_STRATEGY_TO_TEMPLATE = {
    "tftp": ("client-tftp.yaml.j2", "client.yaml"),
    "sdmux": ("client-sdmux.yaml.j2", "client.yaml"),
    "qemu": ("client-qemu.yaml.j2", "env.yaml"),
}


def _env() -> Environment:
    return Environment(
        loader=PackageLoader("boardfarm_common", "templates"),
        undefined=StrictUndefined,
        keep_trailing_newline=True,
    )


def render(board_dir: str | Path) -> tuple[Path, str]:
    """Return ``(output_path, rendered_yaml_text)`` for a board."""
    board_dir = Path(board_dir)
    manifest = load_board(board_dir)
    strategy = manifest.get("strategy")
    if strategy not in _STRATEGY_TO_TEMPLATE:
        raise ValueError(f"{board_dir}: unknown strategy {strategy!r}")
    template_name, out_name = _STRATEGY_TO_TEMPLATE[strategy]
    tmpl = _env().get_template(template_name)
    return board_dir / out_name, tmpl.render(manifest=manifest)


def _find_boards(root: Path) -> list[Path]:
    return [p.parent for p in sorted(root.glob("*/board.yaml"))]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render labgrid client.yaml from board.yaml")
    parser.add_argument("board_dirs", nargs="*", type=Path)
    parser.add_argument(
        "--check", action="store_true",
        help="Exit non-zero if any rendered output differs from the on-disk file.",
    )
    args = parser.parse_args(argv)

    board_dirs = args.board_dirs or _find_boards(Path.cwd())
    if not board_dirs:
        print("no boards found", file=sys.stderr)
        return 2

    diffs = 0
    for bd in board_dirs:
        out_path, rendered = render(bd)
        if args.check:
            existing = out_path.read_text() if out_path.exists() else ""
            if existing != rendered:
                diffs += 1
                print(f"DIFF  {out_path}")
            else:
                print(f"ok    {out_path}")
        else:
            out_path.write_text(rendered)
            print(f"wrote {out_path}")
    return 1 if (args.check and diffs) else 0


if __name__ == "__main__":
    sys.exit(main())
