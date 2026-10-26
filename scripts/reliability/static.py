"""Bounded task identity/scope proof; no solver or old evidence mutation."""

import json
import subprocess

from .runtime import FIXTURE, OUT, ROOT, sha, write_new


def main():
    start = json.loads((OUT / "start.json").read_text(encoding="utf-8"))
    allowed_src = {"src/silo/io/lp.py", "src/silo/io/number_codec.py", "src/silo/io/formats.py",
                   "src/silo/io/__init__.py", "src/silo/cli/main.py", "src/silo/__init__.py"}
    for path, expected in start["source"].items():
        if path not in allowed_src:
            assert sha(ROOT / path) == expected, path
    for path, expected in start["governance"].items():
        assert sha(ROOT / path) == expected, path
    manifest = json.loads((FIXTURE / "manifest.json").read_text(encoding="utf-8"))
    for path, expected in manifest["files"].items():
        assert sha(ROOT / path) == expected, path
    frozen = "f8f00fd60728e0e9314342a3b4e037cfee50f790"
    subprocess.run(["git", "merge-base", "--is-ancestor", frozen, "HEAD"], check=True, cwd=ROOT)
    assert not subprocess.check_output(["git", "diff", start["head"], frozen, "--", "src"],
                                       cwd=ROOT)
    write_new(OUT / "static_scope.json", {"passed": True, "frozen_commit": frozen,
              "prior_production_diff_empty": True, "forbidden_source_hashes_unchanged": True,
              "governance": start["governance"], "manifest_sha": sha(FIXTURE / "manifest.json")})
    print("Scope/immutable-source/governance and freeze-before-production proof passed")


if __name__ == "__main__":
    main()
