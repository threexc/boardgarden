#!/usr/bin/env python3
"""
Bump a recipe to a newer upstream tag, refresh the patches it applies for
each selected MACHINE, and emit one git format-patch file per layer touched.

Similar in spirit to Yocto's auto-upgrade-helper, but without devtool: the
version/SRCREV bump is a plain text edit and patches are refreshed with
`git apply -3` against the new upstream tag.

Must run from the build directory of a bitbake-setup tree, inside its build
environment (after sourcing init-build-env). Layers are expected under
../layers/. MACHINE is switched with bitbake-config-build.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

# tag: regex over upstream tag names, group 1 is the version.
# version_var: where the current version lives. PV means it's in the recipe
#   file name (foo_1.2.bb), anything else is a variable in the recipe file.
# branch: optional SRC_URI branch name template, formatted with version parts.
# select: whether a MACHINE uses the recipe, given that MACHINE's global
#   bitbake environment (cheap: no recipe parsing).
RECIPES = {
    "linux-mainline": {
        "tag": r"^v(\d+\.\d+\.\d+)$",
        "version_var": "LINUX_VERSION",
        "branch": "linux-{0}.{1}.y",
        "select": lambda e: e.get("PREFERRED_PROVIDER_virtual/kernel") == "linux-mainline",
    },
    "u-boot": {
        "tag": r"^v(\d{4}\.\d{2})$",
        "version_var": "PV",
        "select": lambda e: e.get("PREFERRED_PROVIDER_virtual/bootloader") == "u-boot",
    },
    "opensbi": {
        "tag": r"^v(\d+\.\d+)$",
        "version_var": "PV",
        "select": lambda e: (
            "opensbi" in e.get("EXTRA_IMAGEDEPENDS", "").split()
            and e.get("PREFERRED_PROVIDER_opensbi", "opensbi") == "opensbi"
        ),
    },
}

GIT_ID = ["-c", "user.name=recipe-upgrade", "-c", "user.email=recipe-upgrade@localhost"]
LAYERS = Path.cwd().parent / "layers"


def run(*cmd, cwd=None, check=True):
    p = subprocess.run(cmd, cwd=cwd, text=True, errors="surrogateescape", capture_output=True)
    if check and p.returncode:
        sys.stderr.write(p.stdout + p.stderr)
        raise SystemExit(f"command failed: {' '.join(map(str, cmd))}")
    return p


def git(repo, *args, check=True):
    return run("git", "-C", str(repo), *GIT_ID, *args, check=check)


def toplevel(path):
    return Path(
        git(path if path.is_dir() else path.parent, "rev-parse", "--show-toplevel").stdout.strip()
    )


def vkey(version):
    return tuple(int(x) for x in re.findall(r"\d+", version))


def layer_name(repo):
    """Name of the layers/ entry (possibly a symlink, see bitbake-setup -L) for repo."""
    for d in LAYERS.iterdir():
        if d.resolve() == repo.resolve():
            return d.name
    return repo.name


def set_machine(machine):
    run("bitbake-config-build", "disable-fragment", "machine/")
    run("bitbake-config-build", "enable-fragment", f"machine/{machine}")


def bitbake_env(recipe=None):
    """Global (or recipe) environment, or {} if the recipe is skipped."""
    p = run("bitbake", "-e", *([recipe] if recipe else []), check=False)
    if p.returncode:
        return {}
    return dict(re.findall(r'^(?:export )?([^\s#=]+)="(.*)"$', p.stdout, re.M))


def upstream_uri(src_uri):
    for uri in src_uri.split():
        if uri.startswith("git://"):
            path, *params = uri[len("git://") :].split(";")
            params = dict(p.split("=", 1) for p in params if "=" in p)
            return f"{params.get('protocol', 'git')}://{path}"
    raise SystemExit("no git:// entry in SRC_URI")


def find_tag(uri, pattern, current, wanted):
    """Return (version, tag, sha) for wanted (or the newest tag > current)."""
    tags = {}
    for line in run("git", "ls-remote", "--tags", uri).stdout.splitlines():
        sha, ref = line.split()
        name = ref.removeprefix("refs/tags/")
        peeled = name.endswith("^{}")
        name = name.removesuffix("^{}")
        m = re.match(pattern, name)
        # Annotated tags list the tag object and then the peeled commit (^{});
        # SRCREV has to be the commit.
        if m and (peeled or name not in tags):
            tags[name] = (m.group(1), name, sha)
    if wanted:
        hits = [t for t in tags.values() if t[0] == wanted]
        if not hits:
            raise SystemExit(f"no upstream tag for version {wanted}")
        return hits[0]
    best = max(tags.values(), key=lambda t: vkey(t[0]), default=None)
    return best if best and vkey(best[0]) > vkey(current) else None


def patches(env):
    """Local patch files bitbake would apply for this recipe + MACHINE."""
    dirs = env["FILESPATH"].split(":")
    out = []
    for uri in env["SRC_URI"].split():
        if not uri.startswith("file://"):
            continue
        name, *params = uri[len("file://") :].split(";")
        params = dict(p.split("=", 1) for p in params if "=" in p)
        default = "yes" if name.endswith((".patch", ".diff")) else "no"
        if params.get("apply", default) != "yes":
            continue
        path = next((Path(d, name) for d in dirs if Path(d, name).is_file()), None)
        if path is None:
            raise SystemExit(f"{name} not found in FILESPATH")
        out.append(path)
    return out


def apply_one(src, patch):
    if git(src, "apply", "--check", patch, check=False).returncode == 0:
        git(src, "apply", "--index", patch)
        status = "ok"
    elif git(src, "apply", "-R", "--check", patch, check=False).returncode == 0:
        return "dropped"
    elif git(src, "apply", "-3", patch, check=False).returncode == 0:
        # Keep the original header (From/Subject/Upstream-Status/SoB), replace
        # only the diff body.
        text = patch.read_text(errors="surrogateescape")
        m = re.search(r"^(?:diff |--- |Index: )", text, re.M)
        head = text[: m.start()] if m else ""
        body = git(src, "diff", "--cached", "--no-color").stdout
        patch.write_text(head + body, errors="surrogateescape")
        status = "refreshed"
    else:
        git(src, "reset", "-q", "--hard")
        return "failed"
    git(src, "commit", "-qm", patch.name)
    return status


def drop(patch):
    """Delete an already-upstream patch and its SRC_URI entries."""
    repo = toplevel(patch)
    name = re.escape(patch.name)
    whole_line = re.compile(rf"^[ \t]*file://{name}(;\S*)?[ \t]*\\?[ \t]*\n", re.M)
    inline = re.compile(rf"file://{name}(;\S*)?[ \t]*")
    # Walk up from the patch dir to the first dir whose recipes reference it.
    for d in patch.parents:
        hits = [
            f
            for f in d.iterdir()
            if f.suffix in (".bb", ".bbappend", ".inc") and f"file://{patch.name}" in f.read_text()
        ]
        for f in hits:
            f.write_text(inline.sub("", whole_line.sub("", f.read_text())))
        if hits or d == repo:
            break
    # After the walk: git rm also removes the patch dir once it's empty.
    git(repo, "rm", "-q", str(patch))


def output(**kw):
    with open(os.environ.get("GITHUB_OUTPUT", os.devnull), "a") as f:
        for k, v in kw.items():
            print(f"{k}={v}")
            f.write(f"{k}={v}\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--recipe", required=True, choices=RECIPES)
    ap.add_argument(
        "--machines",
        default="",
        help="space-separated candidate machines (default: all in --machine-layer)",
    )
    ap.add_argument("--machine-layer", default="meta-riscv", help="layer under ../layers")
    ap.add_argument("--version", default="", help="target version (default: newest tag)")
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    spec = RECIPES[a.recipe]
    machines = a.machines.split() or sorted(
        f.stem
        for f in (LAYERS / a.machine_layer / "conf/machine").glob("*.conf")
        if not f.stem.startswith("baremetal-")
    )

    # Patch series per MACHINE. Evaluated before the bump; SRC_URI and
    # FILESPATH don't depend on the version for any recipe in RECIPES.
    env, series = {}, {}
    for m in machines:
        set_machine(m)
        if not spec["select"](bitbake_env()):
            continue
        menv = bitbake_env(a.recipe)
        if menv:
            env = env or menv
            series[m] = patches(menv)
    print("machines using recipe:", " ".join(series) or "none")
    if not series:
        raise SystemExit(f"no machine in {machines} uses {a.recipe}")

    old = env[spec["version_var"]].split("+")[0]
    old_rev = env["SRCREV"]
    uri = upstream_uri(env["SRC_URI"])
    found = find_tag(uri, spec["tag"], old, a.version)
    if not found:
        output(
            status="current",
            old_version=old,
            new_version=old,
            machines="[]",
            refresh_failed="false",
        )
        return
    new, tag, new_rev = found
    print(f"{a.recipe}: {old} -> {new} ({tag} {new_rev})")

    recipe_file = Path(env["FILE"])
    rdir = recipe_file.parent
    touched = {toplevel(rdir)}

    # SRCREV may live in the recipe or a shared .inc beside it (u-boot-common.inc).
    bumped = False
    for f in sorted(rdir.iterdir()):
        if f.suffix in (".bb", ".inc", ".bbappend") and old_rev in f.read_text():
            f.write_text(f.read_text().replace(old_rev, new_rev))
            bumped = True
    if not bumped:
        raise SystemExit(f"SRCREV {old_rev} not found next to {recipe_file}")

    if spec["version_var"] == "PV":
        for f in sorted(rdir.glob(f"*_{old}.*")):
            git(rdir, "mv", f.name, f.name.replace(f"_{old}.", f"_{new}."))
    else:
        t = recipe_file.read_text()
        t = re.sub(
            rf'^({spec["version_var"]}\s*\??\??=\s*)"{re.escape(old)}"',
            rf'\g<1>"{new}"',
            t,
            flags=re.M,
        )
        if "branch" in spec:
            t = t.replace(
                spec["branch"].format(*old.split(".")), spec["branch"].format(*new.split("."))
            )
        recipe_file.write_text(t)

    results = {}
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp)
        git(src, "init", "-q")
        # ponytail: assumes upstream tags are "v<version>"; true for all RECIPES.
        git(src, "fetch", "-q", "--depth", "1", uri, f"refs/tags/v{old}", f"refs/tags/{tag}")
        for plist in series.values():
            git(src, "checkout", "-qf", new_rev)
            git(src, "clean", "-qfdx")
            for p in plist:
                if results.get(p) == "dropped":
                    continue
                status = apply_one(src, p)
                results.setdefault(p, status)
                if status == "failed":
                    # Later patches in the series likely depend on this one.
                    break

    for p, status in results.items():
        if status == "dropped":
            drop(p)
        if status != "ok":
            touched.add(toplevel(p))

    lines = {
        s: [f"  {p.name}" for p, st in results.items() if st == s]
        for s in ("refreshed", "dropped", "failed")
    }
    body = [f"Automated upgrade to upstream tag {tag} ({new_rev}).", ""]
    for s, title in (
        ("refreshed", "Refreshed patches:"),
        ("dropped", "Dropped patches (already upstream):"),
        ("failed", "Patches that need a manual refresh:"),
    ):
        if lines[s]:
            body += [title, *lines[s], ""]
    body.append(f"Machines: {' '.join(series) or 'none'}")
    msg = f"{a.recipe}: upgrade {old} -> {new}\n\n" + "\n".join(body) + "\n"

    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / "refresh.log").write_text(msg)
    for repo in sorted(touched):
        # -u: never pick up untracked files, e.g. a build tree inside the checkout.
        git(repo, "add", "-u")
        if git(repo, "diff", "--cached", "--quiet", check=False).returncode == 0:
            continue
        git(repo, "commit", "-qm", msg)
        git(repo, "format-patch", "-q", "-1", "-o", str(a.out / layer_name(repo)))

    output(
        status="upgraded",
        old_version=old,
        new_version=new,
        machines=json.dumps(list(series), separators=(",", ":")),
        refresh_failed=str(bool(lines["failed"])).lower(),
    )


if __name__ == "__main__":
    main()
