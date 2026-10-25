from boardfarm_common.manifest import _deep_merge, board_variants, load_board


def test_deep_merge_overlays_nested_dicts():
    base = {"a": 1, "boot": {"kernel_addr": "$k", "dtb_addr": "$d"}}
    over = {"boot": {"dtb_addr": "$override"}}
    merged = _deep_merge(base, over)
    assert merged == {"a": 1, "boot": {"kernel_addr": "$k", "dtb_addr": "$override"}}


def test_deep_merge_replaces_scalars_and_lists():
    base = {"tools": ["a", "b"], "name": "base"}
    over = {"tools": ["c"], "name": "over"}
    merged = _deep_merge(base, over)
    assert merged == {"tools": ["c"], "name": "over"}


def test_deep_merge_does_not_mutate_inputs():
    base = {"boot": {"kernel_addr": "$k"}}
    over = {"boot": {"dtb_addr": "$d"}}
    _deep_merge(base, over)
    assert base == {"boot": {"kernel_addr": "$k"}}
    assert over == {"boot": {"dtb_addr": "$d"}}


def test_load_board_applies_inherits_and_board_yaml_wins(tmp_path):
    (tmp_path / "family").mkdir()
    (tmp_path / "family" / "defaults.yaml").write_text(
        "arch: riscv64\nboot:\n  kernel_addr: $family_addr\n"
    )
    board_dir = tmp_path / "my-board"
    board_dir.mkdir()
    (board_dir / "board.yaml").write_text(
        "name: my-board\n"
        "strategy: tftp\n"
        "inherits:\n"
        "  - ../family/defaults.yaml\n"
        "boot:\n"
        "  kernel_addr: $board_addr\n"
    )

    merged = load_board(board_dir)

    assert merged["arch"] == "riscv64"
    assert merged["boot"]["kernel_addr"] == "$board_addr"
    assert "inherits" not in merged


def test_load_board_real_board_picks_up_family_defaults(boards_dir):
    merged = load_board(boards_dir / "muse-pi-pro")
    # muse-pi-pro/board.yaml sets no top-level `arch`; it only appears via
    # `inherits: [../families/spacemit-k1/defaults.yaml]`.
    assert merged["arch"] == "riscv64"
    assert merged["name"] == "muse-pi-pro"


def test_load_board_variant_merges_over_base(tmp_path):
    (tmp_path / "board.yaml").write_text(
        "name: my-board\n"
        "strategy: fastboot\n"
        "shell:\n"
        "  username: root\n"
        "variants:\n"
        "  mainline:\n"
        "    strategy: tftp\n"
        "    shell:\n"
        "      prompt: '# '\n"
    )

    base = load_board(tmp_path)
    mainline = load_board(tmp_path, variant="mainline")

    assert board_variants(tmp_path) == ["mainline"]
    assert base["strategy"] == "fastboot"
    assert "variants" not in base
    assert mainline["strategy"] == "tftp"
    assert mainline["shell"] == {"username": "root", "prompt": "# "}
    assert "variants" not in mainline
