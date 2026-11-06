from boardfarm_common.helpers import kernel_version_in

UNAME_RC = "Linux (none) 7.4.0-rc1-00004-g55b82fc69e99 #1 SMP PREEMPT_DYNAMIC riscv64 GNU/Linux"


def test_kernel_version_in():
    assert kernel_version_in("7.4-rc1", UNAME_RC)
    assert kernel_version_in("7.4", "Linux k3 7.4.0 #1 SMP")
    assert kernel_version_in("6.18.3", "Linux k3 6.18.3-k3 #1 SMP")
    assert not kernel_version_in("7.4-rc2", UNAME_RC)
    assert not kernel_version_in("7.3", UNAME_RC)
