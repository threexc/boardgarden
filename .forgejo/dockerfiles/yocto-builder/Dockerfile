FROM debian:13

ARG TARGETPLATFORM
ARG USER_UID=1500
ARG USER_GID=1500

# Install Yocto dependencies
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
    build-essential \
    chrpath \
    cpio \
    curl \
    debianutils \
    diffstat \
    file \
    gawk \
    gcc \
    git \
    iproute2 \
    iputils-ping \
    libacl1 \
    locales \
    lz4 \
    pcre2-utils \
    pylint \
    python3 \
    python3-git \
    python3-jinja2 \
    python3-pexpect \
    python3-pip \
    python3-subunit \
    python3-venv \
    rsync \
    screen \
    socat \
    sysstat \
    subversion \
    texinfo \
    tmux \
    tftp-hpa \
    u-boot-tools \
    unzip \
    wget \
    xz-utils \
    zstd && \
    case ${TARGETPLATFORM} in \
        "linux/amd64") \
	    DEBIAN_FRONTEND=noninteractive apt-get install -y \
	        gcc-multilib \
		g++-multilib \
	    ;; \
    esac && \
    groupadd -g $USER_GID yoctouser && \
    useradd -m -u $USER_GID -g $USER_GID -s /bin/bash yoctouser && \
    echo 'en_US.UTF-8 UTF-8' >> /etc/locale.gen && \
    locale-gen

RUN apt-get clean

# JS actions (e.g. astral-sh/setup-uv v7+) run on node24; Debian 13 ships node 20
COPY --from=node:24-trixie-slim /usr/local/bin/node /usr/local/bin/node

USER yoctouser
WORKDIR /home/yoctouser/yocto-build
