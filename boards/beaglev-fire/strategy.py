from pathlib import Path

import attr
from labgrid.factory import target_factory
from labgrid_boardkit.manifest import load_board
from labgrid_boardkit.strategies import TftpBootStrategy


@target_factory.reg_driver
@attr.s(eq=False)
class BeagleVFireBootStrategy(TftpBootStrategy):
    """Boot strategy for BeagleV-Fire."""

    manifest = load_board(Path(__file__).parent)
