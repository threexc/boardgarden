from pathlib import Path

import attr

from labgrid.factory import target_factory

from boardfarm_common.manifest import load_board
from boardfarm_common.strategies import TftpBootStrategy


@target_factory.reg_driver
@attr.s(eq=False)
class OrangePiRV2BootStrategy(TftpBootStrategy):
    """Boot strategy for OrangePi RV2."""

    manifest = load_board(Path(__file__).parent)
