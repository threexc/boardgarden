from pathlib import Path

import attr
from labgrid.factory import target_factory
from labgrid_boardkit.manifest import load_board
from labgrid_boardkit.strategies import SdMuxBootStrategy


@target_factory.reg_driver
@attr.s(eq=False)
class MilkVDuo256MBootStrategy(SdMuxBootStrategy):
    """Boot strategy for Milk-V Duo 256M via USB SD-Mux."""

    manifest = load_board(Path(__file__).parent)
