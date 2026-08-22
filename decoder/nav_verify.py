"""THE PHASE GATE — does the navigation table hand acquisition what it needs?

    python nav_verify.py

Login, 2026-08-19: *"key determine if the phase passes"* and *"just make sure
the navigation table is ready and will pass phase check by end of night so that
acqusition can kick off"*.

⚠ THIS READS THE CSV, NOT THE DATABASE IT WAS BUILT FROM. A gate that queries
the source proves the source is fine and says nothing about the artifact
acquisition actually opens. The whole point is to catch a table that lost
something on the way out.

Five checks, each with its denominator printed:

    1  UNKEYED == 0            no row may lack a key      <- the hard gate
    2  every row has a doc id and an endpoint
    3  Richmond rows carry their index (instrument/book/page)  <- new tonight
    4  ACRIS rows carry parties where the index has them
    5  the endpoint is the MINTING url, never a resolved one
"""
from __future__ import annotations
import csv, json, sys, collections, pathlib

# ⚠ A GATE THAT CRASHES WHEN IT FAILS IS WORSE THAN NO GATE. Measured
# 2026-08-19: the first version printed a "⚠" marker on the FAILING branch only,
# so the clean table passed and the defective table died with UnicodeEncodeError
# mid-report - losing every check after the first failure, which is precisely the
# output you need. The console here is cp1252. Same idiom as night_chain.py.
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import corpus_paths as CP

csv.field_size_limit(10 ** 9)


def main():
    # ⚠ A GATE YOU CANNOT RUN ON A SMALL TABLE IS A GATE YOU CANNOT TEST.
    # The real table is 11 GB; proving this script is correct against it costs a
    # full scan every time and cannot be done before the table exists. Accepting
    # a path lets `nav_build.py --limit 5000 --out /tmp/x.csv` produce something
    # checkable in seconds. Default stays the real table so the gate is one word.
    tab = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path(CP.NAV_TABLE)
    if not tab.exists():
        print(f"NO TABLE at {tab}")
        return 1
    n = 0
    unkeyed = 0
    no_doc = 0
    no_endpoint = 0
    resolved_endpoint = 0
    keykind = collections.Counter()
    rc_total = rc_with_index = 0
    ac_total = ac_with_party = 0
    sample_rc = sample_ac = None
    pdf_filled = 0
    no_detail_ep = 0

    with tab.open(encoding="utf-8", newline="") as f:
        r = csv.reader(f)
        head = next(r, None)
        # ⚠ READ BY NAME, NEVER BY POSITION. This unpacked row[0..4] as
        # key,id,index,endpoint,pdf. When the columns became
        # id,keyed_by,key,index,endpoint,pdf on 2026-08-20, every one of those
        # names silently pointed at a different field - and NOTHING would have
        # failed: document ids are never empty, so "unkeyed" would count zero
        # from the id column and the gate would print PASS over nonsense.
        # A gate reading the wrong column still returns a number.
        cols = {name: i for i, name in enumerate(head or [])}
        # accept the pre-2026-08-20 single-endpoint layout too: "endpoint" is
        # the image endpoint under its old name.
        # column names by GENERATION, newest first: doc_info (2026-08-20,
        # custodian-native) <- index <- the positional era. Reading by name is
        # what lets one gate cover every generation still on disk.
        ix_name = next((c for c in ("recorded_details", "doc_info", "index")
                        if c in cols), "index")
        dep_name = next((c for c in ("rd_endpoint", "doc_info_endpoint",
                         "index_endpoint") if c in cols), "index_endpoint")
        need = ("id", "key", ix_name)
        ep_name = next((c for c in ("pdf_endpoint", "image_endpoint",
                        "endpoint") if c in cols), "endpoint")
        absent = [c for c in need if c not in cols] + ([ep_name] if ep_name not in cols else [])
        if absent:
            print(f"  FAIL: navigation table lacks column(s): {absent}")
            print(f"        header read: {head}")
            return 1
        i_id, i_key = cols["id"], cols["key"]
        i_ix, i_ep = cols[ix_name], cols[ep_name]
        i_dep = cols.get(dep_name)
        i_kb, i_pdf = cols.get("keyed_by"), cols.get("pdf")
        for row in r:
            n += 1
            key, did = row[i_key], row[i_id]
            ix, endpoint = row[i_ix], row[i_ep]
            pdf = row[i_pdf] if (i_pdf is not None and i_pdf < len(row)) else ""
            if pdf:
                pdf_filled += 1
            if i_dep is not None and not row[i_dep]:
                no_detail_ep += 1
            if not key:
                unkeyed += 1
            elif i_kb is not None:
                keykind[row[i_kb] or "?"] += 1
            else:
                keykind[key.split(":", 1)[0] if ":" in key else "parcel"] += 1
            if not did:
                no_doc += 1
            if not endpoint:
                no_endpoint += 1
            elif "expires" in endpoint.lower() or "signature=" in endpoint.lower():
                resolved_endpoint += 1
            try:
                d = json.loads(ix) if ix else {}
            except Exception:
                d = {}
            # ⚠ BK_ IS ACRIS, NOT RICHMOND. MEASURED 2026-08-20: this test
            # pooled 1,721,172 BK_ documents (ACRIS book/page microfilm) in with
            # Richmond. nav_build writes book/page/instrument into the index ONLY
            # when the document is RC_, so every BK_ row landed in the DENOMINATOR
            # and not one could ever reach the numerator. The line then read
            #   Richmond rows carrying their index  2,426,588 / 4,147,760  58.50%
            # when the true coverage is 2,426,588 / 2,426,588 = 100.00%.
            # A wrong denominator never fails loudly - it prints a believable
            # percentage and invites a hunt for 1.7M "missing" indexes.
            # Classify with the PRODUCER's own predicate: nav_build decides
            # custodian by rc = did.startswith("RC_") and nothing else.
            if did.startswith("RC_"):
                rc_total += 1
                if d.get("book") or d.get("instrument") or d.get("page"):
                    rc_with_index += 1
                    if sample_rc is None:
                        sample_rc = (key, did, d)
            else:
                ac_total += 1
                if d.get("parties"):
                    ac_with_party += 1
                    if sample_ac is None:
                        sample_ac = (key, did, d)

    def line(lbl, got, tot, hard=False):
        """⚠ A COVERAGE LINE MUST NOT WEAR A GATE'S BADGE. Printing "OK" beside
        20.00% reads as passed to anyone scanning the report, when nothing was
        asserted at all. Gates say OK/FAIL; coverage says "cov" and lets the
        number speak."""
        pct = 100 * got / tot if tot else 0.0
        if not hard:
            mark = "cov  "
        else:
            mark = "OK   " if got == tot else "FAIL "
        print(f"  {mark}{lbl:<42}{got:>12,} / {tot:<12,} {pct:6.2f}%")

    print(f"\nNAVIGATION PHASE GATE — {tab}")
    print(f"  {tab.stat().st_size/1e6:,.0f} MB · {n:,} rows\n")
    print(f"  {'GATE  UNKEYED must be 0':<46}{unkeyed:>12,}"
          f"   {'PASS' if unkeyed == 0 else 'FAIL'}")
    line("rows with a document id", n - no_doc, n, hard=True)
    line("rows with an endpoint", n - no_endpoint, n, hard=True)
    line("endpoints that are MINTING urls", n - resolved_endpoint, n, hard=True)
    if no_detail_ep or True:
        line("rows with a detail (index) endpoint", n - no_detail_ep, n, hard=True)
    line("Richmond rows carrying their index", rc_with_index, rc_total)
    line("ACRIS rows carrying parties", ac_with_party, ac_total)
    print("\n  key kinds:", dict(keykind))
    # ⚠ pdf IS DELIBERATELY EMPTY UNTIL ACQUISITION FILLS IT. Counting it
    # here is what turns the ACQUISITION gate into a measurement instead of a
    # restatement of the path formula that used to pre-fill this column for
    # all 24M rows whether or not a single file had been fetched.
    print(f"  pdf cells filled (acquisition): {pdf_filled:,} / {n:,}")
    for lbl, s in (("richmond", sample_rc), ("acris", sample_ac)):
        if s:
            k, d, ix = s
            print(f"\n  sample {lbl}: key={k[:60]}  doc={d}")
            print(f"    index={json.dumps(ix, separators=(',', ':'))[:300]}")
    return 0 if unkeyed == 0 and no_doc == 0 and no_endpoint == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
