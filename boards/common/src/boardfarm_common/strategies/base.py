from pathlib import Path

import attr

from labgrid.strategy.common import Strategy

from boardfarm_common.manifest import load_board


@attr.s(eq=False)
class BoardStrategy(Strategy):
    """Base for all boardfarm strategies.

    Two ways to attach a manifest to a strategy instance:

    1. **Per-board subclass** (default): the concrete subclass sets ``manifest``
       as a class attribute, typically ``manifest = load_board(Path(__file__).parent)``.

    2. **``manifest_path`` kwarg** (zero-Python boards): pass ``manifest_path``
       from labgrid ``client.yaml``. The base ``__attrs_post_init__`` loads it.
       Path is resolved absolute or relative to cwd.

    Family subclasses (tftp, sdmux, ...) must call ``super().__attrs_post_init__()``.
    """

    manifest_path = attr.ib(default=None)

    manifest: dict = {}

    def __attrs_post_init__(self):
        super().__attrs_post_init__()
        if self.manifest_path is not None:
            self.manifest = load_board(Path(self.manifest_path))
