from pathlib import Path

import attr

from labgrid.factory import target_factory

from boardfarm_common.manifest import load_board
from boardfarm_common.strategies import QemuBootStrategy


@target_factory.reg_driver
@attr.s(eq=False)
class QEMUYoctoStrategy(QemuBootStrategy):
    """Boot strategy for the QEMU RISC-V Yocto target."""

    manifest = load_board(Path(__file__).parent)
