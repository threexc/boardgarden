from pathlib import Path

import attr
from boardfarm_common.manifest import load_board
from boardfarm_common.strategies import FastbootFlashStrategy, TftpBootStrategy
from labgrid.factory import target_factory


@target_factory.reg_driver
@attr.s(eq=False)
class K3PicoItxBootStrategy(FastbootFlashStrategy):
    """Boot strategy for K3 Pico-ITX."""

    manifest = load_board(Path(__file__).parent)


@target_factory.reg_driver
@attr.s(eq=False)
class K3PicoItxMainlineBootStrategy(TftpBootStrategy):
    """Boot strategy for K3 Pico-ITX with the mainline-kernel BSP."""

    manifest = load_board(Path(__file__).parent, variant="mainline")
