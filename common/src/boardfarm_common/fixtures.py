"""pytest fixtures + hooks shared across all board test suites.

Auto-loaded via the ``pytest11`` entry point in
``common/pyproject.toml``. No per-board conftest.py needed for these.
"""

import os
import traceback
from pathlib import Path

import pytest

from boardfarm_common.strategies.sdmux import SdMuxBootStrategy
from boardfarm_common.strategies.tftp import TftpBootStrategy


def pytest_configure(config):
    """Auto-set ``--lg-env``.

    Resolution order:
    1. Skip if user already passed ``--lg-env``.
    2. ``BOARD`` env var → ``$BOARD/client.yaml`` (or ``env.yaml``) rel to cwd.
    3. Walk upward from each CLI arg looking for ``client.yaml`` / ``env.yaml``.
    """
    if config.getoption("--lg-env", default=None):
        return

    board = os.environ.get("BOARD")
    if board:
        for candidate in (Path(board) / "client.yaml", Path(board) / "env.yaml"):
            if candidate.is_file():
                config.option.lg_env = str(candidate.resolve())
                return

    for arg in config.args:
        for p in Path(arg).resolve().parents:
            for candidate in (p / "client.yaml", p / "env.yaml"):
                if candidate.is_file():
                    config.option.lg_env = str(candidate)
                    return


def _transition(strategy, target, state: str):
    try:
        strategy.transition(state)
    except Exception as e:
        traceback.print_exc()
        pytest.exit(f"Transition into {state} boot shell failed: {e}", returncode=3)
    return target.get_driver("ShellDriver")


@pytest.fixture(scope="module")
def tftp(strategy, target):
    if not isinstance(strategy, TftpBootStrategy):
        pytest.skip("board does not use TFTP boot strategy")
    return _transition(strategy, target, "tftp")


@pytest.fixture(scope="module")
def sd(strategy, target):
    if not isinstance(strategy, SdMuxBootStrategy):
        pytest.skip("board does not use SD-mux boot strategy")
    return _transition(strategy, target, "sd")


@pytest.fixture(scope="module")
def shell(strategy, target):
    """Generic shell fixture: transitions to the ``shell`` state (qemu)."""
    return _transition(strategy, target, "shell")
