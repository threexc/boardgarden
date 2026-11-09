from pathlib import Path

import attr
from labgrid.factory import target_factory
from labgrid_boardkit.manifest import load_board
from labgrid_boardkit.strategies import SdMuxBootStrategy, TftpBootStrategy


@target_factory.reg_driver
@attr.s(eq=False)
class MusePiProBootStrategy(SdMuxBootStrategy):
    """Boot strategy for Muse Pi Pro via USB SD-Mux."""

    manifest = load_board(Path(__file__).parent)


@target_factory.reg_driver
@attr.s(eq=False)
class MusePiProTftpBootStrategy(TftpBootStrategy):
    """Boot strategy for Muse Pi Pro, TFTP-booting kernel, DTB and initramfs."""

    manifest = load_board(Path(__file__).parent, variant="tftp")
