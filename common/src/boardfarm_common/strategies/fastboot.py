import enum
import time
from pathlib import Path

import attr
from labgrid.strategy.common import StrategyError
from labgrid.util.managedfile import ManagedFile

from boardfarm_common.strategies.base import BoardStrategy


class FastbootStatus(enum.Enum):
    unknown = 0
    off = 1
    flashed = 2
    shell = 3


@attr.s(eq=False)
class FastbootFlashStrategy(BoardStrategy):
    """Flash a physical board's storage over USB fastboot, then boot it.

    With the board powered on, holding the ``recovery`` button while pulsing
    ``reset`` drops it into USB download mode. Each ``fastboot.stage`` image is
    then staged and continued in order (e.g. SPL, then a fastboot-capable
    U-Boot), and each ``fastboot.flash`` partition is written. File names are
    relative to ``fastboot.image_dir``.
    """

    bindings = {
        "power": "PowerProtocol",
        "console": "ConsoleProtocol",
        "shell": "ShellDriver",
        "fastboot": "AndroidFastbootDriver",
        "recovery": "DigitalOutputProtocol",
        "reset": "DigitalOutputProtocol",
    }

    status = attr.ib(default=FastbootStatus.unknown)

    def __attrs_post_init__(self):
        super().__attrs_post_init__()
        self.flashed = False

    def _image(self, name: str) -> str:
        return str(Path(self.manifest["fastboot"]["image_dir"]) / name)

    def _enter_download_mode(self):
        fb = self.manifest["fastboot"]
        self.target.activate(self.recovery)
        self.target.activate(self.reset)
        self.recovery.set(True)
        self.reset.set(True)
        time.sleep(fb.get("press_time", 0.5))
        self.reset.set(False)
        # Keep holding recovery until the boot ROM has sampled it.
        time.sleep(fb.get("press_time", 0.5))
        self.recovery.set(False)

    def _flash(self):
        fb = self.manifest["fastboot"]
        self.target.activate(self.power)
        self.power.on()
        time.sleep(fb.get("power_on_delay", 2))
        self._enter_download_mode()
        self.target.activate(self.fastboot)
        for image in fb.get("stage", []):
            mf = ManagedFile(self._image(image), self.fastboot.fastboot)
            mf.sync_to_resource()
            self.fastboot("stage", mf.get_remote_path())
            self.fastboot.continue_boot()
            # The device re-enumerates as the staged image comes up; fastboot
            # waits for it, but talking to the old instance too early fails.
            time.sleep(fb.get("continue_delay", 3))
        for partition, image in fb["flash"].items():
            self.fastboot.flash(partition, self._image(image))
        self.target.deactivate(self.fastboot)

    def transition(self, status):
        if not isinstance(status, FastbootStatus):
            status = FastbootStatus[status]
        if status == FastbootStatus.unknown:
            raise StrategyError(f"can not transition to {status}")
        elif status == self.status:
            return
        elif status == FastbootStatus.off:
            self.target.deactivate(self.console)
            self.target.activate(self.power)
            self.power.off()
        elif status == FastbootStatus.flashed:
            self.transition(FastbootStatus.off)
            if not self.flashed:
                self._flash()
                self.flashed = True
        elif status == FastbootStatus.shell:
            self.transition(FastbootStatus.flashed)
            self.target.activate(self.console)
            self.power.cycle()
            self.target.activate(self.shell)
        else:
            raise StrategyError(f"no transition found from {self.status} to {status}")
        self.status = status

    def force(self, status):
        if not isinstance(status, FastbootStatus):
            status = FastbootStatus[status]
        if status == FastbootStatus.off:
            self.target.activate(self.power)
        elif status == FastbootStatus.shell:
            self.target.activate(self.shell)
        else:
            raise StrategyError(f"can not force state {status}")
        self.status = status
