FROM debian:13

ARG USER_UID=1500
ARG USER_GID=1500

# QEMU build and test dependencies. The cross compilers let check-tcg build
# guest test binaries for those targets; targets without one are skipped.
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
    bison \
    build-essential \
    bzip2 \
    ca-certificates \
    cpio \
    flex \
    gcc-aarch64-linux-gnu \
    gcc-riscv64-linux-gnu \
    git \
    libfdt-dev \
    libglib2.0-dev \
    libpixman-1-dev \
    libslirp-dev \
    locales \
    meson \
    ninja-build \
    pkg-config \
    python3 \
    python3-venv \
    xz-utils \
    zlib1g-dev \
    zstd && \
    groupadd -g $USER_GID qemuuser && \
    useradd -m -u $USER_UID -g $USER_GID -s /bin/bash qemuuser && \
    echo 'en_US.UTF-8 UTF-8' >> /etc/locale.gen && \
    locale-gen

RUN apt-get clean

USER qemuuser
WORKDIR /home/qemuuser/qemu-build
