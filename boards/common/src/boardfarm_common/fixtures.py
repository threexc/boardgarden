"""pytest fixtures + hooks shared across all board test suites.

Auto-loaded via the ``pytest11`` entry point in
``boards/common/pyproject.toml``. No per-board conftest.py needed for these.
"""

import traceback
from pathlib import Path

import pytest


def pytest_configure(config):
    """Auto-set ``--lg-env`` to the ``client.yaml`` sibling of the test dir.

    Walks upward from each CLI arg until it finds a ``client.yaml`` (or
    ``env.yaml``) alongside a directory. Skips if the user already passed
    ``--lg-env`` explicitly.
    """
    if config.getoption("--lg-env", default=None):
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
    return _transition(strategy, target, "tftp")


@pytest.fixture(scope="module")
def sd(strategy, target):
    return _transition(strategy, target, "sd")


@pytest.fixture(scope="module")
def shell(strategy, target):
    """Generic shell fixture: transitions to the ``shell`` state (qemu)."""
    return _transition(strategy, target, "shell")
