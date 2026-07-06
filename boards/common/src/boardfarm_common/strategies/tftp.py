import enum

import attr
from labgrid.strategy.common import StrategyError

from boardfarm_common import helpers
from boardfarm_common.strategies.base import BoardStrategy


class TftpStatus(enum.Enum):
    unknown = 0
    off = 1
    uboot = 2
    emmc = 3
    tftp = 4


@attr.s(eq=False)
class TftpBootStrategy(BoardStrategy):
    """Boot a physical board via U-Boot + TFTP.

    Reads bootargs, tftp subdir/kernel/dtb, and load addresses from
    ``self.manifest`` (populated by the concrete per-board subclass).
    """

    bindings = {
        "power": "PowerProtocol",
        "console": "ConsoleProtocol",
        "uboot": "UBootDriver",
        "shell": "ShellDriver",
        "tftp": "TFTPProviderDriver",
    }

    status = attr.ib(default=TftpStatus.unknown)

    def __attrs_post_init__(self):
        super().__attrs_post_init__()
        self.staged = False

    @property
    def bootargs(self) -> str:
        return self.manifest["boot"]["bootargs"].strip()

    def _stage(self):
        helpers.uboot_stage(self)

    def _tftp_stage_files(self):
        boot = self.manifest["boot"]
        tftp = self.manifest["tftp"]
        helpers.uboot_set_server_ip(self)
        helpers.uboot_set_bootargs(self, self.bootargs)
        helpers.uboot_tftpboot_file(self, boot["kernel_addr"], tftp["subdir"], tftp["kernel"])
        helpers.uboot_tftpboot_file(self, boot["dtb_addr"], tftp["subdir"], tftp["dtb"])

    def transition(self, status):
        if not isinstance(status, TftpStatus):
            status = TftpStatus[status]
        if status == TftpStatus.unknown:
            raise StrategyError(f"can not transition to {status}")
        elif status == self.status:
            return
        elif status == TftpStatus.off:
            self.target.deactivate(self.console)
            self.target.activate(self.power)
            self.power.off()
        elif status == TftpStatus.uboot:
            self.transition(TftpStatus.off)
            self.target.activate(self.console)
            self.power.cycle()
            self.target.activate(self.uboot)
            self._stage()
        elif status == TftpStatus.emmc:
            self.transition(TftpStatus.uboot)
            self.uboot.boot("emmc")
            self.uboot.await_boot()
            self.target.activate(self.shell)
        elif status == TftpStatus.tftp:
            self.transition(TftpStatus.uboot)
            self._tftp_stage_files()
            self.uboot.boot("tftp")
            self.uboot.await_boot()
            self.target.activate(self.shell)
        else:
            raise StrategyError(f"no transition found from {self.status} to {status}")
        self.status = status

    def force(self, status):
        if not isinstance(status, TftpStatus):
            status = TftpStatus[status]
        if status == TftpStatus.off:
            self.target.activate(self.power)
        elif status == TftpStatus.uboot:
            self.target.activate(self.uboot)
        elif status in (TftpStatus.emmc, TftpStatus.tftp):
            self.target.activate(self.shell)
        else:
            raise StrategyError(f"can not force state {status}")
        self.status = status
