import enum

import attr

from labgrid.step import step
from labgrid.strategy.common import StrategyError

from boardfarm_common.strategies.base import BoardStrategy


class QemuStatus(enum.Enum):
    unknown = 0
    off = 1
    booting = 2
    shell = 3


@attr.s(eq=False)
class QemuBootStrategy(BoardStrategy):
    """Boot a QEMU-based target."""

    bindings = {
        "qemu_driver": "QEMUDriver",
        "shell": "ShellDriver",
    }

    status = attr.ib(default=QemuStatus.unknown)

    @step(title="transition")
    def transition(self, status):
        if not isinstance(status, QemuStatus):
            status = QemuStatus[status]

        if status == QemuStatus.off:
            if self.status == QemuStatus.shell:
                self.target.deactivate(self.shell)
                self.qemu_driver.off()
                self.target.deactivate(self.qemu_driver)
            self.status = QemuStatus.off
        elif status == QemuStatus.shell:
            if self.status == QemuStatus.shell:
                return
            if self.status == QemuStatus.booting:
                raise StrategyError(
                    "Cannot go to shell directly from booting; turn off first."
                )
            self.target.activate(self.qemu_driver)
            self.qemu_driver.on()
            self.status = QemuStatus.booting
            self.target.activate(self.shell)
            self.status = QemuStatus.shell
        else:
            raise StrategyError(f"Unknown status {status}")
