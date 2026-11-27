"""FFmpeg benchmarks for testv-image-ffmpeg-bench images (meta-testv), e.g.
built with different RISC-V tunes and compared by the ffmpeg-bench workflow.
The benchmarks themselves are meta-testv's ffmpeg-bench script, as run by its
ffmpeg_bench testimage case.

Runs on any qemu env with a ``shell`` fixture, e.g.

uv run pytest --lg-env boards/k3-pico-itx-8gb/qemu-guest.yaml board-tests/test_ffmpeg_bench.py

Each benchmark runs ``BENCH_ITERATIONS`` times (default 3); the median of
each one's utime/rtime is recorded as junit properties and written, with
``BENCH_LABEL`` and the image's TUNE_FEATURES, to ``BENCH_JSON`` (default
bench.json) for meta-testv's scripts/ffmpeg-bench-report.
"""

import json
import os
import statistics


def _parse(lines):
    """Lines of "bench <name> <utime> <rtime>" -> {name: {utime, rtime, runs}},
    with the median of each name's runs (as meta-testv's ffmpeg_bench case)."""
    runs = {}
    for line in lines:
        f = line.split()
        if len(f) == 4 and f[0] == "bench":
            runs.setdefault(f[1], []).append((float(f[2]), float(f[3])))
    return {
        name: {
            "utime": statistics.median(u for u, _ in r),
            "rtime": statistics.median(t for _, t in r),
            "runs": r,
        }
        for name, r in runs.items()
    }


def test_ffmpeg_bench(shell, record_property):
    # The tune the image was built with (testv's IMAGE_BUILDINFO_VARS), so
    # results can't be credited to the wrong build.
    out = shell.run_check("cat /etc/buildinfo")
    info = dict(
        (k.strip(), v.strip()) for k, sep, v in (line.partition("=") for line in out) if sep
    )
    tune_features = info.get("TUNE_FEATURES", "")
    record_property("TUNE_FEATURES", tune_features)

    iterations = int(os.environ.get("BENCH_ITERATIONS", 3))
    timeout = int(os.environ.get("BENCH_TIMEOUT", 3600))
    benchmarks = _parse(shell.run_check(f"ffmpeg-bench -n {iterations}", timeout=timeout))
    assert benchmarks

    with open(os.environ.get("BENCH_JSON", "bench.json"), "w") as f:
        json.dump(
            {
                "label": os.environ.get("BENCH_LABEL", tune_features),
                "tune_features": tune_features,
                "benchmarks": benchmarks,
            },
            f,
            indent=2,
        )
    for name, b in benchmarks.items():
        record_property(f"{name}.utime", b["utime"])
        record_property(f"{name}.rtime", b["rtime"])
        print(f"{name}: utime={b['utime']:.3f}s rtime={b['rtime']:.3f}s")


if __name__ == "__main__":
    out = ["bench a 1.0 1.1", "bench a 3.0 3.1", "bench a 2.0 2.1", "noise", "bench b 5 6"]
    r = _parse(out)
    assert r["a"]["utime"] == 2.0 and r["a"]["rtime"] == 2.1 and len(r["a"]["runs"]) == 3
    assert r["b"] == {"utime": 5.0, "rtime": 6.0, "runs": [(5.0, 6.0)]}
    print("ok")
