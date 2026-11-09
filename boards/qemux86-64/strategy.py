from pathlib import Path

import attr
from labgrid.factory import target_factory
from labgrid_boardkit.manifest import load_board
from labgrid_boardkit.strategies import QemuBootStrategy


@target_factory.reg_driver
@attr.s(eq=False)
class QEMUX86_64YoctoStrategy(QemuBootStrategy):
    """Boot strategy for the QEMU x86-64 Yocto target."""

    manifest = load_board(Path(__file__).parent)
