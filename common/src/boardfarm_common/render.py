"""Render labgrid client.yaml (or env.yaml for qemu) from a board manifest.

Each ``variants:`` entry renders to ``client-<variant>.yaml`` alongside. All
boards' Yocto MACHINEs are also indexed in ``boards/machines.tsv``, a flat
table the CI shell steps can read without a YAML parser.

CLI:
    boardfarm-render                       # renders client.yaml for every boards/*/board.yaml under the repo root (cwd)
    boardfarm-render <board_dir> [...]     # renders only the given boards (the index always covers all of them)
    boardfarm-render --check               # non-destructive; exit 1 if any rendered output differs
"""

import argparse
import sys
from pathlib import Path

from jinja2 import Environment, PackageLoader, StrictUndefined

from boardfarm_common.manifest import board_variants, load_board

_STRATEGY_TO_TEMPLATE = {
    "tftp": ("client-tftp.yaml.j2", "client.yaml"),
    "sdmux": ("client-sdmux.yaml.j2", "client.yaml"),
    "fastboot": ("client-fastboot.yaml.j2", "client.yaml"),
    "qemu": ("client-qemu.yaml.j2", "env.yaml"),
}

INDEX_NAME = "machines.tsv"
INDEX_COLUMNS = (
    "machine",
    "board",
    "variant",
    "strategy",
    "remote_place",
    "tftp_subdir",
    "initramfs",
    "nightly",
    "client",
    "image_dir",
)


def _env() -> Environment:
    return Environment(
        loader=PackageLoader("boardfarm_common", "templates"),
        undefined=StrictUndefined,
        keep_trailing_newline=True,
    )


def _template(board_dir: Path, manifest: dict, variant: str | None) -> tuple[str, str]:
    """Return ``(template_name, output_file_name)`` for a manifest."""
    strategy = manifest.get("strategy")
    if strategy not in _STRATEGY_TO_TEMPLATE:
        raise ValueError(f"{board_dir}: unknown strategy {strategy!r}")
    template_name, out_name = _STRATEGY_TO_TEMPLATE[strategy]
    if variant is not None:
        out_name = out_name.replace(".yaml", f"-{variant}.yaml")
    return template_name, out_name


def render(board_dir: str | Path, variant: str | None = None) -> tuple[Path, str]:
    """Return ``(output_path, rendered_yaml_text)`` for a board or one of its variants."""
    board_dir = Path(board_dir)
    manifest = load_board(board_dir, variant)
    template_name, out_name = _template(board_dir, manifest, variant)
    tmpl = _env().get_template(template_name)
    return board_dir / out_name, tmpl.render(manifest=manifest)


def render_index(board_dirs: list[Path]) -> str:
    """Return the tab-separated MACHINE index: one row per board and variant."""
    lines = ["\t".join(INDEX_COLUMNS)]
    for board_dir in board_dirs:
        for variant in [None, *board_variants(board_dir)]:
            m = load_board(board_dir, variant)
            tftp = m.get("tftp", {})
            row = {
                "machine": m.get("yocto_machine"),
                "board": board_dir.name,
                "variant": variant,
                "strategy": m.get("strategy"),
                "remote_place": m.get("remote_place"),
                "tftp_subdir": tftp.get("subdir", board_dir.name),
                "initramfs": "yes" if "initramfs" in tftp else "no",
                "nightly": "no" if m.get("exclude_from_nightly") else "yes",
                "client": _template(board_dir, m, variant)[1],
                "image_dir": m["fastboot"]["image_dir"] if m["strategy"] == "fastboot" else None,
            }
            lines.append("\t".join(str(row[c] or "-") for c in INDEX_COLUMNS))
    return "\n".join(lines) + "\n"


def _find_boards(root: Path) -> list[Path]:
    return [p.parent for p in sorted(root.glob("*/board.yaml"))]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render labgrid client.yaml from board.yaml")
    parser.add_argument("board_dirs", nargs="*", type=Path)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit non-zero if any rendered output differs from the on-disk file.",
    )
    args = parser.parse_args(argv)

    root = args.board_dirs[0].parent if args.board_dirs else Path.cwd() / "boards"
    all_boards = _find_boards(root)
    board_dirs = args.board_dirs or all_boards
    if not board_dirs:
        print("no boards found", file=sys.stderr)
        return 2

    outputs = [render(bd, v) for bd in board_dirs for v in [None, *board_variants(bd)]]
    outputs.append((root / INDEX_NAME, render_index(all_boards)))

    diffs = 0
    for out_path, rendered in outputs:
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
