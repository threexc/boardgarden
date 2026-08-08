FROM debian:13

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    iproute2 \
    locales \
    netcat-openbsd \
    nodejs \
    openssh-client \
    ovmf \
    pkg-config \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    qemu-system-x86 \
    qemu-system-riscv \
    qemu-utils \
    rsync \
    socat \
    tftp-hpa \
    unzip \
    xz-utils \
    && rm -rf /var/lib/apt/lists/*

# Set locale (important for some Yocto operations)
#RUN locale-gen en_US.UTF-8
RUN echo 'en_US.UTF-8 UTF-8' >> /etc/locale.gen && locale-gen

# Create a non-root user (optional, but recommended)
ARG USER_UID=1500
ARG USER_GID=1500
RUN groupadd -g $USER_GID labgrid && useradd -m -u $USER_UID -g $USER_GID -s /bin/bash labgrid

RUN mkdir -p /opt/hostedtoolcache && chown -R $USER_UID:$USER_GID /opt/hostedtoolcache

USER labgrid
WORKDIR /home/labgrid
