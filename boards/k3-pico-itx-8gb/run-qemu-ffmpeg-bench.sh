#!/bin/bash
# shellcheck disable=SC2029 # BOARD_DIR is meant to expand locally
# Boot each downloaded ffmpeg-bench-* build (stage-qemu-images artifacts), in
# random order, under the k3-pico-itx-8gb's qemu with KVM via
# boards/k3-pico-itx-8gb/qemu-guest.yaml (board set up by
# .forgejo/actions/k3-kvm-host), and run board-tests/test_ffmpeg_bench.py on
# it, writing logs/<build>/ and the run order to logs/order.txt. The board's
# rootfs only has room for a few images, so one build is staged at a time.
# Used by the ffmpeg-bench workflow; BENCH_ITERATIONS etc. pass through to the
# test.
set -uo pipefail

IMAGES=${IMAGES:-/home/labgrid/images}
# On the rootfs (where the image's extra space is), not tmpfs /var/tmp.
BOARD_DIR=/home/root/ffmpeg-bench
export LG_QEMU_DIR=$BOARD_DIR
# KVM provides SBI itself; see qemu-guest.yaml for the irqchip choice.
export LG_QEMU_ACCEL="-accel kvm,kernel-irqchip=split -cpu host"
export LG_QEMU_SMP=${LG_QEMU_SMP:-2} LG_QEMU_MEMORY=${LG_QEMU_MEMORY:-2048}

if ! ssh kvm-host 'test -w /dev/kvm'; then
  echo "::error::/dev/kvm not usable on the board"
  exit 1
fi

mkdir -p logs
for d in "$IMAGES"/ffmpeg-bench-*/; do
  [ -d "$d" ] && basename "$d"
done | shuf > logs/order.txt
echo "run order: $(paste -sd' ' logs/order.txt)"

failed=0
# Not a while-read loop: ssh would eat its stdin.
mapfile -t order < logs/order.txt
for build in "${order[@]}"; do
  out="logs/${build}"
  mkdir -p "$out"
  echo "::group::${build}"
  if ! { ssh kvm-host "rm -rf ${BOARD_DIR} && mkdir -p ${BOARD_DIR}" &&
    scp -q "${IMAGES}/${build}"/* "kvm-host:${BOARD_DIR}/"; }; then
    echo "::error::staging ${build} failed"
    touch "${out}/stage-failed"
    failed=1
    echo "::endgroup::"
    continue
  fi
  BENCH_JSON="${out}/bench.json" BENCH_LABEL="${build#ffmpeg-bench-}" uv run pytest -vv \
    --lg-env boards/k3-pico-itx-8gb/qemu-guest.yaml \
    --lg-log "$out" \
    --junitxml "${out}/junit.xml" \
    board-tests/test_ffmpeg_bench.py 2>&1 | tee "${out}/pytest.log" || failed=1
  # Never leave a guest running into the next build's run.
  ssh kvm-host "pkill -f qemu-system-riscv64; rm -rf ${BOARD_DIR}" || true
  echo "::endgroup::"
done
exit $failed
