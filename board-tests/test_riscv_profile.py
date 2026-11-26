"""RISC-V extension/profile checks for testv-profile-test images (meta-testv),
using riscv-ext-probe. Run by run-board-tests when the image is
testv-profile-test.

The profile a board should meet comes from ``riscv_profile`` in its board.yaml
(e.g. ``rva23u64``); boards without one only get the hwprobe consistency check.
"""

import pytest
from labgrid_boardkit.fixtures import _transition
from labgrid_boardkit.strategies import SdMuxBootStrategy, TftpBootStrategy

# User-mode profile mandatory extensions, by the names riscv-ext-probe knows.
# RV64GC isn't a profile, but is the baseline older SoCs claim: G = IMAFD_Zicsr_Zifencei.
RISCV64GC = {"i", "m", "a", "f", "d", "c", "zicsr", "zifencei"}
RVA20U64 = {
    "i", "m", "a", "f", "d", "c", "zicsr", "zicntr",
    "ziccif", "ziccrse", "ziccamoa", "za128rs", "zicclsm",
}  # fmt: skip
RVA22U64 = (RVA20U64 - {"za128rs"}) | {
    "za64rs", "zihpm", "zihintpause", "zba", "zbb", "zbs", "zic64b",
    "zicbom", "zicbop", "zicboz", "zfhmin", "zkt",
}  # fmt: skip
RVA23U64 = RVA22U64 | {
    "v", "zvfhmin", "zvbb", "zvkt", "zihintntl", "zicond", "zimop",
    "zcmop", "zcb", "zfa", "zawrs", "supm",
}  # fmt: skip
PROFILES = {
    "riscv64gc": RISCV64GC,
    "rva20u64": RVA20U64,
    "rva22u64": RVA22U64,
    "rva23u64": RVA23U64,
}


def _is_initramfs(strategy) -> bool:
    """As in labgrid_boardkit.tests.test_tftp: these boots never see the
    image's rootfs, only the initramfs."""
    tftp = strategy.manifest.get("tftp", {})
    return "initramfs" in tftp or tftp.get("kernel") == "fitImage"


@pytest.fixture(scope="module")
def probe_shell(strategy, target):
    if isinstance(strategy, TftpBootStrategy):
        state = "tftp"
    elif isinstance(strategy, SdMuxBootStrategy):
        state = "sd"
    else:
        state = "shell"  # fastboot, qemu
    shell = _transition(strategy, target, state)
    if shell.run("command -v riscv-ext-probe")[2] != 0:
        if _is_initramfs(strategy):
            pytest.skip(
                "initramfs boot without riscv-ext-probe: "
                "build with initramfs_image=testv-profile-test-initramfs"
            )
        pytest.fail("riscv-ext-probe not installed")
    # The kernel logs each probed SIGILL to the console, which splices into the
    # probe's output lines. The board is powered off after the run anyway.
    shell.run_check("dmesg -n 1")
    return shell


def _parse(lines):
    """'<ext> <status|0|1> [detail...]' lines -> {ext: rest of line}"""
    return {ext: rest for ext, _, rest in (line.partition(" ") for line in lines if line)}


@pytest.fixture(scope="module")
def probed(probe_shell):
    # Exits 1 when any extension fails, which is expected on most CPUs.
    out, _, _ = probe_shell.run("riscv-ext-probe", timeout=300)
    return _parse(out)


@pytest.fixture(scope="module")
def hwprobe(probe_shell):
    out = probe_shell.run_check("riscv-ext-probe --hwprobe", timeout=60)
    return _parse(line.removeprefix("ext ") for line in out if line.startswith("ext "))


def test_hwprobe_extensions_work(probed, hwprobe):
    """Everything the kernel reports through riscv_hwprobe(2) must execute."""
    advertised = {ext for ext, v in hwprobe.items() if v == "1" and ext in probed}
    broken = {
        ext: probed[ext] for ext in sorted(advertised) if probed[ext] not in ("ok", "untestable")
    }
    assert broken == {}


def test_profile(probed, strategy):
    profile = strategy.manifest.get("riscv_profile")
    if not profile:
        pytest.skip("board.yaml sets no riscv_profile")
    missing = {
        ext: probed.get(ext, "not probed")
        for ext in sorted(PROFILES[profile])
        if probed.get(ext) not in ("ok", "untestable")
    }
    assert missing == {}, f"{profile} extensions not supported"


if __name__ == "__main__":
    assert _parse(["v fail cpu1:SIGILL", "m ok", ""]) == {"v": "fail cpu1:SIGILL", "m": "ok"}
    assert RVA23U64 > RVA22U64 and "za128rs" not in RVA22U64
    print("ok")
