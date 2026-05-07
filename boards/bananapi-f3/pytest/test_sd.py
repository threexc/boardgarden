import json
import pytest
import re
import os

from labgrid.driver import ExecutionError

# check for everything in the typical Yocto 'core-image-minimal' version of
# busybox (as of May 07th, 2026), except for the '[' and '[[' shell builtins
BUSYBOX_TOOLS = [
    "addgroup", "adduser", "ascii", "ash", "awk", "base32", "basename", "blkid",
    "bunzip2", "bzcat", "bzip2", "cat", "chattr", "chgrp", "chmod", "chown",
    "chroot", "chvt", "clear", "cmp", "cp", "cpio", "crc32", "cut", "date",
    "dc", "dd", "deallocvt", "delgroup", "deluser", "depmod", "df", "diff",
    "dirname", "dmesg", "dnsdomainname", "du", "dumpkmap", "dumpleases", "echo",
    "egrep", "env", "expr", "false", "fbset", "fdisk", "fgrep", "find", "flock",
    "free", "fsck", "fstrim", "fuser", "getfattr", "getopt", "getty", "grep",
    "groups", "gunzip", "gzip", "head", "hexdump", "hostname", "hwclock", "id",
    "ifdown", "ifup", "insmod", "ip", "kill", "killall", "klogd", "less", "ln",
    "loadfont", "loadkmap", "logger", "logname", "logread", "losetup", "ls",
    "lsmod", "lzcat", "md5sum", "mesg", "microcom", "mkdir", "mkdosfs",
    "mkfifo", "mkfs.vfat", "mknod", "mkswap", "mktemp", "modprobe", "more",
    "mount", "mountpoint", "mv", "nc", "nohup", "nproc", "nslookup", "od",
    "openvt", "patch", "pgrep", "pidof", "pivot_root", "printf", "ps", "pwd",
    "rdate", "readlink", "realpath", "reboot", "renice", "reset", "resize",
    "rev", "rfkill", "rm", "rmdir", "rmmod", "run-parts", "sed", "seq",
    "setconsole", "setsid", "sh", "sha1sum", "sha256sum", "shuf", "sleep",
    "sort", "start-stop-daemon", "stat", "strings", "stty", "sulogin",
    "swapoff", "swapon", "switch_root", "sync", "sysctl", "syslogd", "tail",
    "tar", "tee", "telnet", "test", "tftp", "time", "top", "touch", "tr",
    "true", "ts", "tty", "udhcpc", "udhcpd", "umount", "uname", "uniq",
    "unlink", "unzip", "uptime", "users", "usleep", "vi", "watch", "wc", "wget",
    "which", "who", "whoami", "xargs", "xzcat", "yes", "zcat",
]

def test_uname_a(sd):
    version = os.environ.get("VERSION")
    try:
        state = sd.run_check('/bin/uname -a', timeout=60.0)

        assert(version in state[0])
    except ExecutionError:
        sd.run('ls /bin/uname')
        raise

def test_busybox_tools_available(sd):
    missing = []
    for tool in BUSYBOX_TOOLS:
        stdout, stderr, code = sd.run(
            f"test -x /bin/{tool} || test -x /usr/bin/{tool} || test -x /sbin/{tool} || test -x /usr/sbin/{tool}"
        )
        if code != 0:
            missing.append(tool)
    assert missing == [], f"Missing busybox tools: {missing}"
