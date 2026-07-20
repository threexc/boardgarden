FROM debian:13

ARG TARGETPLATFORM
ARG USER_UID=1500
ARG USER_GID=1500

# Install Linux Kernel dependencies
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
    bc \
    bison \
    build-essential \
    cpio \
    dwarves \
    fakeroot \
    flex \
    gcc-aarch64-linux-gnu \
    gcc-riscv64-linux-gnu \
    git \
    kmod \
    libelf-dev \
    libncurses-dev \
    libssl-dev \
    locales \
    rsync && \
    case ${TARGETPLATFORM} in \
        "linux/amd64") \
	    DEBIAN_FRONTEND=noninteractive apt-get install -y \
	        gcc-multilib \
		g++-multilib \
	    ;; \
    esac && \
    groupadd -g $USER_GID kerneluser && \
    useradd -m -u $USER_GID -g $USER_GID -s /bin/bash kerneluser && \
    echo 'en_US.UTF-8 UTF-8' >> /etc/locale.gen && \
    locale-gen

RUN apt-get clean

USER kerneluser
WORKDIR /home/kerneluser/kernel-build
