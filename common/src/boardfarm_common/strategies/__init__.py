"""Boardfarm strategy families.

Import the family classes from here or (preferred at scale) resolve them by
name via ``boardfarm_common.loader.strategy_for(manifest)``, which consults
the ``boardfarm.strategies`` entry-point registry declared in ``pyproject.toml``.
"""

from boardfarm_common.strategies.base import BoardStrategy
from boardfarm_common.strategies.fastboot import FastbootFlashStrategy, FastbootStatus
from boardfarm_common.strategies.qemu import ExternalQemuStrategy, QemuBootStrategy, QemuStatus
from boardfarm_common.strategies.sdmux import SdMuxBootStrategy, SdMuxStatus
from boardfarm_common.strategies.tftp import TftpBootStrategy, TftpStatus

__all__ = [
    "BoardStrategy",
    "ExternalQemuStrategy",
    "FastbootFlashStrategy",
    "FastbootStatus",
    "QemuBootStrategy",
    "QemuStatus",
    "SdMuxBootStrategy",
    "SdMuxStatus",
    "TftpBootStrategy",
    "TftpStatus",
]
