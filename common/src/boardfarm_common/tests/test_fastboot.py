"""Shared smoke tests for boards flashed over fastboot. Auto-skipped for boards
whose strategy isn't a FastbootFlashStrategy (see ``fastboot`` fixture in
``boardfarm_common.fixtures``).
"""

import os


def test_uname_a(fastboot):
    stdout = fastboot.run_check("/bin/uname -a", timeout=60.0)
    assert os.environ.get("VERSION") in stdout[0]
