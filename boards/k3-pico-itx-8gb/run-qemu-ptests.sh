#!/bin/bash
# shellcheck disable=SC2029 # BOARD_DIR is meant to expand locally
# Boot every downloaded ptest image under the board's qemu-system-riscv64 via
# qemu-ptest.yaml, in random order, with KVM (and then TCG if TCG=true),
# writing logs/<pkg>/<mode>/ and the run order to logs/order.txt.
# The board's rootfs only has room for about one ptest image, so each is
# staged just before its runs and removed right after.
# Used by the ptest-kvm-compare workflow; expects BOARD_DIR, LG_QEMU_SMP,
# LG_QEMU_MEMORY and PTEST_TIMEOUT (optionally IMAGES, TCG, TCG_CPU and
# PTEST_RUNNER_TIMEOUT) in the environment.
set -uo pipefail

IMAGES=${IMAGES:-/home/labgrid/images}
modes=kvm
[ "${TCG:-false}" = true ] && modes="kvm tcg"

if ! ssh ptest-board 'test -w /dev/kvm'; then
  echo "::error::/dev/kvm not usable on the board"
  ssh ptest-board 'id; ls -l /dev/kvm; lsmod | grep -w kvm || echo "kvm module not loaded"' || true
  exit 1
fi

mkdir -p logs
for d in "$IMAGES"/ptest_image_*/; do
  [ -d "$d" ] && basename "$d" | sed 's/^ptest_image_//'
done | shuf > logs/order.txt
echo "run order: $(paste -sd' ' logs/order.txt)"

failed=0
mapfile -t order < logs/order.txt
for pkg in "${order[@]}"; do
  export LG_QEMU_DIR="${BOARD_DIR}/${pkg}"
  mkdir -p "logs/${pkg}"
  echo "::group::stage ${pkg}"
  ssh ptest-board "rm -rf ${BOARD_DIR} && mkdir -p ${LG_QEMU_DIR} && df -h ${BOARD_DIR}"
  if ! scp -q "${IMAGES}/ptest_image_${pkg}"/* "ptest-board:${LG_QEMU_DIR}/"; then
    echo "::error::staging ${pkg} on the board failed"
    touch "logs/${pkg}/stage-failed"
    failed=1
    echo "::endgroup::"
    continue
  fi
  echo "::endgroup::"

  for mode in $modes; do
    case "$mode" in
      # KVM provides SBI itself, so no OpenSBI. irqchip/AIA constraints are
      # explained in qemu-ptest.yaml.
      kvm) export LG_QEMU_ACCEL="-accel kvm,kernel-irqchip=split -cpu host" ;;
      tcg) export LG_QEMU_ACCEL="-accel tcg -cpu ${TCG_CPU:-max} -bios fw_jump.elf" ;;
    esac
    out="logs/${pkg}/${mode}"
    mkdir -p "$out"
    echo "::group::${pkg} (${mode})"
    # ShellDriver.run() prints nothing until ptest-runner exits; follow the
    # guest console (written live by --lg-log) so progress shows in the job log.
    tail -F -n +1 "$out/console_main" 2>/dev/null &
    tail_pid=$!
    uv run pytest -vv \
      --lg-env boards/k3-pico-itx-8gb/qemu-ptest.yaml \
      --lg-log "$out" \
      --junitxml "$out/junit.xml" \
      common/src/boardfarm_common/ptest 2>&1 | tee "$out/pytest.log" || failed=1
    kill "$tail_pid" 2>/dev/null
    # Belt and braces: never leave a guest running into the next run.
    ssh ptest-board 'pkill -f qemu-system-riscv64' || true
    echo "::endgroup::"
  done

  ssh ptest-board "rm -rf ${BOARD_DIR}"
done
exit $failed
