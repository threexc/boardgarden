# ansible

Provisioning for boardgarden's container hosts. So far this only covers the
**testresults file server** (nginx serving `/testresults` over HTTP), since it
has no live dependents and is the lowest-risk place to prove out the container +
Ansible mechanics.

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
cp inventory.example.ini inventory.ini   # edit to point at your host(s)
ansible-playbook playbooks/site.yml --ask-become-pass -e testresults_nginx_port=<port_number>
```

Requires the `reporter` system user and `/testresults` directory to already
exist on the target host (same ones used by the bare-metal report upload
path documented in [docs/runners.md](../docs/runners.md)). This role reads
that user's UID/GID rather than creating a new one, so existing SSH keys and
file ownership stay valid.

## Layout

- `roles/container_host/` installs Podman, deploys the Quadlet unit +
  nginx config, enables the service.
- `roles/container_host/files/compose/` provides static Docker/podman-compose
  fallback (not applied by this playbook).
