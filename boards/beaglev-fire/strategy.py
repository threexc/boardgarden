from pathlib import Path

import attr
from boardfarm_common.manifest import load_board
from boardfarm_common.strategies import TftpBootStrategy
from labgrid.factory import target_factory


@target_factory.reg_driver
@attr.s(eq=False)
class BeagleVFireBootStrategy(TftpBootStrategy):
    """Boot strategy for BeagleV-Fire."""

    manifest = load_board(Path(__file__).parent)
