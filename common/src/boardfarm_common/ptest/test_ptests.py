"""ptest-runner suite for any qemu board, e.g.

uv run pytest --lg-env boards/qemux86-64/env.yaml common/src/boardfarm_common/ptest
"""

import os


class TestPtests:
    def test_system_booted(self, shell):
        stdout, stderr, rc = shell.run("echo hello")
        assert rc == 0
        assert "hello" in stdout

    def test_kernel_version(self, shell):
        stdout, stderr, rc = shell.run("uname -r")
        assert rc == 0
        assert len(stdout) > 0
        print(f"Kernel version: {stdout[0]}")

    def test_ptests(self, shell):
        timeout = int(os.environ.get("PTEST_TIMEOUT", 1200))
        cmd = "ptest-runner"
        # ptest-runner kills a ptest silent for this long (its default: 300s)
        if runner_timeout := os.environ.get("PTEST_RUNNER_TIMEOUT"):
            cmd += f" -t {int(runner_timeout)}"
        stdout, stderr, rc = shell.run(cmd, timeout=timeout)
        assert rc == 0
