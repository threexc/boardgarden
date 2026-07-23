"""Shared TFTP boot smoke tests. Auto-skipped for boards whose strategy
isn't a TftpBootStrategy (see ``tftp`` fixture in ``boardfarm_common.fixtures``).
"""

import os

import pytest
from labgrid.driver import ExecutionError


def _is_initramfs(strategy) -> bool:
    """True if this board's manifest boots a bare initramfs rather than a
    full rootfs (see ``tftp.initramfs`` in board.yaml)."""
    return "initramfs" in strategy.manifest.get("tftp", {})


def test_tools_available(tftp, strategy):
    if _is_initramfs(strategy):
        pytest.skip("initramfs boot: busybox-only environment, no /bin/bash expected")
    tools = ["/bin/bash", "/bin/ls"]
    missing = [t for t in tools if tftp.run(f"test -x {t}")[2] != 0]
    assert missing == []


def test_uname_a(tftp):
    version = os.environ.get("VERSION")
    try:
        state = tftp.run_check("/bin/uname -a", timeout=60.0)
        assert version in state[0]
    except ExecutionError:
        tftp.run("ls /bin/uname")
        raise
