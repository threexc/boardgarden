from pathlib import Path

import attr
from labgrid.factory import target_factory
from labgrid_boardkit.manifest import load_board
from labgrid_boardkit.strategies import QemuBootStrategy


@target_factory.reg_driver
@attr.s(eq=False)
class QEMUYoctoStrategy(QemuBootStrategy):
    """Boot strategy for the QEMU RISC-V Yocto target."""

    manifest = load_board(Path(__file__).parent)
