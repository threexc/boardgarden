from pathlib import Path

import attr

from labgrid.factory import target_factory

from boardfarm_common.manifest import load_board
from boardfarm_common.strategies import SdMuxBootStrategy


@target_factory.reg_driver
@attr.s(eq=False)
class BananaPiF3BootStrategy(SdMuxBootStrategy):
    """Boot strategy for BananaPi F3 via USB SD-Mux."""

    manifest = load_board(Path(__file__).parent)
