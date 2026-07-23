import pytest
from boardfarm_common.loader import UnknownStrategy, available_strategies, strategy_for
from boardfarm_common.strategies.qemu import QemuBootStrategy
from boardfarm_common.strategies.sdmux import SdMuxBootStrategy
from boardfarm_common.strategies.tftp import TftpBootStrategy


def test_available_strategies_lists_builtin_families():
    strategies = available_strategies()
    assert strategies["tftp"] == "boardfarm_common.strategies.tftp:TftpBootStrategy"
    assert strategies["sdmux"] == "boardfarm_common.strategies.sdmux:SdMuxBootStrategy"
    assert strategies["qemu"] == "boardfarm_common.strategies.qemu:QemuBootStrategy"


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("tftp", TftpBootStrategy),
        ("sdmux", SdMuxBootStrategy),
        ("qemu", QemuBootStrategy),
    ],
)
def test_strategy_for_resolves_registered_families(name, expected):
    assert strategy_for({"strategy": name}) is expected


def test_strategy_for_missing_key_raises():
    with pytest.raises(UnknownStrategy, match="missing"):
        strategy_for({})


def test_strategy_for_unregistered_name_raises():
    with pytest.raises(UnknownStrategy, match="not registered"):
        strategy_for({"strategy": "does-not-exist"})
