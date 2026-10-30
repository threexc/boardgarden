# Runners, secrets, and variables

## Runner labels

| Label | Used by | Requirements |
|---|---|---|
| `yocto-build` | `yocto-build-and-test`, `weekly-build-only` (via `build-yocto-image` + `deploy-to-tftp`) | Cores, RAM, storage, Docker, `/buildcache` bind-mount |
| `board-test` | `yocto-build-and-test` (via `run-board-tests`), `ptest-kvm-compare` | Docker, network route to the exporter/TFTP server |
| `light-maintenance` | `build-push-containers`, `lint`, `validate-manifests`, `renovate` | Docker, outbound to Forgejo + ghcr.io |

## Host containers

The registered Forgejo instance also acts as the container registry.

Images built by `build-push-containers.yaml`:

- `${BOARDGARDEN_HOST}/${BOARDGARDEN_OWNER}/yocto-builder`
- `${BOARDGARDEN_HOST}/${BOARDGARDEN_OWNER}/container-builder`
- `${BOARDGARDEN_HOST}/${BOARDGARDEN_OWNER}/lg-operator`

These are built weekly and on push to `.forgejo/dockerfiles/**`. First bootstrap
on a new instance requires manually running this workflow once (or seeding
images by push from a workstation).

## Repo variables

Set these in Settings → Actions → Variables.

| Variable | Example | Purpose |
|---|---|---|
| `BOARDGARDEN_HOST` | `forgejo.example.ts.net` | Hostname of the Forgejo container registry (no scheme) |
| `BOARDGARDEN_OWNER` | `tgamblin` | Owner/org of the `boardgarden`, `bitbake`, `openembedded-core`, `meta-riscv` mirrors |
| `LG_COORDINATOR_HOST` | `labgrid-coordinator.example.ts.net` | Hostname of the Labgrid coordinator, used as `LG_COORDINATOR`. Resolved on the `LG_PROXY` host, not the runner (see below) |
| `TFTP_SERVER_HOST` | `halifax` | Short hostname of the TFTP + report server. Used as `TFTP_SERVER`, rsync target, and left half of `--add-host`. Co-located with the Labgrid exporters on `halifax`, so it is also the host labgrid ssh's to for exporter access, and `LG_PROXY` |
| `TFTP_SERVER_IP` | `192.168.40.166` | LAN address for the TFTP server. Right half of `--add-host` |

## Repo secrets

Set these in Settings → Actions → Secrets.

| Secret | Used by | What it is |
|---|---|---|
| `LG_EXPORTER_SSH_KEY` | `run-board-tests` | Private key granting the runner login as `labgrid@` on the exporter host (`halifax`) |
| `REGISTRY_TOKEN` | `build-push-containers` | Forgejo container registry token (paired with `REGISTRY_USERNAME`) |
| `REGISTRY_USERNAME` | `build-push-containers` | Forgejo user or bot with `write:package` scope |
| `RENOVATE_TOKEN` | `renovate` | Forgejo bot PAT with `read:repository`, `write:repository`, `write:issue` |
| `REPORT_SSH_KEY` | `run-board-tests` | Private key for `reporter@halifax`. rsync of `report.html` to `/testresults/` |
| `SSH_KNOWN_HOSTS` | `deploy-to-tftp` (via `setup-ssh`), `run-board-tests` | Multi-line known_hosts covering every host the runner will ssh to (TFTP server, report server, Labgrid exporter host — all `halifax` today; the coordinator needs no ssh). Seed with `ssh-keyscan -H -T 10 <host>` |
| `TFTP_SERVER_SSH_KEY` | `deploy-to-tftp` → `setup-ssh`; `run-board-tests` | Private key for `auto@halifax`. rsync build artifacts into `/srv/tftp/<board>/` |

## Container `--add-host` mappings

Workflows that run inside containers inject `/etc/hosts` entries so the
container can reach the Labgrid coordinator / TFTP server on the private
network. Composed from the repo variables above:

```
--add-host ${TFTP_SERVER_HOST}:${TFTP_SERVER_IP}
```

## Coordinator access via `LG_PROXY`

Board-test containers set `LG_PROXY` to the exporter host, so
`labgrid-client` tunnels its coordinator connection over the same
`labgrid@` ssh login it already uses for exporter resources. Runners never
connect to the coordinator directly; only the exporter host needs to
resolve and reach `LG_COORDINATOR_HOST` (gRPC, port 20408). The `labgrid`
user's sshd config and `authorized_keys` entry on the exporter host must
allow TCP forwarding.

## SSH_KNOWN_HOSTS

`SSH_KNOWN_HOSTS` is the most-touched secret when re-deploying: any change
to the TFTP server / report server / exporter (new host key = new server or
regenerated `/etc/ssh/ssh_host_*_key`) invalidates it, and workflows fail
with `Host key verification failed`.

Regenerate contents:

```bash
{
  ssh-keyscan -H -T 10 <TFTP_SERVER_HOST>
} > known_hosts.new
```

## Buildcache and UIDs/GIDs

`build-yocto-image` (via `yocto-build-and-test` / `weekly-build-only`) and the other `yocto-build` jobs bind-mount
`/buildcache` into the container at the same path, populating
`DL_DIR` and `SSTATE_DIR`. Provision this on the runner host:

```
sudo install -d -o 1500 -g 1500 /buildcache/{downloads,sstate-cache}
```

`1500` is the default UID/GID for the custom containers from
`.forgejo/dockerfiles`.
