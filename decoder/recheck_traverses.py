"""Re-walk EVERY stored description through the CURRENT metes engine.

The enforcement arm of the backward re-check: a stored area is a claim made by
whatever version of the parser existed when it was transcribed. Eight parser
bugs have been fixed so far — spelled-out distances, bearing minutes read as
feet, unicode fractions, leftmost-direction, and the rest — and each fix could
in principle move an area recorded earlier.

Run it after ANY change to metes.py. It repairs nothing; it reports.

Usage: python recheck_traverses.py [--fill]
   --fill  write a traverse block for descriptions that have none (and only those)
"""
import json, pathlib, sys, urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import metes

ENV = r"C:/dev/acris-decoder.env"


def _env():
    v = {}
    for line in open(ENV, encoding="utf-8"):
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, val = line.split("=", 1)
            v[k.strip()] = val.strip()
    return v["ACRIS_SUPABASE_URL"], v["ACRIS_SUPABASE_SERVICE_KEY"]


def walk(decoded_dir=None):
    url, key = _env()
    H = {"apikey": key, "Authorization": f"Bearer {key}"}
    docs = json.load(urllib.request.urlopen(urllib.request.Request(
        url + "/rest/v1/decoder_document?select=document_id,raw_facts", headers=H),
        timeout=90))
    same = moved = missing = 0
    findings = []
    for d in sorted(docs, key=lambda x: x["document_id"]):
        for ld in ((d.get("raw_facts") or {}).get("legal_descriptions") or []):
            cv = ld.get("courses_verbatim")
            if not cv:
                continue
            now = metes.traverse(cv)
            # A traverse that legitimately produced NO area (an unparseable or
            # non-closing description) still HAS a stored traverse. Testing for
            # an area instead of for the BLOCK reported a gap that was not one —
            # the Williamsburg lot 19 description is correctly recorded as
            # unparseable and was being counted as unchecked.
            tblock = ld.get("traverse") or {}
            has_block = bool(tblock.get("verdict"))
            stored = tblock.get("area_sf")
            a = now.get("area_sf")
            rec = {"document_id": d["document_id"],
                   "parcel": ld.get("bbl") or (ld.get("covers_bbls") or [None])[0],
                   "stored": stored, "now": a, "verdict": metes.verdict(now),
                   "closure_ft": now.get("closure_error_ft")}
            if not has_block:
                missing += 1
                rec["state"] = "no_stored_traverse"
            elif stored is None and a is None:
                same += 1
                rec["state"] = "unchanged (no area — unparseable, as recorded)"
            elif a is None:
                moved += 1
                rec["state"] = "now_unparseable"
            elif abs(a - stored) < 0.05:
                same += 1
                rec["state"] = "unchanged"
            else:
                moved += 1
                rec["state"] = "CHANGED"
                rec["delta"] = round(a - stored, 2)
            findings.append(rec)
    return findings, same, moved, missing


if __name__ == "__main__":
    findings, same, moved, missing = walk()
    for f in findings:
        if f["state"] != "unchanged":
            print(f"  [{f['state']:<20}] {f['document_id']}  {f['parcel']}  "
                  f"stored={f['stored']}  now={f['now']}  {f['verdict']}")
    print(f"\n{len(findings)} descriptions re-walked | {same} unchanged | "
          f"{moved} CHANGED | {missing} without a stored traverse")
    if moved:
        print("  a CHANGED area means an earlier decode recorded a figure the current "
              "engine no longer produces — investigate before trusting either.")
