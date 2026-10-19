"""Shared smoke tests for boards flashed over fastboot. Auto-skipped for boards
whose strategy isn't a FastbootFlashStrategy (see ``fastboot`` fixture in
``boardfarm_common.fixtures``).
"""

import os

from labgrid.driver import ExecutionError


def test_uname_a(fastboot):
    stdout = fastboot.run_check("/bin/uname -a", timeout=60.0)
    assert os.environ.get("VERSION") in stdout[0]


def test_buildinfo(fastboot):
    try:
        fastboot.run_check("cat /etc/buildinfo", timeout=60.0)
    except ExecutionError:
        fastboot.run("ls /etc/")
        raise
