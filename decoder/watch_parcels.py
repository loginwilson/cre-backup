"""Parcel recording watch — flag NEW ACRIS activity on parcels we have decoded.

WHY THIS EXISTS, AND THE FAILURE THAT CAUSED IT

    On 2026-08-06 the lot 49 event ledger was audited against the live index and
    two documents turned out to have NO line in it at all — a 1998 DEED that was
    the parcel's only conveyance between 1971 and 2007, and a 2003 CEMA. Nothing
    flagged them. The narrative read perfectly well without them, which is
    exactly the problem: **a decode goes stale silently, and it reads as
    complete the whole time.**

    Two distinct staleness modes, and this module watches both:

      1. NEW ACTIVITY — a recording made after we last looked. The parcel keeps
         living; the file does not.
      2. MISSED HISTORY — a document that was always there and we never cited.
         Found by diffing the live index against the document ids named in the
         markdown, NOT against what we happen to hold on disk (holding a file
         proves a fetch, not a reading).

    ⚠ Mode 2 is the one that bites. Mode 1 is obvious once you look; mode 2 hides
    behind a coherent story.

WHAT IT DOES NOT DO

    It does not decide whether a document matters. It reports the diff and the
    dates. A human (or a decoder) reads what turned up.
"""
import json, os, pathlib, re, sys, urllib.request, datetime

# Windows consoles default to cp1252 and a WARNING SIGN raises UnicodeEncodeError
# mid-report — which on the first run truncated the output right before the
# "not cited" section, i.e. the console encoding hid the finding.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = pathlib.Path(__file__).parent
STATE = HERE / "watch_state.json"

LEGALS = "https://data.cityofnewyork.us/resource/8h5j-fqxa.json"
MASTER = "https://data.cityofnewyork.us/resource/bnx9-e6tj.json"

# Parcels under watch, with the writeups that are supposed to cover them.
# A parcel with no writeup is still watched for new activity.
WATCH = {
    "1008000049": {
        "borough": "1", "block": "800", "lot": "49",
        "label": "112-118 W 25th (Lam / Chelsea 25 Hotel)",
        "writeups": ["LOT49_EVENTS.md", "LOT49_TIMELINE.md"],
        # the sibling created when the site split — its record is this site's too
        "siblings": [("1", "800", "50")],
    },
}

DOC_ID = re.compile(r"(FT_\d{13}|20\d{14})")


def _get(url):
    with urllib.request.urlopen(url.replace(" ", "%20")) as r:
        return json.load(r)


def index_docs(borough, block, lot):
    """Every document_id ACRIS indexes against this BBL. Paginated with $order —
    $offset without $order silently drops and duplicates rows."""
    out, off = set(), 0
    while True:
        u = (f"{LEGALS}?borough={borough}&block={block}&lot={lot}"
             f"&$select=document_id&$order=:id&$limit=1000&$offset={off}")
        r = _get(u)
        out |= {x["document_id"] for x in r}
        if len(r) < 1000:
            return out
        off += 1000


def master_rows(ids):
    rows = []
    ids = sorted(ids)
    for i in range(0, len(ids), 50):
        ch = ids[i:i + 50]
        w = " in (" + ",".join("'" + c + "'" for c in ch) + ")"
        rows += _get(f"{MASTER}?$where=document_id{w}"
                     f"&$select=document_id,doc_type,document_date,"
                     f"recorded_datetime,document_amt&$limit=200")
    return {r["document_id"]: r for r in rows}


def cited_in(writeups):
    """Document ids NAMED IN THE PROSE. Deliberately not 'files on disk' —
    the whole point is to catch a document we hold but never wrote up."""
    seen = set()
    for w in writeups:
        p = HERE / w
        if p.exists():
            seen |= set(DOC_ID.findall(p.read_text(encoding="utf-8", errors="replace")))
    return seen


def check(bbl, cfg, state):
    live = index_docs(cfg["borough"], cfg["block"], cfg["lot"])
    sib = set()
    for b, bl, lt in cfg.get("siblings", []):
        sib |= index_docs(b, bl, lt)
    prev = set(state.get(bbl, {}).get("known", []))
    prev_sib = set(state.get(bbl, {}).get("known_siblings", []))

    new = live - prev if prev else set()
    new_sib = sib - prev_sib if prev_sib else set()
    uncited = live - cited_in(cfg.get("writeups", []))

    meta = master_rows(new | new_sib | uncited) if (new or new_sib or uncited) else {}

    def fmt(i):
        m = meta.get(i, {})
        d = (m.get("document_date") or m.get("recorded_datetime") or "")[:10]
        amt = float(m.get("document_amt") or 0)
        a = "  ${:,.0f}".format(amt) if amt else ""
        return f"    {d or '(no date)':<10} {i:<16} {m.get('doc_type','?'):<9}{a}"

    print(f"\n=== {bbl} · {cfg['label']}")
    print(f"  live index: {len(live)} documents"
          + (f"  ·  sibling lots: {len(sib)}" if sib else ""))

    if prev and new:
        print(f"  ⚠ NEW SINCE LAST RUN: {len(new)}")
        for i in sorted(new, key=lambda x: fmt(x)):
            print(fmt(i))
    elif prev:
        print("  new since last run: none")
    else:
        print("  (first run — baseline recorded, no comparison possible)")

    if sib:
        if prev_sib and new_sib:
            print(f"  ⚠ NEW ON SIBLING LOT(S): {len(new_sib)}")
            for i in sorted(new_sib, key=lambda x: fmt(x)):
                print(fmt(i))
        elif prev_sib:
            print("  new on sibling lot(s): none")

    if cfg.get("writeups"):
        if uncited:
            print(f"  ⚠ IN THE INDEX BUT NOT CITED IN {', '.join(cfg['writeups'])}: {len(uncited)}")
            for i in sorted(uncited, key=lambda x: fmt(x)):
                print(fmt(i))
        else:
            print(f"  every indexed document is cited in the writeup ✓")

    state[bbl] = {"known": sorted(live), "known_siblings": sorted(sib),
                  "checked": datetime.date.today().isoformat()}
    return bool(new or new_sib or uncited)


if __name__ == "__main__":
    state = json.load(open(STATE)) if STATE.exists() else {}
    flagged = False
    for bbl, cfg in WATCH.items():
        try:
            flagged |= check(bbl, cfg, state)
        except Exception as e:
            print(f"\n=== {bbl}  ERROR: {e}")
            flagged = True          # an error is not a clean run
    json.dump(state, open(STATE, "w"), indent=1)
    print(f"\nstate written to {STATE.name}")
    sys.exit(1 if flagged else 0)
