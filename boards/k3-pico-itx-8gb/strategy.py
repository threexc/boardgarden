from pathlib import Path

import attr
from labgrid.factory import target_factory
from labgrid_boardkit.manifest import load_board
from labgrid_boardkit.strategies import FastbootFlashStrategy, TftpBootStrategy


@target_factory.reg_driver
@attr.s(eq=False)
class K3PicoItxBootStrategy(FastbootFlashStrategy):
    """Boot strategy for K3 Pico-ITX."""

    manifest = load_board(Path(__file__).parent)


@target_factory.reg_driver
@attr.s(eq=False)
class K3PicoItxTftpBootStrategy(TftpBootStrategy):
    """Boot strategy for K3 Pico-ITX, TFTP-booting the default BSP."""

    manifest = load_board(Path(__file__).parent, variant="tftp")


@target_factory.reg_driver
@attr.s(eq=False)
class K3PicoItxMainlineBootStrategy(FastbootFlashStrategy):
    """Boot strategy for K3 Pico-ITX with the mainline-kernel BSP."""

    manifest = load_board(Path(__file__).parent, variant="mainline")


@target_factory.reg_driver
@attr.s(eq=False)
class K3PicoItxMainlineFitBootStrategy(TftpBootStrategy):
    """Boot strategy for K3 Pico-ITX, TFTP-booting the mainline BSP as a FIT image."""

    manifest = load_board(Path(__file__).parent, variant="mainline-fit")
