import pytest
from boardfarm_common.render import render

BOARDS_AND_OUTPUTS = [
    ("bananapi-f3", "client.yaml"),
    ("k3-pico-itx", "client.yaml"),
    ("muse-pi-pro", "client.yaml"),
    ("orangepi-rv2", "client.yaml"),
    ("qemuriscv64", "env.yaml"),
]


@pytest.mark.parametrize(("board", "out_name"), BOARDS_AND_OUTPUTS)
def test_render_matches_committed_output(boards_dir, board, out_name):
    """Regression guard: the committed client.yaml/env.yaml for every real
    board must match what render() produces from board.yaml right now. This
    is the same invariant `boardfarm-render --check` enforces in CI, exercised
    here as a pure unit test with no network/hardware involved."""
    board_dir = boards_dir / board
    out_path, rendered = render(board_dir)

    assert out_path == board_dir / out_name
    assert rendered == out_path.read_text()


def test_render_unknown_strategy_raises(tmp_path):
    board_dir = tmp_path / "mystery-board"
    board_dir.mkdir()
    (board_dir / "board.yaml").write_text("name: mystery-board\nstrategy: unknown\n")

    with pytest.raises(ValueError, match="unknown strategy"):
        render(board_dir)
