import pytest
from boardfarm_common.manifest import board_variants
from boardfarm_common.render import INDEX_NAME, _find_boards, render, render_index
from conftest import REAL_BOARDS


@pytest.mark.parametrize("board", REAL_BOARDS)
def test_render_matches_committed_output(boards_dir, board):
    """Regression guard: the committed client.yaml/env.yaml (and any
    client-<variant>.yaml) for every real board must match what render()
    produces from board.yaml right now. This is the same invariant
    `boardfarm-render --check` enforces in CI, exercised here as a pure unit
    test with no network/hardware involved."""
    board_dir = boards_dir / board
    for variant in [None, *board_variants(board_dir)]:
        out_path, rendered = render(board_dir, variant)

        assert out_path.parent == board_dir
        assert rendered == out_path.read_text()


def test_machine_index_matches_committed_output(boards_dir):
    assert render_index(_find_boards(boards_dir)) == (boards_dir / INDEX_NAME).read_text()


def test_machine_index_has_a_row_per_variant(tmp_path):
    board_dir = tmp_path / "my-board"
    board_dir.mkdir()
    (board_dir / "board.yaml").write_text(
        "name: my-board\n"
        "yocto_machine: my-machine\n"
        "strategy: qemu\n"
        "remote_place: bf-my-board\n"
        "variants:\n"
        "  mainline:\n"
        "    yocto_machine: my-machine-mainline\n"
        "    exclude_from_nightly: true\n"
    )

    index = render_index([board_dir]).splitlines()

    assert index[1].split("\t")[:3] == ["my-machine", "my-board", "-"]
    row = dict(zip(index[0].split("\t"), index[2].split("\t"), strict=True))
    assert row["machine"] == "my-machine-mainline"
    assert row["variant"] == "mainline"
    assert row["nightly"] == "no"
    assert row["client"] == "env-mainline.yaml"


def test_render_unknown_strategy_raises(tmp_path):
    board_dir = tmp_path / "mystery-board"
    board_dir.mkdir()
    (board_dir / "board.yaml").write_text("name: mystery-board\nstrategy: unknown\n")

    with pytest.raises(ValueError, match="unknown strategy"):
        render(board_dir)
