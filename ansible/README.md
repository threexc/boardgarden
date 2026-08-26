# ansible

Provisioning for boardgarden's container hosts. So far this covers:

- the **testresults file server** (nginx serving `/testresults` over HTTP) —
  no live dependents, lowest-risk place to prove out the container + Ansible
  mechanics.
- **tftpd-hpa** — live in CI (`deploy-to-tftp`, `run-board-tests`), built
  locally on the target from a thin custom image since no maintained
  upstream tftpd-hpa image exists. Entrypoint flags
  (`--secure --user tftp --address :69`) assume the stock Debian
  `/etc/default/tftpd-hpa` defaults from the ecovault → ecogrid migration —
  diff against the real file on ecogrid before relying on this in
  production.

## Why Podman + Quadlet

Rootless-friendly, no daemon, and integrates with systemd the same way
[systemd_services](../systemd_services) already manages the Labgrid
coordinator/exporter. Enable it with `systemctl enable --now`. Podman generates
the actual `.service` unit from the `.container` Quadlet file at boot /
`daemon-reload` time.

The Quadlet unit is installed system-wide under `/etc/containers/systemd/` and
managed by the system systemd instance. The container process itself still runs
as an unprivileged UID inside its own user namespace (`User=` in the Quadlet
unit), matching the existing assumptions about the `reporter` system user that
already owns `/testresults`.

## Docker / non-Ansible compatibility

Everything here targets Podman via Ansible, but the actual container image
and volume layout aren't Podman-specific. For a host you're managing by hand
(or with Docker instead of Podman), use the plain Compose file and nginx
config under
[`roles/container_host/files/compose/`](roles/container_host/files/compose/)
directly — see the usage comment at the top of
`testresults-nginx.compose.yaml`.

## Usage

```bash
ansible-galaxy collection install -r requirements.yml   # containers.podman, for building the tftpd-hpa image
cp inventory.example.ini inventory.ini                  # edit to point at your host(s)
ansible-playbook playbooks/site.yml --ask-become-pass -e container_host_testresults_nginx_port=<port_number>
```

Requires the `reporter` and `tftp` system users, and the `/testresults` and
`/srv/tftp` directories, to already exist on the target host (same ones used
by the bare-metal report/TFTP paths documented in
[docs/runners.md](../docs/runners.md)). This role reads those users'
UID/GID rather than creating new ones, so existing SSH keys and file
ownership stay valid.

## Layout

- `roles/container_host/` installs Podman, builds/deploys each service's
  Quadlet unit, enables the service. Tasks are split one file per service
  (`tasks/testresults.yml`, `tasks/tftpd-hpa.yml`) since more services
  (Labgrid coordinator, Forgejo) are still coming.
- `roles/container_host/files/compose/` provides static Docker/podman-compose
  fallback (not applied by this playbook).
- All role variables are prefixed `container_host_` (ansible-lint
  `var-naming[no-role-prefix]`).
