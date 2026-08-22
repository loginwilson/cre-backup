"""LEGAL INSTRUMENTS NAVIGATION — the one table acquisition reads.

    python nav_build.py                    whole corpus
    python nav_build.py --bbl 5007680058   one parcel (test)
    python nav_build.py --limit 5000       bounded slice

    key | id | index | endpoint | pdf

⚠ ONE ROW PER DOCUMENT, NEVER PER PARCEL-LINK. A document touching four lots is
ONE row with four keys, semicolon separated. Emitting per-link inflates Richmond
from 2,426,404 documents to 2,891,086 rows (+19%) and double-counts anything
measured off this file — including the acquisition completeness check.

⚠ key IS NOT ALWAYS A PARCEL. subject_type is parcel | entity | class. A document
with no BBL is keyed to its PARTY, prefixed `party:`. A row with no key at all is
the only real failure, and the phase gate is that there are none.

⚠ endpoint MINTS, it does not resolve. Richmond's viewer issues a fresh token per
request; a resolved URL carries a timestamp and signature and is stale in minutes.
What is stored is the minting URL, so this table never goes out of date.

⚠ pdf IS DETERMINISTIC FROM THE ID, so it is written at BUILD time, not by
acquisition. Acquisition flips `got` — it never writes a path back. That is what
keeps the completeness check readable from one table:
    total - (present + pending + imageless) = 0
"""
from __future__ import annotations
import argparse, atexit, csv, io, json, os, pathlib, sqlite3, sys, time

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import corpus_paths as CP

RC = "https://www.richmondcountyclerk.com"

# ⚠ ROLES COME FROM THE AUTHORITY, NEVER FROM A HAND MAP. ACRIS stores party_type
# as its own 1/2 code; what those MEAN is per doc type - DEED 1 is GRANTOR/SELLER,
# INIT 1 is DEBTOR, ASST 1 is ASSIGNOR/OLD LENDER. _doctype_codes.json is ACRIS's
# own Document Control Codes table as pulled (126 types). Resolving here makes the
# ACRIS index read the same way Richmond's already does, which carries role names.
DOCTYPES = json.loads((HERE / "_doctype_codes.json").read_text(encoding="utf-8"))


def role_of(doc_type, party_type):
    """ACRIS 1/2 -> the role that doc type gives it. Unknown stays raw, never guessed."""
    t = DOCTYPES.get((doc_type or "").upper())
    if not t:
        return str(party_type or "")
    if str(party_type) == "1":
        return (t.get("party1_type") or "1").upper()
    if str(party_type) == "2":
        return (t.get("party2_type") or "2").upper()
    return str(party_type or "")


def _already_current(a):
    """⚠ A FULL REBUILD THAT CANNOT CHANGE ANYTHING IS 24 MINUTES OF NOTHING.

    MEASURED 2026-08-19: the 4am routine ends with a nav rebuild, and the night
    chain then rebuilds again the moment the routine's TSV changes. Two full
    passes, 11 GB written twice, and acquisition restarts 24 minutes late - the
    one thing the night was scheduled around.

    The table is current when the specification it is built FROM has not been
    written since the table was. That is the whole test: nav_build reads
    parcel_spec.db and nothing else, so if the db is older than the csv there is
    no input that could produce a different row.

    Refuses only a FULL rebuild. --bbl / --limit / --out are subset or
    redirected builds and always run; --force overrides unconditionally."""
    if a.force or a.bbl or a.limit or a.out:
        return False
    out = pathlib.Path(CP.NAV_TABLE)
    if not out.exists():
        return False
    # ⚠ THE MARKER, NOT THE CSV. A csv's mtime says "recently touched", which
    # is true of a file being written AND of one abandoned by a crash. Only a
    # run that reached the end writes _nav_build.done, so keying currency on the
    # marker makes "finished" and "merely recent" different facts. No marker
    # (first run, or a crash) -> rebuild, which is the safe direction.
    done = pathlib.Path(CP.NAV_WORK) / "_nav_build.done"
    if not done.exists():
        print("  no completion marker - rebuilding (a truncated table cannot "
              "be told from a finished one by mtime alone)")
        return False
    db = pathlib.Path(CP.SPEC_DB)
    if not db.exists():
        return False
    # ⚠ db AND -wal, NEVER -shm. Every write either lands in the db file (on
    # checkpoint) or in -wal (before it), so those two cover all writes. -shm is
    # shared-memory index touched whenever ANY connection opens - including a
    # read-only one, including nav_build's own - so including it would make the
    # guard see a newer source almost every time and never actually fire.
    src = max([db.stat().st_mtime]
              + [pathlib.Path(str(db) + x).stat().st_mtime
                 for x in ("-wal",)
                 if pathlib.Path(str(db) + x).exists()])
    if src <= done.stat().st_mtime:
        age = (time.time() - done.stat().st_mtime) / 60
        print(f"  navigation table is CURRENT - {out.name}")
        print(f"    built {age:.0f} min ago, {out.stat().st_size/1e6:,.0f} MB")
        print(f"    specification unchanged since - nothing could differ")
        print(f"    (pass --force to rebuild anyway)")
        return True
    return False


def _claim_lock(a):
    """⚠ TWO nav_build RUNS WOULD WRITE THE SAME 11 GB CSV AT ONCE.

    MEASURED RISK 2026-08-20 05:20: the 4am sync ends with a nav rebuild and
    night_watch runs one when it stops waiting at 06:00. The sync was still on
    its navigation stage at that hour, so both would have streamed to
    legal_instrument_navigation.csv simultaneously - not a slow build, a
    CORRUPT one, and nothing downstream would have said so.

    N-12 fixed the redundant rebuild by making the JOB idempotent rather than
    telling a scheduler to defer. Same move here: the job refuses to be the
    second copy. A pid file alone is not enough - a killed process leaves its
    file behind - so the recorded pid must be alive AND running nav_build.

    Subset builds (--bbl/--limit/--out) write elsewhere and never contend."""
    if a.bbl or a.limit or a.out:
        return True
    lock = pathlib.Path(CP.NAV_WORK) / "_nav_build.pid"
    try:
        import psutil
        if lock.exists():
            old = int((lock.read_text() or "0").strip() or 0)
            if old and old != os.getpid() and psutil.pid_exists(old):
                try:
                    cl = " ".join(psutil.Process(old).cmdline() or [])
                    if "nav_build.py" in cl:
                        print(f"  nav_build pid {old} is already rebuilding "
                              f"this table - refusing to be the second writer")
                        return False
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        lock.parent.mkdir(parents=True, exist_ok=True)
        lock.write_text(str(os.getpid()), encoding="utf-8")
        atexit.register(lambda: lock.exists() and lock.unlink())
    except Exception as e:
        # ⚠ UNLIKE only_one(), THIS SAYS SO. A guard that degrades to "allow"
        # in silence is how the duplicate-driver failure got through (N-14).
        print(f"  ⚠ nav_build lock unavailable ({type(e).__name__}: {e}) - "
              f"proceeding UNLOCKED; a concurrent rebuild would corrupt the csv")
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bbl", action="append")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--out")
    ap.add_argument("--force", action="store_true",
                    help="rebuild even when the table is already current")
    a = ap.parse_args()

    # ⚠ LOCK FIRST, CURRENCY SECOND. MEASURED 2026-08-20 06:00: the currency
    # guard ran first and declared a HALF-WRITTEN table "CURRENT - built 0 min
    # ago, 5,374 MB" while another nav_build was still streaming it toward
    # 11,268 MB. mtime says "recently touched", which a file being written
    # satisfies perfectly - so the freshest possible mtime is also the least
    # trustworthy one. Had this been the only run, a truncated csv would have
    # been left in place as live. Ask "is someone writing it?" BEFORE asking
    # "is it up to date?"
    if not _claim_lock(a):
        return
    if _already_current(a):
        return

    con = sqlite3.connect("file:" + str(CP.SPEC_DB).replace("\\", "/") + "?mode=ro",
                          uri=True, timeout=900)

    where, params = ["1=1"], []
    if a.bbl:
        where.append("d.document_id IN (SELECT document_id FROM parcel_document"
                     " WHERE bbl IN (%s))" % ",".join("?" * len(a.bbl)))
        params += a.bbl
    sql = ("SELECT d.document_id, d.doc_type, d.recorded_date, d.doc_date, d.amount,"
           " d.image_state, d.reel_yr, d.reel_nbr, d.reel_pg, d.microfilm,"
           " b.instrument, b.book, b.page"
           " FROM document d LEFT JOIN rc_binding b ON b.document_id=d.document_id"
           " WHERE " + " AND ".join(where) + " ORDER BY d.document_id")
    if a.limit:
        sql += " LIMIT %d" % a.limit

    # MERGE JOIN, NOT DICT LOADS. Holding every parcel link and every party in
    # memory is what made the first build time out - the corpus is ~20M documents
    # with more links and far more parties, and 16 GB will not hold it. All three
    # tables are indexed on document_id (document PK, ix_pd_doc, party_document
    # PK), so ordered scans merge in CONSTANT memory at any scale.
    def stream(q):
        cur = con.execute(q)
        row = cur.fetchone()
        while row is not None:
            did = row[0]; group = []
            while row is not None and row[0] == did:
                group.append(row[1:]); row = cur.fetchone()
            yield did, group

    # ⚠ THE INDEX IS THE CUSTODIAN'S DETAIL PAGE, NOT A SUMMARY OF IT.
    # Measured 2026-08-20: sync had already captured the whole page - PARCELS,
    # PARTY, REFERENCES and REMARKS each land in their own table - but nav was
    # emitting only type/date/amount and a name-plus-city per party. Everything
    # below was sitting in the specification, fully structured, and being
    # dropped on the floor at the last step:
    #   reference_document  11,899,912 rows over 7,986,145 documents
    #   remark_document      6,224,012 rows
    #   parcel_document     29,333,876 rows (air_rights Y on 26,768)
    #   party_document      19,458,713 rows (10,736,434 with a street address)
    # Air rights, easements and partial-lot flags are the whole business here;
    # references are what resolution chains documents WITH. All four tables are
    # indexed on document_id, so they merge in constant memory like the others.
    pd_it = stream("SELECT document_id, bbl, partial_lot, easement, air_rights,"
                   " subterranean, property_type FROM parcel_document"
                   " ORDER BY document_id")
    pa_it = stream("SELECT document_id, party_type, name, address_1, address_2,"
                   " city, state, zip, country FROM party_document"
                   " ORDER BY document_id")
    rf_it = stream("SELECT document_id, ref_crfn, ref_doc_id, reel_year,"
                   " reel_borough, reel_nbr, reel_page FROM reference_document"
                   " ORDER BY document_id")
    rm_it = stream("SELECT document_id, sequence_number, remark_text"
                   " FROM remark_document ORDER BY document_id")
    pd_cur = next(pd_it, None)
    pa_cur = next(pa_it, None)
    rf_cur = next(rf_it, None)
    rm_cur = next(rm_it, None)

    # ACRIS DOES NOT STORE image_state ON THE DOCUMENT ROW - it is NULL for every
    # ACRIS document. What ACRIS knows is the NO-IMAGE SET, kept as a flat id list
    # (174,142 ids, measured 2026-08-19). Reading only document.image_state makes
    # the whole ACRIS side read "unknown" and the completeness check
    # total - (present + pending + imageless) = 0 can never close.
    noimg = set()
    if CP.NOIMAGE_IDS.exists():
        with io.open(CP.NOIMAGE_IDS, encoding="utf-8", errors="replace") as nf:
            for ln in nf:
                ln = ln.strip()
                if ln:
                    noimg.add(ln)
        print(f"    {len(noimg):,} ACRIS ids known imageless", flush=True)

    out = pathlib.Path(a.out) if a.out else CP.NAV_TABLE
    out.parent.mkdir(parents=True, exist_ok=True)

    t0, n, unkeyed, keyed_by_party, keyed_by_doc = time.time(), 0, 0, 0, 0
    keyed_by_parcel = 0
    with out.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        # ⚠ THESE COLUMNS ARE THE PHASE CONTRACT (settled 2026-08-20):
        #   id        the document
        #   keyed_by  HOW it is keyed - parcel | party | doc
        #   key       the key itself
        #   index     every data point the custodian's detail page carries
        #   endpoint  where the image is fetched
        #   pdf       EMPTY until acquisition writes what it actually landed
        #
        # ⚠ pdf STARTS EMPTY AND THAT IS THE WHOLE POINT. It used to hold a
        # COMPUTED path (CP.STORE/<id>.tif) written for all 24M rows whether or
        # not a file existed, so "100% of rows have a pdf" was true BY
        # CONSTRUCTION and acquisition could report completion having fetched
        # nothing at all. Empty makes the acquisition gate a COUNT of files that
        # exist rather than a restatement of the path formula.
        # ⚠ TWO ENDPOINTS, SETTLED 2026-08-20 (login): the DETAIL url is
        # where the index came from; the IMAGE url is where the pdf comes from.
        # Both stored even though both are pure functions of the id - the table
        # is the phase CONTRACT, and a consumer should never need to know a
        # custodian URL formula to use it.
        # `doc_info` is the CUSTODIAN-NATIVE name (settled 2026-08-20): both
        # sources title the page "Document Information". The column is the
        # REGISTER'S OWN ENTRY about the document - their voice, not ours.
        # renamed doc_info -> recorded_details (login 2026-08-20: "recorded
        # details and RD endpoint - just saves space"); same content contract.
        # THE SWEEP CONTRACT (login, 2026-08-20): every artifact paired with
        # the endpoint that produces it. One row = one document's whole path:
        #   id            <- sync's deliverable
        #   id_endpoint   <- where the id resolves (RC: the doc-id search,
        #                    cold-valid; ACRIS: the detail page directly)
        #   keyed_by/key  <- how acquisition reaches it
        #   recorded_details + rd_endpoint  <- the register's entry + its page
        #   pdf + pdf_endpoint              <- acquisition's fill + its source
        # ⚠ Richmond's rd/pdf endpoints are SESSION-BOUND (shell/403 cold);
        # they are the true addresses, reached through id_endpoint's click-path.
        # FINAL (login, 2026-08-20, after the cold-browser test): once a
        # browser session exists, BOTH custodians' direct urls work - so two
        # endpoints per row answer everything. The Richmond doc-id search
        # entry (session establishment / fallback) lives in the md, not here.
        # COLUMN ORDER REVISED 2026-08-20 (login): key LAST - the keying walk
        # proved key is DERIVED from recorded_details + pdf, so the columns
        # read as the pipeline runs: identity, evidence, sources, conclusion.
        # nav_verify reads by NAME, so the reorder cannot silently break it.
        w.writerow(["id", "recorded_details", "rd_endpoint",
                    "pdf", "pdf_endpoint", "keyed_by", "key"])
        for (did, dtype, rec, dd, amt, img, ry, rn, rp, mfilm,
             instr, book, page) in con.execute(sql, params):
            while pd_cur is not None and pd_cur[0] < did:
                pd_cur = next(pd_it, None)
            while pa_cur is not None and pa_cur[0] < did:
                pa_cur = next(pa_it, None)
            while rf_cur is not None and rf_cur[0] < did:
                rf_cur = next(rf_it, None)
            while rm_cur is not None and rm_cur[0] < did:
                rm_cur = next(rm_it, None)
            pcl = pd_cur[1] if (pd_cur and pd_cur[0] == did) else []
            pp  = pa_cur[1] if (pa_cur and pa_cur[0] == did) else []
            rfs = rf_cur[1] if (rf_cur and rf_cur[0] == did) else []
            rms = rm_cur[1] if (rm_cur and rm_cur[0] == did) else []
            # ⚠ A NON-EMPTY LIST OF EMPTY STRINGS IS NOT A KEY. `if k:` was
            # true for [''], which writes an EMPTY key that still counts as
            # "keyed by parcel" - that counter was a subtraction and could never
            # see it. Censused 0 occurrences on 2026-08-20, but the census that
            # found it is not run daily, so the guard stays.
            k = [b for (b, *_r) in pcl if b]

            rc = did.startswith("RC_")
            if k:
                keyed_by = "parcel"
                keyed_by_parcel += 1
                key = ";".join(k)
            elif pp:
                key = ";".join("party:" + (x[1] or "") for x in pp if x[1])
                if key:
                    keyed_by = "party"
                    keyed_by_party += 1
                else:
                    keyed_by = "doc"
                    keyed_by_doc += 1
                    key = "doc:" + did
            else:
                # ⚠ NEITHER A PARCEL NOR A PARTY, AND STILL A REAL DOCUMENT.
                # Measured 2026-08-19: PAT 570, MISC 80, MAPS 27, SMIS 4, RPAT 3
                # per 300k - filed maps and miscellany that attach to no lot and
                # name no party. They must still be ACQUIRED, so they key to
                # themselves. An empty key would drop them from the corpus
                # silently, which is the one thing the phase gate exists to stop.
                keyed_by = "doc"
                keyed_by_doc += 1
                key = "doc:" + did

            if img:
                state = img
            elif did in noimg:
                state = "imageless"
            elif rc:
                state = "unknown"
            else:
                # ACRIS: not in the no-image set means an image is expected. The
                # URL is a pure function of the id, so nothing is stored per doc.
                state = "expected"
            ix = {"type": dtype or "", "recorded": rec or "", "executed": dd or "",
                  "image": state}
            # ⚠ AMOUNT IS CAPTURED FAITHFULLY - NO CLASS FILTER (REVERSED
            # 2026-08-20, same day). The first version omitted amount for six
            # "100% structural zero" classes - but that census read OUR captured
            # field, which for bulk-era ACRIS is the Socrata base index, and
            # cannot distinguish "the class has no amounts" from "the base
            # index is blind here" (login caught this). Capture is IRREVERSIBLE
            # compression; the per-class zero semantics (DEED $0 = real state,
            # DEVR $0 = never verifies, structural classes = information-free)
            # are VERIFIER rules in the extraction md and priors in the trust
            # ledger - revisable when extraction compares index vs document.
            # Bonus: no class set to match against a MIXED type namespace
            # ("TERM" bulk-era vs "UCC3 TERMINATION" live-era).
            if amt is not None and str(amt).strip() != "":
                ix["amount"] = amt
            if rc:
                if instr: ix["instrument"] = instr
                if book:  ix["book"] = book
                if page:  ix["page"] = page
                # ⚠ RICHMOND RD = DOC-ID INPUT + POST ACTION (measured
                # 2026-08-20): viewDocumentInfo renders only off a ONE-SHOT
                # grant minted by POSTing the results form - the grant is
                # consumed by its own redirect, so no static details URL can
                # exist. The stored address is therefore the doc-id search
                # (cold-valid, instrument slides in); the runner replays the
                # POST click from there. pdf_endpoint needs no such dance -
                # ViewContent substitutes directly and mints its own viewer.
                if instr:
                    ix_ep = (RC + "/search/ShowResultsDocumentNumberSearch/0"
                             "?DocumentNumber=" + str(instr)
                             + "&SelectedDocumentIdentifier=0")
                else:
                    ix_ep = RC + "/Search/viewDocumentInfo/" + did[3:]
                endpoint = RC + "/ViewVscmsDocument/ViewContent?p_endorsementId=" + did[3:]
            else:
                if ry and str(ry) not in ("0", ""): ix["reel"] = f"{ry}/{rn}/{rp}"
                if mfilm: ix["microfilm"] = 1
                ix_ep = ("https://a836-acris.nyc.gov/DS/DocumentSearch/"
                         "DocumentDetail?doc_id=" + did)
                endpoint = ("https://a836-acris.nyc.gov/DS/DocumentSearch/"
                            "DocumentImageView?doc_id=" + did)
            # PARCELS panel - the partial/easement/air-rights flags are the
            # reason this system exists; they were being discarded.
            if pcl:
                # ⚠ STORE WHAT VARIES, DROP WHAT THE CLASS DETERMINES (settled
                # 2026-08-20). The flags are Y-ONLY: measured, a Y is signal
                # (26,768 air-rights Ys corpus-wide) and an N establishes
                # NOTHING - the Domino DEVR reads N on every lot while moving
                # 215,858 SF of development rights. Storing 29.3M Ns would be
                # noise wearing the shape of data.
                _Y = ("Y", "y")
                ix["parcels"] = [
                    {kk: vv for kk, vv in (
                        {"bbl": b or "", "partial": pl or "", "use": use or "",
                         "easement": "Y" if es in _Y else "",
                         "air_rights": "Y" if ar in _Y else "",
                         "subterranean": "Y" if sb in _Y else ""}
                    ).items() if vv}
                    for (b, pl, es, ar, sb, use) in pcl]
            # PARTY panel - EVERY field the page carries, one key per field,
            # repeated across parties even when identical (login 2026-08-20:
            # "put all the party information and role, even if it repeats").
            # Joining addr+unit or city+state read cleaner but broke the
            # contract: the fields are the page's own columns, kept apart.
            if pp:
                ix["parties"] = [
                    {kk: vv for kk, vv in (
                        {"role": (pt or "").strip().upper() if rc else role_of(dtype, pt),
                         "name": nm or "",
                         "address": a1 or "", "address2": a2 or "",
                         "city": city or "", "state": st or "",
                         "zip": zp or "", "country": ctry or ""}
                    ).items() if vv}
                    for (pt, nm, a1, a2, city, st, zp, ctry) in pp]
            # REFERENCES panel - what RESOLUTION chains documents with.
            if rfs:
                ix["references"] = [
                    {kk: vv for kk, vv in (
                        {"crfn": rcrfn or "", "doc_id": rdoc or "",
                         "reel": "/".join(str(x) for x in (r_y, r_n, r_p) if x)}
                    ).items() if vv}
                    for (rcrfn, rdoc, r_y, r_b, r_n, r_p) in rfs]
            # REMARKS panel.
            if rms:
                _rm = [t for (_sq, t) in sorted(rms, key=lambda z: z[0] or 0) if t]
                if _rm:
                    ix["remarks"] = _rm

            w.writerow([did, json.dumps(ix, separators=(",", ":")),
                        ix_ep, "", endpoint, keyed_by, key])
            n += 1
            if n % 500000 == 0:
                el = max(time.time()-t0, 1)
                print(f"    {n:,} rows · {el:.0f}s · {n/el:,.0f}/s", flush=True)
    print(f"\n  {n:,} rows -> {out}")
    print(f"  {out.stat().st_size/1e6:.1f} MB · {(time.time()-t0)/60:.1f} min")
    # ⚠ COUNTED, NOT SUBTRACTED. n - party - doc can never be wrong, which
    # is exactly why it can never detect anything either.
    print(f"  keyed by parcel: {keyed_by_parcel:,}")
    print(f"  keyed by party : {keyed_by_party:,}")
    print(f"  keyed by doc   : {keyed_by_doc:,}  (no parcel, no party)")
    print(f"  UNKEYED: {unkeyed:,}  ({100*unkeyed/max(n,1):.3f}%)   <- phase gate: must be 0")
    con.close()
    # ⚠ LAST LINE OF A SUCCESSFUL FULL BUILD. Anything that aborts earlier
    # leaves no marker, so the next run rebuilds instead of trusting a partial.
    if not (a.bbl or a.limit or a.out):
        try:
            (pathlib.Path(CP.NAV_WORK) / "_nav_build.done").write_text(
                json.dumps({"rows": n, "bytes": out.stat().st_size,
                            "finished": time.strftime("%Y-%m-%dT%H:%M:%S"),
                            "unkeyed": unkeyed}), encoding="utf-8")
        except Exception as e:
            print(f"  ⚠ could not write completion marker: {type(e).__name__}")


if __name__ == "__main__":
    main()
