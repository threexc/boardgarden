# Onboarding a new board

This walks through adding a new board to boardgarden end-to-end: manifest,
strategy wiring, labgrid config, tests, exporter-side setup, and CI.

## 1. Pick a strategy family

| Family | Use when | Available in registry |
|---|---|---|
| `tftp`  | Physical board booted via U-Boot + TFTP | `TftpBootStrategy` |
| `sdmux` | Physical board booted from an SD card written through a USB SD-Mux | `SdMuxBootStrategy` |
| `qemu`  | Emulated target (Yocto image, no hardware) | `QemuBootStrategy` |

Adding a new family? See [Adding a strategy family](#adding-a-strategy-family)
at the end of this doc.

## 2. Create `boards/<name>/board.yaml`

`board.yaml` is the source of truth for the board. `client.yaml` /
`env.yaml` are generated from it (see step 4).

Minimum fields depend on the family — the JSON Schema
(`common/src/boardfarm_common/schema/board.schema.json`) enforces
this in CI.

### `tftp` example

```yaml
name: my-board
strategy: tftp
description: Vendor Foo, Widget-1
remote_place: bf-my-board
image_source: yocto
inherits:
  - ../families/spacemit-k1/defaults.yaml   # optional; drop if no matching family

boot:
  method: tftp
  bootargs: >
    console=ttyS0,115200n8 root=/dev/mmcblk0p2 rootwait rw

tftp:
  subdir: my-board
  dtb: my-board.dtb

uboot:
  tftp_cmd: booti $kernel_addr_r - $dtb_addr

shell:
  username: root
  password: null

strategy_class: MyBoardBootStrategy   # matches the class name in strategy.py
```

Fields inherited from `families/spacemit-k1/defaults.yaml`:
`arch`, `boot.kernel_addr`, `boot.dtb_addr`, `tftp.kernel`,
`uboot.emmc_cmd`, `uboot.prompt`, `uboot.autoboot`, `uboot.interrupt`.

If you're onboarding a board with a shared SoC/family, add a
`boards/families/<family>/defaults.yaml` first and inherit from it.

### `sdmux` example

```yaml
name: my-sdmux-board
strategy: sdmux
description: Vendor Bar, SBC-2 (SD boot via SD-Mux)
remote_place: bf-my-sdmux-board
arch: aarch64
image_source: yocto

image:
  label: sdimage
  path: /home/labgrid/my-sdmux-board.rootfs-latest.wic.gz

tools:
  usbsdmux: /home/labgrid/.local/bin/usbsdmux

shell:
  username: root
  password: null

strategy_class: MySdmuxBoardBootStrategy
```

### `qemu` example

See `boards/qemuriscv64/board.yaml`.

## 3. Add `boards/<name>/strategy.py`

Thin subclass that binds a labgrid-registered driver name to the shared
family class.

```python
from pathlib import Path

import attr

from labgrid.factory import target_factory

from boardfarm_common.manifest import load_board
from boardfarm_common.strategies import TftpBootStrategy


@target_factory.reg_driver
@attr.s(eq=False)
class MyBoardBootStrategy(TftpBootStrategy):
    """Boot strategy for My Board."""

    manifest = load_board(Path(__file__).parent)
```

Substitute `TftpBootStrategy` with `SdMuxBootStrategy` / `QemuBootStrategy`
for other families.

## 4. Render `client.yaml`

Do not hand-write `client.yaml`. Generate it from the manifest:

```
uv run boardfarm-render boards/my-board       # writes boards/my-board/client.yaml
```

CI runs `boardfarm-render --check` on every push. If someone edits
`client.yaml` by hand, CI fails. Change `board.yaml` (or the template) and
re-render.

Available templates live at
`common/src/boardfarm_common/templates/client-<family>.yaml.j2`.
Extend them there — not in per-board files.

## 5. Validate

```
uv run boardfarm-validate boards/my-board     # single board
uv run boardfarm-validate              # all boards
```

Errors point at the schema rule that failed. Fix the manifest, not the
schema (unless a genuinely new field is being introduced).

## 6. Add a pytest suite

Copy an existing board's `pytest/` directory as a starting point:

```
boards/my-board/pytest/
  conftest.py       # sets --lg-env to ../client.yaml, exposes tftp fixture
  pytest.ini        # (optional; global config is in pyproject.toml)
  test_tftp.py      # smoke tests
```

Run the suite locally against real hardware:

```
uv run pytest -vvv boards/my-board/pytest/
```

## 7. Exporter-side setup

- Add a systemd unit under `systemd_services/labgrid-exporter-<board>.service`
  (copy an existing one, change the export config file).
- Add udev rules under `udev/` if the board introduces new USB IDs; make
  sure serial + GPIO + power come up at predictable paths.
- Ensure the coordinator's config exports the RemotePlace named in
  `board.yaml`'s `remote_place:`.

## 8. Commit

Files that make up a new board:

```
boards/my-board/board.yaml
boards/my-board/strategy.py
boards/my-board/client.yaml        # generated
boards/my-board/pytest/conftest.py
boards/my-board/pytest/test_tftp.py
systemd_services/labgrid-exporter-my-board.service   # if physical
udev/50-my-board.rules                                # if new USB IDs
```

CI's `validate-manifests` workflow will re-check schema + template drift on
the PR.

## 9. Smoke test on hardware

```
uv run labgrid-client -p bf-my-board acquire
uv run pytest -vvv boards/my-board/pytest/
uv run labgrid-client -p bf-my-board release
```

---

## Adding a strategy family

Only needed if none of `tftp` / `sdmux` / `qemu` fit.

1. `common/src/boardfarm_common/strategies/<family>.py` — new class
   plus its own `Status` enum, subclass `BoardStrategy`.
2. Re-export from `common/src/boardfarm_common/strategies/__init__.py`.
3. Register the family in `common/pyproject.toml`:
   ```toml
   [project.entry-points."boardfarm.strategies"]
   <family> = "boardfarm_common.strategies.<family>:<ClassName>"
   ```
4. Extend `schema/board.schema.json`:
   - add `<family>` to the top-level `strategy` enum
   - add an `allOf/if-then` block declaring required fields for the family
5. Add `templates/client-<family>.yaml.j2`.
6. `docs/onboard-a-board.md` — extend the family table.

External packages register in the same entry-point group; no upstream edit
required to add a family from outside this repo.
