from pathlib import Path

import attr
from boardfarm_common.manifest import load_board
from boardfarm_common.strategies import SdMuxBootStrategy, TftpBootStrategy
from labgrid.factory import target_factory


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
