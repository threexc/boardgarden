"""Shared TFTP boot smoke tests. Auto-skipped for boards whose strategy
isn't a TftpBootStrategy (see ``tftp`` fixture in ``boardfarm_common.fixtures``).
"""

import os

from labgrid.driver import ExecutionError


def test_tools_available(tftp):
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
