FROM debian:13-slim

ARG TFTP_UID=1500
ARG TFTP_GID=1500

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        tftpd-hpa && \
    rm -rf /var/lib/apt/lists/* && \
    usermod -u "${TFTP_UID}" tftp && \
    groupmod -g "${TFTP_GID}" tftp

# --secure chroots into the trailing directory arg, then --user drops
# privileges post-chroot — matches the package's own default
# /etc/default/tftpd-hpa behavior (TFTP_OPTIONS="--secure"). Runs as root
# so chroot(2)/setuid(2) succeed; drops to the tftp user itself.
ENTRYPOINT ["/usr/sbin/in.tftpd", "--foreground", "--address", ":69", "--secure", "--user", "tftp", "/srv/tftp"]
