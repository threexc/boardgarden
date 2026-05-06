import attr
import enum
import time

import boardfarm_common.helpers as helpers

from labgrid.factory import target_factory
from labgrid.strategy.common import Strategy, StrategyError
from labgrid.driver.usbstoragedriver import Mode


class Status(enum.Enum):
    unknown = 0
    off = 1
    flashed = 2
    sd = 3


@target_factory.reg_driver
@attr.s(eq=False)
class BananaPiF3BootStrategy(Strategy):
    """BananaPiF3BootStrategy - Strategy to switch to boot BananaPi F3 with an SD Mux"""
    bindings = {
        "power": "PowerProtocol",
        "console": "ConsoleProtocol",
        "shell": "ShellDriver",
        "sdmux": "USBSDMuxDriver",
        "sdcard": "USBStorageDriver",
    }

    status = attr.ib(default=Status.unknown)

    def __attrs_post_init__(self):
        super().__attrs_post_init__()
        self.flashed = False

    def transition(self, status):
        if not isinstance(status, Status):
            status = Status[status]
        if status == Status.unknown:
            raise StrategyError(f"can not transition to {status}")
        elif status == self.status:
            return # nothing to do
        elif status == Status.off:
            self.target.deactivate(self.console)
            self.target.activate(self.power)
            self.power.off()
        elif status == Status.flashed:
            image = self.target.env.config.get_image_path("sdimage")
            self.transition(Status.off)

            # We only need to flash the image once, not for every test
            if not self.flashed:
                self.target.activate(self.sdmux)
                self.sdmux.set_mode("host")

                self.target.activate(self.sdcard)
                self.sdcard.write_image(image, Mode.BMAPTOOL)
                self.target.deactivate(self.sdcard)

                self.sdmux.set_mode("dut")

                self.target.deactivate(self.sdmux)

                self.flashed = True
        elif status == Status.sd:
            self.transition(Status.flashed)
            self.target.activate(self.console)
            self.power.cycle()
            self.target.activate(self.shell)
        else:
            raise StrategyError(f"no transition found from {self.status} to {status}")
        self.status = status

    def force(self, status):
        if not isinstance(status, Status):
            status = Status[status]
        if status == Status.off:
            self.target.activate(self.power)
        elif status == Status.sd:
            self.target.activate(self.shell)
        else:
            raise StrategyError("can not force state {}".format(status))
        self.status = status

