"""FFmpeg benchmarks for testv-image-ffmpeg-bench images (meta-testv), e.g.
built with different RISC-V tunes and compared by the ffmpeg-bench workflow.

Runs on any qemu env with a ``shell`` fixture, e.g.

uv run pytest --lg-env boards/qemuriscv64/env.yaml board-tests/test_ffmpeg_bench.py

Each benchmark runs ``BENCH_ITERATIONS`` times (default 3); the median of
ffmpeg -benchmark's utime/rtime is recorded as junit properties and written,
with the image's TUNE_FEATURES, to ``BENCH_JSON`` (default bench.json).
Everything runs with -threads 1, so results compare code generation rather
than how many vCPUs the guest got.
"""

import json
import os
import re
import statistics

import pytest

SAMPLES = "/usr/share/ffmpeg-bench"
# Synthetic sources: lavfi generates the input, so these include its cost.
TESTSRC = "-f lavfi -i testsrc2=size=1280x720:rate=25:duration=4"
# name: (input options, output options)
BENCHMARKS = {
    "decode-h264": (f"-i {SAMPLES}/h264-1440x1080.h264", ""),
    "decode-hevc": (f"-i {SAMPLES}/hevc-1920x1080.hevc", ""),
    "decode-vp9": (f"-i {SAMPLES}/vp9-852x480.webm", ""),
    "encode-mpeg4": (TESTSRC, "-c:v mpeg4"),
    "encode-ffv1": (TESTSRC, "-c:v ffv1"),
    "scale-bicubic": (TESTSRC, "-vf scale=1920x1080:flags=bicubic"),
    "encode-flac": ("-f lavfi -i sine=frequency=440:duration=120", "-c:a flac"),
}
BENCH = re.compile(r"bench: utime=([\d.]+)s stime=([\d.]+)s rtime=([\d.]+)s")


def _parse(lines):
    """ffmpeg -benchmark output -> (utime, rtime) in seconds"""
    for line in lines:
        if m := BENCH.search(line):
            return float(m[1]), float(m[3])
    raise ValueError("no 'bench:' line in ffmpeg output")


@pytest.fixture(scope="module")
def results():
    data = {"benchmarks": {}}
    yield data
    with open(os.environ.get("BENCH_JSON", "bench.json"), "w") as f:
        json.dump(data, f, indent=2)


def test_buildinfo(shell, results, record_property):
    """The tune the image was built with (testv's IMAGE_BUILDINFO_VARS), so
    results can't be credited to the wrong build."""
    out = shell.run_check("cat /etc/buildinfo")
    info = dict(
        (k.strip(), v.strip()) for k, sep, v in (line.partition("=") for line in out) if sep
    )
    results["buildinfo"] = info
    record_property("TUNE_FEATURES", info.get("TUNE_FEATURES", ""))
    print(f"TUNE_FEATURES: {info.get('TUNE_FEATURES')}")


@pytest.mark.parametrize("name", BENCHMARKS)
def test_bench(shell, results, record_property, name):
    iterations = int(os.environ.get("BENCH_ITERATIONS", 3))
    timeout = int(os.environ.get("BENCH_TIMEOUT", 1800))
    inp, out = BENCHMARKS[name]
    # -threads is per input/output, so it goes on both sides.
    cmd = (
        f"ffmpeg -nostdin -hide_banner -nostats -benchmark -threads 1 {inp}"
        f" -threads 1 -filter_threads 1 {out} -f null -"
    )
    # Only the bench: line on success, the log's tail on failure.
    cmd = f"{cmd} >/tmp/ff.log 2>&1 && grep '^bench:' /tmp/ff.log || {{ tail -20 /tmp/ff.log; false; }}"
    runs = [_parse(shell.run_check(cmd, timeout=timeout)) for _ in range(iterations)]
    utime = statistics.median(u for u, _ in runs)
    rtime = statistics.median(r for _, r in runs)
    results["benchmarks"][name] = {"utime": utime, "rtime": rtime, "runs": runs}
    record_property("utime", utime)
    record_property("rtime", rtime)
    print(f"{name}: utime={utime:.3f}s rtime={rtime:.3f}s over {iterations} runs")


if __name__ == "__main__":
    out = ["frame=  79 fps", "bench: utime=1.250s stime=0.010s rtime=1.300s", "bench: maxrss=1KiB"]
    assert _parse(out) == (1.25, 1.3)
    try:
        _parse(["Error opening input"])
    except ValueError:
        pass
    else:
        raise AssertionError("missing bench line not caught")
    print("ok")
