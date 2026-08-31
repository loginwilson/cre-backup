"""Validate the positive and negative fixtures against the committed schema suite.

schemacheck.py asks "does at least one instance exist?" by synthesis. This asks the
same question with hand-authored instances, which catches the cases synthesis cannot
reach -- a conditional whose satisfiable branch is not the first enum value -- and
also checks that the negative cases are actually rejected.

Exit status is nonzero if any positive fixture fails or any negative fixture passes.
"""
import json
import pathlib
import sys

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

HERE = pathlib.Path(__file__).resolve().parent
V2 = HERE.parent
FILES = ["discovery.schema.json", "enrichment.schema.json", "extraction.schema.json"]


def registry():
    res = []
    for f in FILES:
        c = json.loads((V2 / f).read_text(encoding="utf-8"))
        res.append((c["$id"], Resource.from_contents(c)))
    return Registry().with_resources(res)


def main():
    reg = registry()
    data = json.loads((HERE / "positive.json").read_text(encoding="utf-8"))
    failures = 0

    for group, must_validate in (("fixtures", True), ("negative_fixtures", False)):
        for fx in data.get(group, []):
            f, ptr = fx["schema"].split("#", 1)
            ref = "https://cred.nyc/v2/" + f + "#" + ptr
            v = Draft202012Validator({"$ref": ref}, registry=reg)
            errs = list(v.iter_errors(fx["instance"]))
            ok = (not errs) if must_validate else bool(errs)
            if not ok:
                failures += 1
                detail = errs[0].message[:80] if errs else "validated but should have been rejected"
                print("  FAIL  %-28s %s" % (fx["name"], detail))
            else:
                print("  ok    %-28s %s" % (fx["name"], "rejected" if not must_validate else ""))

    n = len(data.get("fixtures", [])) + len(data.get("negative_fixtures", []))
    print("\n%d fixtures, %d failures" % (n, failures))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
