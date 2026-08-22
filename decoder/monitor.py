"""Change detection — the half of the job that is not population.

Populating says what is true today. Monitoring says what CHANGED, and the two
need different designs: population reads everything once, monitoring reads a
cheap fingerprint often and only descends where the fingerprint moved.

Three kinds of change, three fingerprints, all cheap:

  RULE CHANGED     a ZR section's LAST AMENDED date moves. This is the big one:
                   an amendment silently invalidates every envelope computed
                   from that section. Free, because zr_feed already stores
                   LAST AMENDED as part of the fact — comparing the cache to the
                   live page IS the detector.

  UNIVERSE GREW    the COUNT of documents of a type in ACRIS goes up. New rows
                   are new sites needing decode. One Socrata count query per
                   type per day, no document fetched.

  PARCEL MOVED     a decoded parcel's underlying facts shift — its zoning
                   district, its lot area, its lot ceasing to exist.

Nothing here decodes anything. It produces a WORKLIST, and the decoders run
against that list. Keeping those separate is what makes a daily cadence
affordable: the detector must stay cheap enough to run on everything.
"""
import json, pathlib, sys, urllib.parse, urllib.request
from datetime import date

HERE = pathlib.Path(__file__).parent
STATE = HERE / "monitor_state.json"
TOKEN = "XBMcBRBwtwiD4elm0XS5iwLRZ"
ACRIS_MASTER = "https://data.cityofnewyork.us/resource/bnx9-e6tj.json"

# Document types the decoder claims to cover. A count that moves means new
# instruments exist that no decode has seen.
WATCHED_DOC_TYPES = ["DEVR"]

# Sections every envelope in the store depends on. If one is amended, the
# figures derived from it are stale — not wrong yesterday, wrong from now on.
WATCHED_SECTIONS = ["23-22", "24-11", "33-121", "33-122", "33-123",
                    "43-12", "43-132", "77-22", "115-21"]


def load_state():
    if STATE.exists():
        return json.loads(STATE.read_text(encoding="utf-8"))
    return {"sections": {}, "doc_counts": {}, "last_run": None}


def save_state(st):
    st["last_run"] = date.today().isoformat()
    STATE.write_text(json.dumps(st, indent=1), encoding="utf-8")


def acris_count(doc_type):
    """How many documents of this type ACRIS holds. A count, not the rows —
    the whole point is that the fingerprint stays cheap."""
    q = urllib.parse.urlencode({
        "$select": "count(document_id)",
        "$where": f"doc_type='{doc_type}'",
        "$$app_token": TOKEN})
    with urllib.request.urlopen(f"{ACRIS_MASTER}?{q}", timeout=90) as f:
        rows = json.load(f)
    if not rows:
        return None
    return int(next(iter(rows[0].values())))


def section_amended(sec):
    """LAST AMENDED, live. Bypasses the cache on purpose — comparing the cache
    to itself would report calm forever."""
    sys.path.insert(0, str(HERE))
    import zr_feed
    rec = zr_feed.fetch_section(sec, refresh=True)
    return rec.get("last_amended")


def run(check_acris=True, check_zr=True):
    st = load_state()
    findings = []

    if check_zr:
        for sec in WATCHED_SECTIONS:
            try:
                now = section_amended(sec)
            except Exception as e:
                findings.append({"kind": "zr_unreachable", "section": sec,
                                 "detail": str(e)[:120], "severity": "check_failed"})
                continue
            was = st["sections"].get(sec)
            st["sections"][sec] = now
            if was is None:
                findings.append({"kind": "zr_baseline", "section": sec,
                                 "detail": f"first observation, last amended {now}",
                                 "severity": "info"})
            elif was != now:
                findings.append({
                    "kind": "ZR_AMENDED", "section": sec,
                    "detail": f"last amended moved {was} -> {now}",
                    "severity": "high",
                    "implication": ("every envelope figure derived from this section is "
                                    "stale; re-run close_split_far and any baseline that "
                                    "cites it")})

    if check_acris:
        for dt in WATCHED_DOC_TYPES:
            try:
                now = acris_count(dt)
            except Exception as e:
                findings.append({"kind": "acris_unreachable", "doc_type": dt,
                                 "detail": str(e)[:120], "severity": "check_failed"})
                continue
            was = st["doc_counts"].get(dt)
            st["doc_counts"][dt] = now
            if was is None:
                findings.append({"kind": "acris_baseline", "doc_type": dt,
                                 "detail": f"first observation, {now:,} documents",
                                 "severity": "info"})
            elif now != was:
                findings.append({
                    "kind": "ACRIS_COUNT_MOVED", "doc_type": dt,
                    "detail": f"{was:,} -> {now:,} ({now - was:+,})",
                    "severity": "high" if now > was else "investigate",
                    "implication": ("new instruments exist that no decode has seen; "
                                    "pull the delta by recorded date and queue them"
                                    if now > was else
                                    "a count that FALLS is not a normal event — "
                                    "corrections or a changed query, worth reading before "
                                    "trusting either number")})

    save_state(st)
    return findings


if __name__ == "__main__":
    fs = run(check_acris="--no-acris" not in sys.argv,
             check_zr="--no-zr" not in sys.argv)
    order = {"high": 0, "investigate": 1, "check_failed": 2, "info": 3}
    for f in sorted(fs, key=lambda f: order.get(f["severity"], 9)):
        tag = f.get("section") or f.get("doc_type") or ""
        print(f"  [{f['severity']:<12}] {f['kind']:<20} {tag:<10} {f['detail']}")
        if f.get("implication"):
            print(f"                 -> {f['implication']}")
    changed = [f for f in fs if f["severity"] in ("high", "investigate")]
    failed = [f for f in fs if f["severity"] == "check_failed"]
    print(f"\n{len(fs)} observations | {len(changed)} changes | {len(failed)} checks could not run")
    if failed:
        print("  a check that could not run is NOT a clean check")
