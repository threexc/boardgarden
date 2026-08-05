# Helper functions for the boardfarm's test suites and strategies

default_bootargs = (
    "console=tty1 "
    "console=ttyS0,115200 "
    "consoleblank=0 "
    "earlycon=sbi "
    "fsck.fix=yes "
    "fsck.repair=yes "
    "loglevel=7 "
    "net.ifnames=0 "
    "no_console_suspend "
    "plymouth.ignore-serial-consoles "
    "rootwait "
    "rw "
    "splash "
    "systemd.journald.storage=volatile "
)

default_serverip = "192.168.40.101"


def uboot_stage(strategy):
    if strategy.staged:
        return
    strategy.target.activate(strategy.tftp)

    for name, image in strategy.target.env.config.get_images().items():
        if name.startswith("tftp-"):
            strategy.tftp.stage(image)

    strategy.target.deactivate(strategy.tftp)
    strategy.staged = True


def uboot_set_server_ip(strategy, serverip=default_serverip):
    strategy.uboot.run("setenv autoload no")
    strategy.uboot.run("dhcp", timeout=10)
    strategy.uboot.run(f"setenv serverip {serverip}")


def uboot_set_bootargs(strategy, bootargs=default_bootargs):
    strategy.uboot.run(f"setenv bootargs {bootargs}")


def uboot_tftpboot_file(strategy, loadaddr, board_name, file_name):
    strategy.uboot.run(f"tftpboot {loadaddr} {board_name}/{file_name}")
