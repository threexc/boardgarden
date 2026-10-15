#!/bin/bash
# Boot every staged ptest image under the board's qemu-system-riscv64 in one
# mode (kvm or tcg) via qemu-ptest.yaml, writing logs/<pkg>/<mode>/.
# Used by the ptest-kvm-compare workflow; expects BOARD_DIR, TCG_CPU,
# LG_QEMU_SMP, LG_QEMU_MEMORY and PTEST_TIMEOUT in the environment.
set -uo pipefail

mode=$1
case "$mode" in
  # KVM provides SBI itself, so no OpenSBI. irqchip/AIA constraints are
  # explained in qemu-ptest.yaml.
  kvm) export LG_QEMU_ACCEL="-accel kvm,kernel-irqchip=split -cpu host" ;;
  tcg) export LG_QEMU_ACCEL="-accel tcg -cpu ${TCG_CPU} -bios fw_jump.elf" ;;
  *) echo "usage: $0 kvm|tcg" >&2; exit 2 ;;
esac

if [ "$mode" = kvm ] && ! ssh ptest-board 'test -w /dev/kvm'; then
  echo "::error::/dev/kvm not usable on the board"
  exit 1
fi

failed=0
# shellcheck disable=SC2029 # BOARD_DIR is meant to expand locally
for dir in $(ssh ptest-board "ls -d ${BOARD_DIR}/*/"); do
  pkg=$(basename "$dir")
  export LG_QEMU_DIR="${BOARD_DIR}/${pkg}"
  out="logs/${pkg}/${mode}"
  mkdir -p "$out"
  echo "::group::${pkg} (${mode})"
  uv run pytest -vv \
    --lg-env boards/k3-pico-itx-8gb/qemu-ptest.yaml \
    --lg-log "$out" \
    --junitxml "$out/junit.xml" \
    common/src/boardfarm_common/ptest 2>&1 | tee "$out/pytest.log" || failed=1
  # Belt and braces: never leave a guest running into the next run.
  ssh ptest-board 'pkill -f qemu-system-riscv64' || true
  echo "::endgroup::"
done
exit $failed
