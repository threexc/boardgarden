from pathlib import Path

import attr
from labgrid.factory import target_factory
from labgrid_boardkit.manifest import load_board
from labgrid_boardkit.strategies import SdMuxBootStrategy


@target_factory.reg_driver
@attr.s(eq=False)
class BananaPiF3BootStrategy(SdMuxBootStrategy):
    """Boot strategy for BananaPi F3 via USB SD-Mux."""

    manifest = load_board(Path(__file__).parent)
