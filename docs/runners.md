# Runners, secrets, and variables

## Runner labels

| Label | Used by | Requirements |
|---|---|---|
| `tgamblin-build` | `nightly-build-and-test`, `weekly-build-only` (via `build-yocto-image` + `deploy-to-tftp`) | Cores, RAM, storage, Docker, `/auto/runner/buildcache` bind-mount |
| `tgamblin-qemu` | `riscv-ptest-nightly` | Same as `tgamblin-build`; runs QEMU |
| `tgamblin-board-test` | `nightly-build-and-test` (via `run-board-tests`) | Docker, network route to Labgrid coordinator + TFTP server |
| `tgamblin-maintenance` | `meta-riscv-check-layer`, `build-push-containers`, `lint`, `validate-manifests`, `renovate` | Docker, outbound to Forgejo + ghcr.io |

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
| `LG_COORDINATOR_HOST` | `ecogrid` | Short hostname of the Labgrid coordinator (also the exporter host). Used as `LG_COORDINATOR`, ssh target, and left half of `--add-host` |
| `LG_COORDINATOR_IP` | `192.168.40.101` | LAN address for the coordinator. Right half of `--add-host` |
| `TFTP_SERVER_HOST` | `ecovault` | Short hostname of the TFTP + report server. Used as `TFTP_SERVER`, rsync target, and left half of `--add-host` |
| `TFTP_SERVER_IP` | `192.168.40.134` | LAN address for the TFTP server. Right half of `--add-host` |

## Repo secrets

Set these in Settings → Actions → Secrets.

| Secret | Used by | What it is |
|---|---|---|
| `LG_EXPORTER_SSH_KEY` | `run-board-tests` | Private key granting the runner login as `labgrid@` on the exporter host (`ecogrid`) |
| `REGISTRY_TOKEN` | `build-push-containers` | Forgejo container registry token (paired with `REGISTRY_USERNAME`) |
| `REGISTRY_USERNAME` | `build-push-containers` | Forgejo user or bot with `write:package` scope |
| `RENOVATE_TOKEN` | `renovate` | Forgejo bot PAT with `read:repository`, `write:repository`, `write:issue` |
| `REPORT_SSH_KEY` | `run-board-tests`, `riscv-ptest-nightly` | Private key for `reporter@ecovault`. rsync of `report.html` to `/testresults/` |
| `SSH_KNOWN_HOSTS` | `deploy-to-tftp` (via `setup-ssh`), `run-board-tests` | Multi-line known_hosts covering every host the runner will ssh to (TFTP server, report server, LG coordinator). Seed with `ssh-keyscan -H -T 10 <host>` |
| `TFTP_SERVER_SSH_KEY` | `deploy-to-tftp` → `setup-ssh`; `run-board-tests` | Private key for `auto@ecovault`. rsync build artifacts into `/srv/tftp/<board>/` |

## Container `--add-host` mappings

Workflows that run inside containers inject `/etc/hosts` entries so the
container can reach the Labgrid coordinator / TFTP server on the private
network. Composed from the repo variables above:

```
--add-host ${LG_COORDINATOR_HOST}:${LG_COORDINATOR_IP}
--add-host ${TFTP_SERVER_HOST}:${TFTP_SERVER_IP}
```

## SSH_KNOWN_HOSTS

`SSH_KNOWN_HOSTS` is the most-touched secret when re-deploying: any change
to the TFTP server / report server / exporter (new host key = new server or
regenerated `/etc/ssh/ssh_host_*_key`) invalidates it, and workflows fail
with `Host key verification failed`.

Regenerate contents:

```bash
{
  ssh-keyscan -H -T 10 <TFTP_SERVER_HOST>
  ssh-keyscan -H -T 10 <LG_COORDINATOR_HOST>
} > known_hosts.new
```

## Buildcache and UIDs/GIDs

`build-yocto-image` (via `nightly-build-and-test` / `weekly-build-only`) and `riscv-ptest-nightly` bind-mount
`/auto/runner/buildcache` into the container as `/buildcache`, populating
`DL_DIR` and `SSTATE_DIR`. Provision this on the runner host:

```
sudo install -d -o 1500 -g 1500 /auto/runner/buildcache/{downloads,sstate-cache}
```

`1500` is the default UID/GID for the custom containers from
`.forgejo/dockerfiles`.
