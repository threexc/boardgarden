"""Unit tests for the strategy state machines (transition/force graphs) in
boardfarm_common.strategies. These exercise the pure decision logic with a
fake labgrid Target that just records activate()/deactivate() calls, so no
real hardware, serial console, or labgrid environment file is needed.
"""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from boardfarm_common.strategies.qemu import QemuBootStrategy, QemuStatus
from boardfarm_common.strategies.sdmux import SdMuxBootStrategy, SdMuxStatus
from boardfarm_common.strategies.tftp import TftpBootStrategy, TftpStatus
from labgrid.strategy.common import StrategyError


class FakeTarget:
    """Stand-in for labgrid.Target: records activate/deactivate calls without
    resolving real bindings/drivers."""

    def __init__(self):
        self.name = "fake-target"
        self.activated = []
        self.deactivated = []
        self.env = SimpleNamespace(config=SimpleNamespace(get_images=lambda: {}))

    def bind(self, driver):
        driver.target = self

    def activate(self, driver):
        self.activated.append(driver)

    def deactivate(self, driver):
        self.deactivated.append(driver)


def _mock_drivers(strategy, *names):
    for name in names:
        setattr(strategy, name, Mock(name=name))


# ---- TftpBootStrategy ------------------------------------------------------


@pytest.fixture
def tftp_strategy():
    strategy = TftpBootStrategy(target=FakeTarget(), name="tftp-test")
    _mock_drivers(strategy, "power", "console", "uboot", "shell", "tftp")
    strategy.manifest = {
        "boot": {
            "bootargs": "console=ttyS0",
            "kernel_addr": "$kernel_addr_r",
            "dtb_addr": "$dtb_addr",
        },
        "tftp": {"subdir": "my-board", "kernel": "Image", "dtb": "my-board.dtb"},
    }
    return strategy


def test_tftp_force_states(tftp_strategy):
    tftp_strategy.force("off")
    assert tftp_strategy.status == TftpStatus.off
    assert tftp_strategy.target.activated == [tftp_strategy.power]

    tftp_strategy.force("uboot")
    assert tftp_strategy.status == TftpStatus.uboot
    assert tftp_strategy.target.activated[-1] is tftp_strategy.uboot

    tftp_strategy.force("tftp")
    assert tftp_strategy.status == TftpStatus.tftp
    assert tftp_strategy.target.activated[-1] is tftp_strategy.shell


def test_tftp_force_rejects_unknown(tftp_strategy):
    with pytest.raises(StrategyError):
        tftp_strategy.force("unknown")


def test_tftp_transition_to_uboot_stages_and_marks_staged(tftp_strategy):
    tftp_strategy.transition("uboot")

    assert tftp_strategy.status == TftpStatus.uboot
    assert tftp_strategy.staged is True
    tftp_strategy.power.cycle.assert_called_once()
    assert tftp_strategy.tftp in tftp_strategy.target.activated
    assert tftp_strategy.tftp in tftp_strategy.target.deactivated


def test_tftp_transition_to_tftp_sets_bootargs_and_boots(tftp_strategy):
    tftp_strategy.transition("tftp")

    assert tftp_strategy.status == TftpStatus.tftp
    tftp_strategy.uboot.run.assert_any_call("setenv bootargs console=ttyS0")
    tftp_strategy.uboot.run.assert_any_call("tftpboot $kernel_addr_r my-board/Image")
    tftp_strategy.uboot.run.assert_any_call("tftpboot $dtb_addr my-board/my-board.dtb")
    tftp_strategy.uboot.boot.assert_called_once_with("tftp")
    tftp_strategy.uboot.await_boot.assert_called_once()


def test_tftp_transition_same_status_is_a_noop(tftp_strategy):
    tftp_strategy.force("off")
    calls_before = len(tftp_strategy.target.activated)
    tftp_strategy.transition("off")
    assert len(tftp_strategy.target.activated) == calls_before


def test_tftp_transition_rejects_unknown(tftp_strategy):
    with pytest.raises(StrategyError):
        tftp_strategy.transition("unknown")


# ---- SdMuxBootStrategy ------------------------------------------------------


@pytest.fixture
def sdmux_strategy():
    strategy = SdMuxBootStrategy(target=FakeTarget(), name="sdmux-test")
    _mock_drivers(strategy, "power", "console", "shell", "sdmux", "sdcard")
    strategy.target.env.config.get_image_path = Mock(return_value="/tmp/image.wic.gz")
    return strategy


def test_sdmux_transition_to_flashed_writes_image_once(sdmux_strategy):
    sdmux_strategy.transition("flashed")

    assert sdmux_strategy.flashed is True
    sdmux_strategy.sdcard.write_image.assert_called_once()
    sdmux_strategy.sdmux.set_mode.assert_any_call("host")
    sdmux_strategy.sdmux.set_mode.assert_any_call("dut")

    # Booting to `sd` and asking for `flashed` again must not reflash.
    sdmux_strategy.transition("sd")
    sdmux_strategy.transition("flashed")
    sdmux_strategy.sdcard.write_image.assert_called_once()


def test_sdmux_transition_to_sd_boots(sdmux_strategy):
    sdmux_strategy.transition("sd")
    assert sdmux_strategy.status == SdMuxStatus.sd
    sdmux_strategy.power.cycle.assert_called_once()


def test_sdmux_force_rejects_unknown(sdmux_strategy):
    with pytest.raises(StrategyError):
        sdmux_strategy.force("unknown")


# ---- QemuBootStrategy -------------------------------------------------------


@pytest.fixture
def qemu_strategy():
    strategy = QemuBootStrategy(target=FakeTarget(), name="qemu-test")
    _mock_drivers(strategy, "qemu_driver", "shell")
    return strategy


def test_qemu_transition_to_shell_and_back_to_off(qemu_strategy):
    qemu_strategy.transition("shell")
    assert qemu_strategy.status == QemuStatus.shell
    qemu_strategy.qemu_driver.on.assert_called_once()

    qemu_strategy.transition("off")
    assert qemu_strategy.status == QemuStatus.off
    qemu_strategy.qemu_driver.off.assert_called_once()


def test_qemu_transition_to_shell_is_idempotent(qemu_strategy):
    qemu_strategy.transition("shell")
    qemu_strategy.transition("shell")
    qemu_strategy.qemu_driver.on.assert_called_once()


def test_qemu_transition_rejects_shell_directly_from_booting(qemu_strategy):
    qemu_strategy.status = QemuStatus.booting
    with pytest.raises(StrategyError, match="booting"):
        qemu_strategy.transition("shell")


def test_qemu_transition_rejects_status_with_no_handler(qemu_strategy):
    with pytest.raises(StrategyError):
        qemu_strategy.transition("unknown")
