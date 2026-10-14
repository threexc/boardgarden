import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parents[1] / ".forgejo/actions/prepare-recipe-upgrade/upgrade.py"
spec = importlib.util.spec_from_file_location("upgrade", SCRIPT)
upgrade = importlib.util.module_from_spec(spec)
spec.loader.exec_module(upgrade)


def git(repo, *args):
    return upgrade.git(repo, *args).stdout.strip()


@pytest.fixture
def upstream(tmp_path):
    """Repo with v1.0 and v1.1 tags; v1.1 shifts context and upstreams a fix."""
    repo = tmp_path / "upstream"
    repo.mkdir()
    git(repo, "init", "-q")
    lines = [f"line {i}\n" for i in range(20)]
    (repo / "a.txt").write_text("".join(lines))
    (repo / "b.txt").write_text("old\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "1.0")
    git(repo, "tag", "-a", "-m", "1.0", "v1.0")
    # Patches are generated against v1.0.
    patches = tmp_path / "patches"
    patches.mkdir()

    def make_patch(name, path, text):
        (repo / path).write_text(text)
        diff = git(repo, "diff")
        (patches / name).write_text(f"Subject: {name}\n\nUpstream-Status: Pending\n---\n{diff}\n")
        git(repo, "checkout", "-q", ".")

    make_patch("clean.patch", "b.txt", "new\n")
    make_patch("fuzzy.patch", "a.txt", "".join(lines[:10] + ["patched\n"] + lines[11:]))
    make_patch("conflict.patch", "a.txt", "".join(lines[:2] + ["mine\n"] + lines[3:]))
    make_patch("upstreamed.patch", "a.txt", "".join(lines[:18] + ["fixed\n"] + lines[19:]))
    # v1.1: lines 7 (context of fuzzy) and 2 (conflict) change, 18 is fixed upstream.
    lines[7] = "changed context\n"
    lines[2] = "theirs\n"
    lines[18] = "fixed\n"
    (repo / "a.txt").write_text("".join(lines))
    git(repo, "commit", "-qam", "1.1")
    git(repo, "tag", "v1.1")
    git(repo, "tag", "v1.2-rc1")
    return repo, patches


def test_find_tag(upstream):
    repo, _ = upstream
    version, tag, sha = upgrade.find_tag(f"file://{repo}", r"^v(\d+\.\d+)$", "1.0", "")
    assert (version, tag, sha) == ("1.1", "v1.1", git(repo, "rev-parse", "v1.1"))
    assert upgrade.find_tag(f"file://{repo}", r"^v(\d+\.\d+)$", "1.1", "") is None
    # Annotated tag resolves to the commit, not the tag object.
    assert upgrade.find_tag(f"file://{repo}", r"^v(\d+\.\d+)$", "1.1", "1.0")[2] == git(
        repo, "rev-parse", "v1.0^{commit}"
    )


def test_apply_one(upstream):
    repo, patches = upstream
    git(repo, "checkout", "-q", "v1.1")
    fuzzy_before = (patches / "fuzzy.patch").read_text()
    assert upgrade.apply_one(repo, patches / "clean.patch") == "ok"
    assert upgrade.apply_one(repo, patches / "fuzzy.patch") == "refreshed"
    assert upgrade.apply_one(repo, patches / "upstreamed.patch") == "dropped"
    assert upgrade.apply_one(repo, patches / "conflict.patch") == "failed"
    fuzzy_after = (patches / "fuzzy.patch").read_text()
    assert fuzzy_after != fuzzy_before
    assert fuzzy_after.startswith("Subject: fuzzy.patch\n\nUpstream-Status: Pending\n")
    assert "+changed context" not in fuzzy_after and " changed context" in fuzzy_after
    # A refreshed patch applies cleanly on top of the new tag.
    git(repo, "checkout", "-qf", "v1.1")
    assert upgrade.apply_one(repo, patches / "fuzzy.patch") == "ok"


def test_drop(tmp_path):
    layer = tmp_path / "layer"
    pdir = layer / "recipes-foo/foo/files"
    pdir.mkdir(parents=True)
    (pdir / "gone.patch").write_text("x\n")
    bb = layer / "recipes-foo/foo/foo_1.0.bb"
    bb.write_text(
        'SRC_URI = "git://x;branch=main \\\n    file://gone.patch \\\n    file://keep.cfg \\\n"\n'
        'SRC_URI:append:m = " file://gone.patch;striplevel=1 file://other.patch"\n'
    )
    git(layer, "init", "-q")
    git(layer, "add", "-A")
    git(layer, "commit", "-qm", "init")
    upgrade.drop(pdir / "gone.patch")
    assert not (pdir / "gone.patch").exists()
    assert bb.read_text() == (
        'SRC_URI = "git://x;branch=main \\\n    file://keep.cfg \\\n"\n'
        'SRC_URI:append:m = " file://other.patch"\n'
    )
