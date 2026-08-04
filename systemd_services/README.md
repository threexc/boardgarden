# systemd services

Unit files for running the Labgrid coordinator and per-board exporters as
persistent system services. Install on whichever host(s) sit on the same
network as your boards (coordinator and exporters can share a host or be
split across several — see [docs/runners.md](../docs/runners.md) for how
these map to `LG_COORDINATOR_HOST`/`LG_COORDINATOR_IP` in CI).

## Files

- `labgrid-coordinator.service` — the coordinator. Run on one host.
- `labgrid-exporter@.service` — template unit, one instance per board. The
  instance name (`%i`) must match a `boards/<name>` directory, e.g.
  `boards/bananapi-f3` → `labgrid-exporter@bananapi-f3.service`.

Both assume a dedicated `labgrid` system user/group, in the `dialout` and
`plugdev` groups (adjust `SupplementaryGroups=` in the exporter unit for
your distro if device nodes use different groups), and a `boards/.venv`
already built via `uv sync` (see the top-level [README](../README.md#boards)).

## Configuration

Both units read `BOARDGARDEN_ROOT` (default `/home/labgrid/boardgarden`) to
locate the checkout and venv. Exporters also need `LG_COORDINATOR` set to
the coordinator's hostname. Override either by dropping a
`/etc/labgrid/boardgarden.env` file:

```
BOARDGARDEN_ROOT=/home/labgrid/boardgarden
LG_COORDINATOR=ecogrid
```

The file is optional (`EnvironmentFile=-...`) — omit it if the defaults
already match your layout.

## Install

```bash
sudo cp systemd_services/labgrid-coordinator.service systemd_services/labgrid-exporter@.service /etc/systemd/system/
sudo mkdir -p /etc/labgrid
sudo $EDITOR /etc/labgrid/boardgarden.env   # set LG_COORDINATOR at least
sudo systemctl daemon-reload

# on the coordinator host:
sudo systemctl enable --now labgrid-coordinator.service

# on each exporter host, one instance per board directory under boards/:
sudo systemctl enable --now labgrid-exporter@bananapi-f3.service
sudo systemctl enable --now labgrid-exporter@k3-pico-itx.service
sudo systemctl enable --now labgrid-exporter@muse-pi-pro.service
sudo systemctl enable --now labgrid-exporter@orangepi-rv2.service
```

Adding a new board later only needs a new `boards/<name>` directory plus
`systemctl enable --now labgrid-exporter@<name>.service` — no new unit file.
