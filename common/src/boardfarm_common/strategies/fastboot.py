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

    Holding the ``recovery`` button while power comes up, then pulsing
    ``reset``, drops the board into USB download mode. Each ``fastboot.stage`` image is
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
        press = fb.get("press_time", 1)
        self.target.activate(self.recovery)
        self.target.activate(self.reset)
        self.target.activate(self.power)
        # Hold recovery across power-up (enters download mode if the board
        # starts on power) and a reset pulse (if it was already running).
        self.recovery.set(True)
        time.sleep(press)
        # cycle(), not on(): transition(off) only just cut power, and a relay
        # flipped back within milliseconds never actually drops the board.
        self.power.cycle()
        time.sleep(fb.get("power_on_delay", 2))
        self.reset.set(True)
        time.sleep(press)
        self.reset.set(False)
        # Keep holding recovery until the boot ROM has sampled it.
        time.sleep(press)
        self.recovery.set(False)

    def _flash(self):
        fb = self.manifest["fastboot"]
        # Copy staged images to the exporter up front: the boot ROM's download
        # mode doesn't wait around for slow transfers.
        staged = []
        for image in fb.get("stage", []):
            mf = ManagedFile(self._image(image), self.fastboot.fastboot)
            mf.sync_to_resource()
            staged.append(mf.get_remote_path())
        self._enter_download_mode()
        self.target.activate(self.fastboot)
        for remote_path in staged:
            self.fastboot("stage", remote_path)
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
