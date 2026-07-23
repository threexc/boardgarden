import jsonschema
import pytest
from boardfarm_common.manifest import load_board
from boardfarm_common.validate import main, validate_manifest

REAL_BOARDS = ["bananapi-f3", "k3-pico-itx", "muse-pi-pro", "orangepi-rv2", "qemuriscv64"]


@pytest.mark.parametrize("board", REAL_BOARDS)
def test_validate_manifest_accepts_real_boards(boards_dir, board):
    validate_manifest(load_board(boards_dir / board))


def test_validate_manifest_rejects_missing_required_field(boards_dir):
    manifest = load_board(boards_dir / "qemuriscv64")
    del manifest["qemu"]["binary"]
    with pytest.raises(jsonschema.ValidationError):
        validate_manifest(manifest)


def test_validate_manifest_rejects_unknown_strategy_enum_value(boards_dir):
    manifest = load_board(boards_dir / "qemuriscv64")
    manifest["strategy"] = "does-not-exist"
    with pytest.raises(jsonschema.ValidationError):
        validate_manifest(manifest)


def test_main_ok_for_real_boards(boards_dir, capsys):
    board_dirs = [str(boards_dir / b) for b in REAL_BOARDS]
    assert main(board_dirs) == 0
    out = capsys.readouterr().out
    for board in REAL_BOARDS:
        assert f"ok    {boards_dir / board}/board.yaml" in out


def test_main_fails_for_invalid_board(tmp_path, capsys):
    board_dir = tmp_path / "broken-board"
    board_dir.mkdir()
    (board_dir / "board.yaml").write_text("name: broken-board\nstrategy: tftp\n")

    assert main([str(board_dir)]) == 1
    err = capsys.readouterr().err
    assert "FAIL" in err
