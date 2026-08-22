"""PATCH GUARD — a patch that silently fails is worse than one that crashes.

⚠ THE CLASS THIS CLOSES.

_patch_zlda.py died on a bash heredoc error. I saw the error, switched tools
for the NEXT patch, and never re-ran the failed one. Five claims — the 2010
air-rights price, the light/air/view granting words, the deliberately
unrecorded purchase agreement — went into a message to the user and into no
table.

It surfaced only because a supersession edge happened to point at one of the
missing claims. HAD I NOT WRITTEN THAT EDGE, THEY WOULD STILL BE LOST. The
narrative was right, the scorecard said ANSWERED, and the claim count kept
rising from other patches. Nothing in the system was asking "did the thing
I just wrote actually arrive?"

⚠ 24 PATCH SCRIPTS WERE WRITTEN TODAY AND NOT ONE VERIFIED ITS OWN OUTPUT.

So: apply() extracts the claim ids from the text it is about to insert,
writes the file, RE-IMPORTS the module fresh, and asserts every id is
present. A patch either lands completely or raises.

    import patchlib
    patchlib.apply(NEW)          # anchors on the last section header
"""
import importlib
import pathlib
import re
import sys

TARGET = pathlib.Path("claims.py")


def claim_ids(text):
    """⚠ SKIP f-STRING PLACEHOLDERS. A patch that BUILDS claim text at
    runtime contains literals like C("{cid}", which are templates, not
    claims. Counting them makes the audit report permanent phantom
    failures — and a guard that cries wolf trains you to ignore it, which
    is worse than no guard."""
    return [c for c in re.findall(r'C\(\s*"([^"]+)"', text)
            if "{" not in c and "}" not in c]


def apply(new_text, target=TARGET, anchor_re=r"^ # ---- .*$"):
    """Insert new_text above the last section header, then PROVE it landed."""
    want = claim_ids(new_text)
    if not want:
        raise ValueError("patch contains no C(...) claims — nothing to apply")

    t = target.read_text(encoding="utf-8")

    # ⚠ REFUSE DUPLICATES. Re-running a patch that already applied would
    # otherwise write a second copy and the validator would report a
    # duplicate claim_id far from the cause.
    already = [c for c in want if f'C("{c}"' in t]
    if already:
        raise SystemExit(f"⚠ already present, refusing to double-apply: "
                         f"{', '.join(already[:5])}")

    hdrs = list(re.finditer(anchor_re, t, re.M))
    if not hdrs:
        raise SystemExit("⚠ no section header to anchor on")
    a = hdrs[-1].group(0)
    target.write_text(t.replace(a, new_text + a, 1), encoding="utf-8")

    # ⚠ THE GUARD. Re-import from disk — not from whatever is already in
    # sys.modules, which would happily report the pre-patch state.
    for m in ("claims",):
        if m in sys.modules:
            del sys.modules[m]
    try:
        K = importlib.import_module("claims")
    except Exception as e:
        raise SystemExit(f"⚠ PATCH WROTE BUT claims.py NO LONGER IMPORTS: "
                         f"{type(e).__name__}: {e}\n"
                         f"   the file is now broken — fix before continuing")

    have = {c["claim_id"] for c in K.rows()}
    missing = [c for c in want if c not in have]
    if missing:
        raise SystemExit(f"⚠ PATCH APPLIED BUT {len(missing)} CLAIMS ARE NOT "
                         f"IN THE LEDGER: {', '.join(missing)}")

    print(f"applied {len(want)} claims · verified all present: "
          f"{', '.join(want[:4])}{' ...' if len(want) > 4 else ''}")
    return want


def audit():
    """Which claims does every _patch_*.py claim to write, and did they land?"""
    import claims as K
    have = {c["claim_id"] for c in K.rows()}
    lost = {}
    for p in sorted(pathlib.Path(".").glob("_patch_*.py")):
        txt = p.read_text(encoding="utf-8", errors="replace")
        want = claim_ids(txt)
        gone = [c for c in want if c not in have]
        if gone:
            lost[p.name] = gone
    return lost


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    lost = audit()
    print("PATCH AUDIT — every _patch_*.py vs the ledger\n")
    if not lost:
        print("  ✓ every claim any patch script names is in the ledger")
    else:
        print(f"  ⚠ {sum(len(v) for v in lost.values())} claims named by a "
              f"patch script are MISSING:\n")
        for f, ids in lost.items():
            print(f"    {f}")
            for i in ids:
                print(f"        {i}")
