"""Registry lookup for strategy families.

Strategies are registered as ``boardfarm.strategies`` entry points in
``pyproject.toml``. Third-party packages can add families the same way.
"""

from importlib.metadata import entry_points


class UnknownStrategy(KeyError):
    pass


def available_strategies() -> dict[str, str]:
    """Return {family_name: dotted-path} for every registered strategy."""
    return {ep.name: ep.value for ep in entry_points(group="boardfarm.strategies")}


def strategy_for(manifest: dict):
    """Look up a strategy class by ``manifest['strategy']``."""
    name = manifest.get("strategy")
    if not name:
        raise UnknownStrategy("board.yaml is missing top-level 'strategy: <family>' key")
    eps = {ep.name: ep for ep in entry_points(group="boardfarm.strategies")}
    if name not in eps:
        raise UnknownStrategy(f"strategy {name!r} not registered (available: {sorted(eps)})")
    return eps[name].load()
