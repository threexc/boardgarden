from pathlib import Path

import attr
from boardfarm_common.manifest import load_board
from boardfarm_common.strategies import SdMuxBootStrategy
from labgrid.factory import target_factory


@target_factory.reg_driver
@attr.s(eq=False)
class MilkVDuo256MBootStrategy(SdMuxBootStrategy):
    """Boot strategy for Milk-V Duo 256M via USB SD-Mux."""

    manifest = load_board(Path(__file__).parent)
