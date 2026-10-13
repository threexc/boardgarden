from pathlib import Path

import attr
from boardfarm_common.manifest import load_board
from boardfarm_common.strategies import QemuBootStrategy
from labgrid.factory import target_factory


@target_factory.reg_driver
@attr.s(eq=False)
class QEMUX86_64YoctoStrategy(QemuBootStrategy):
    """Boot strategy for the QEMU x86-64 Yocto target."""

    manifest = load_board(Path(__file__).parent)
