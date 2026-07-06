import enum

import attr

from labgrid.driver.usbstoragedriver import Mode
from labgrid.strategy.common import StrategyError

from boardfarm_common.strategies.base import BoardStrategy


class SdMuxStatus(enum.Enum):
    unknown = 0
    off = 1
    flashed = 2
    sd = 3


@attr.s(eq=False)
class SdMuxBootStrategy(BoardStrategy):
    """Boot a physical board from an SD card written via USB SD-Mux.

    ``image_label`` names the image entry in the labgrid client.yaml
    ``images:`` section that holds the wic/gz path.
    """

    bindings = {
        "power": "PowerProtocol",
        "console": "ConsoleProtocol",
        "shell": "ShellDriver",
        "sdmux": "USBSDMuxDriver",
        "sdcard": "USBStorageDriver",
    }

    status = attr.ib(default=SdMuxStatus.unknown)
    image_label = attr.ib(default="sdimage")

    def __attrs_post_init__(self):
        super().__attrs_post_init__()
        self.flashed = False

    def transition(self, status):
        if not isinstance(status, SdMuxStatus):
            status = SdMuxStatus[status]
        if status == SdMuxStatus.unknown:
            raise StrategyError(f"can not transition to {status}")
        elif status == self.status:
            return
        elif status == SdMuxStatus.off:
            self.target.deactivate(self.console)
            self.target.activate(self.power)
            self.power.off()
        elif status == SdMuxStatus.flashed:
            image = self.target.env.config.get_image_path(self.image_label)
            self.transition(SdMuxStatus.off)
            if not self.flashed:
                self.target.activate(self.sdmux)
                self.sdmux.set_mode("host")
                self.target.activate(self.sdcard)
                self.sdcard.write_image(image, Mode.BMAPTOOL)
                self.target.deactivate(self.sdcard)
                self.sdmux.set_mode("dut")
                self.target.deactivate(self.sdmux)
                self.flashed = True
        elif status == SdMuxStatus.sd:
            self.transition(SdMuxStatus.flashed)
            self.target.activate(self.console)
            self.power.cycle()
            self.target.activate(self.shell)
        else:
            raise StrategyError(f"no transition found from {self.status} to {status}")
        self.status = status

    def force(self, status):
        if not isinstance(status, SdMuxStatus):
            status = SdMuxStatus[status]
        if status == SdMuxStatus.off:
            self.target.activate(self.power)
        elif status == SdMuxStatus.sd:
            self.target.activate(self.shell)
        else:
            raise StrategyError(f"can not force state {status}")
        self.status = status
