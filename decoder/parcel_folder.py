"""WHERE DOES A PARCEL'S RECORD LIVE ON DISK, AND HOW DOES IT STAY WALKABLE?

    ACRIS_CORPUS_ROOT=D:/acris python parcel_folder.py --bbl 4000110001
    ACRIS_CORPUS_ROOT=D:/acris python parcel_folder.py --bbl 4000110001 --dry

⚠ WHY THIS EXISTS. Login, 2026-08-17, looking at a directory of loose per-document
files: *"it has to be organized, otherwise it will be impossible to reason the
extraction if its all loose."* The store under `02-acquisition/documents/` is sharded
by doc-id prefix — correct for 17M files, useless for reading one parcel's history.
This builds the human view on top of it.

    02-acquisition/documents/FT/FT_4070002230107.pdf      the ONE copy
    02-acquisition/by-parcel/4/00011/0001/
        _INDEX.md                                          the whole record, in order
        1986-07-22__2160-1228__DEED__2160... .pdf          hardlink
        1986-07-22__2160-1231__DEED__2160... .pdf          hardlink

⚠ HARDLINKS, NOT COPIES. A document can touch hundreds of lots — the 2006 mortgage in
the Park Avenue South chain covered six across two boroughs, and blanket mortgages run
far longer. Copying would multiply the corpus by its own lot-fanout. On NTFS a hardlink
is a directory entry and costs no data. ⚠ NTFS caps links at 1023 per file; past that
the document is listed in `_INDEX.md` and not linked, so the manifest stays complete
even where the folder cannot.

⚠ DATE-FIRST FILENAMES SO THE FOLDER SORTS ITSELF. Explorer's default name sort then
IS the chronological walk — which is the entire point of organising by parcel.

⚠ THE MANIFEST IS BUILT FROM THE SPECIFICATION, NEVER FROM THE FETCH LEDGER. If it
were built from what landed, the 174,142 image-less documents would silently vanish and
the chronology would grow holes that nothing could see. They are interleaved with imaged
ones — the 1983/84 UCC-1 filings behind the IDA bonds and the 1986 UCC-3 that terminates
them sit between imaged deeds on Queens Block 11. `no_image` is a STATUS, not an
absence: for those documents the index IS the document, and we hold their full record
(legals + master + parties + refs + remarks) in `noimage_index/`.

⚠ ORDER BY document_date THEN recorded_date, never by document_id — the id prefix is an
intake stamp and precedes recording by five days on 2016081800161001.
"""
from __future__ import annotations

import argparse, gzip, json, os, pathlib, re, sqlite3, sys
import datetime as _dt          # ⚠ aliased: `dt` is a loop variable below
import time as _time            # ⚠ aliased for the same reason: `t` is a loop variable

import image_policy
import lineage

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = pathlib.Path(__file__).parent
import corpus_paths as CP
ROOT = CP.ROOT
SPEC = CP.SPEC
DB = CP.SPEC_DB
NOIMG = CP.NOIMAGE_INDEX / "master.jsonl.gz"
STORE = CP.STORE
BYPARCEL = CP.BYPARCEL

MAX_LINKS = 1023          # NTFS hard limit, not a policy choice
SAFE = re.compile(r"[^A-Za-z0-9._-]+")


_NOIMG_CACHE = None
_EMPTY_CACHE = None


def noimage_ids():
    """⚠ Loaded once PER PROCESS — the docstring said "loaded once" and the code reloaded
    it on every call. Harmless at one parcel (0.65 s); fatal under build_all, which calls
    build() 1,346,101 times. Measured 2026-08-19: 0.65 s x 1.35M = 243 hours of pure
    re-reading a gzip whose contents never change."""
    global _NOIMG_CACHE
    if _NOIMG_CACHE is not None:
        return _NOIMG_CACHE
    if not NOIMG.exists():
        _NOIMG_CACHE = set()
        return _NOIMG_CACHE
    out = set()
    with gzip.open(NOIMG, "rt", encoding="utf-8") as f:
        for line in f:
            try:
                d = json.loads(line).get("document_id")
            except ValueError:
                continue
            if d:
                out.add(d)
    _NOIMG_CACHE = out
    return out


def empty_ids():
    """Documents the fetcher PROVED have no image, by asking once and getting the
    placeholder back.

    ⚠ THE IMAGE-LESS INDEX IS INCOMPLETE AND THIS IS HOW WE LEARN THE REST.
    `noimage_index` holds 138,970 ids; the phase doc claims 174,142. Measured
    2026-08-17: FT_1610008670761 (a 1966 DEED, reel 40152/263) is absent from the index,
    returned the placeholder in 0.51s, and was written `empty`. Reported as "not
    acquired" it looks like work outstanding forever — a parcel that can never complete.
    It is not missing; it has no image, and the index row is its whole record.

    ⚠ BUT A PLACEHOLDER IS NOT PROOF WHILE THE SCAN MAY STILL BE COMING — returns
    (terminal, pending). `pending` and `imageless` are INDISTINGUISHABLE on any single
    read; only AGE separates them (image_policy.py, TERMINAL_DAYS=7, the one image
    policy for both sources). A document recorded three days ago that returned the
    placeholder has proved nothing — Richmond scans attach at a STEP around 24 h, and
    a late one lands on day 3 or day 6.

    Folding those in with the terminal set caused a SILENT PERMANENT LOSS, and every
    count read clean while it happened:

        placeholder -> ledger `empty` -> rendered "**no image** — index is the record"
        -> the parcel's manifest has no outstanding row -> overnight.py marks the
        parcel COMPLETE (it tests for `| not acquired |`) -> never queued again.

    So the image attaches on day 3 and nothing ever asks for it. Worse than a missed
    update: it writes a PERMANENT claim ("this document has no image, the index is its
    whole record") about a record nobody has finished looking at.

    Clock is the recorded date, falling back to when we first asked (the ledger's `at`),
    exactly as image_policy does — so a document with no usable date is never immortal.

    ⚠ CACHED PER PROCESS, AND THAT IS NOT AN OPTIMISATION — IT IS THE DIFFERENCE BETWEEN
    POSSIBLE AND NOT. Measured 2026-08-19: this costs **119 s per call**, because looking
    up the recorded_date of each `empty` row is ~2,800 random reads into an 8 GB spec DB
    on a USB drive (~42 ms each, cold). build() calls it once per parcel and build_all
    calls build() 1,346,101 times, so uncached this alone is ~44,500 HOURS. The answer is
    identical for every parcel in a run — compute it once."""
    global _EMPTY_CACHE
    if _EMPTY_CACHE is not None:
        return _EMPTY_CACHE
    led = CP.LEDGER
    if not led.exists():
        _EMPTY_CACHE = (set(), set())
        return _EMPTY_CACHE
    try:
        c = sqlite3.connect(f"file:{led}?mode=ro", uri=True)
        # ⚠ THE CLOCK COMES FROM THE SPECIFICATION, NOT THE LEDGER. The ledger knows
        # when WE asked; only the spec knows when the document was RECORDED, and that
        # is what the lag window is measured against. If the spec cannot be attached we
        # fall back to the ask date, which is conservative (it can only hold a document
        # pending longer, never retire one early).
        try:
            c.execute("ATTACH ? AS spec", (f"file:{DB}?mode=ro",))
            q = ("SELECT d.doc_id, d.at, s.recorded_date FROM doc d "
                 "LEFT JOIN spec.document s ON s.document_id = d.doc_id "
                 "WHERE d.status='empty'")
        except sqlite3.Error:
            q = "SELECT doc_id, at, NULL FROM doc WHERE status='empty'"
        today = _dt.date.today()
        terminal, pending = set(), set()
        for doc, asked_at, recorded in c.execute(q):
            if image_policy.is_terminal(today, recorded, asked_at):
                terminal.add(doc)
            else:
                pending.add(doc)
        c.close()
        _EMPTY_CACHE = (terminal, pending)
        return _EMPTY_CACHE
    except sqlite3.Error:
        # ⚠ DO NOT CACHE A FAILURE. An unreadable ledger is transient (the walk holds it
        # open); caching the empty answer would mark every remaining parcel's documents
        # "not acquired" for the rest of the process.
        return set(), set()


def rows(bbls):
    """Every document on this parcel ACROSS ITS LINEAGE, oldest first.

    ⚠ LEFT JOIN — a legals row whose master row is missing is still a document that
    exists, and dropping it would be exactly the invisible hole this file exists to
    prevent.

    ⚠ `bbls` IS THE FAMILY, NOT THE LOT. A BBL is a name and names get superseded:
    measured 2026-08-17 against DOF's Digital Alteration Book, 24,416 of the BBLs
    ACRIS has named are retired, and **545,345 documents sit under a retired name**.
    Keyed on the current BBL alone, a walk of 1010381002 reads 17 documents; its 121
    predecessor lots carry the rest of the story. Ordering is over the union, so a
    predecessor's 1969 deed sorts before the successor's 1986 one — which is the whole
    point of walking a parcel rather than a lot."""
    # ⚠ READ-ONLY, AND IT MATTERS. This builds a view; it has no business holding a
    # writable handle on the specification. A read-write connection also contends
    # with a live landing — measured 2026-08-19: `database is locked` while
    # rc_detail_land was mid-write. Under WAL a mode=ro reader does not block.
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    con.execute("PRAGMA busy_timeout=60000")
    qs = ",".join("?" * len(bbls))
    q = con.execute(f"""
        SELECT d.document_id, COALESCE(NULLIF(d.doc_date,''), d.recorded_date, '') AS dt,
               COALESCE(d.doc_type,''), COALESCE(d.amount,''),
               COALESCE(d.reel_nbr,''), COALESCE(d.reel_pg,''),
               COALESCE(pd.partial_lot,''), COALESCE(pd.easement,''),
               COALESCE(pd.air_rights,''), pd.bbl
        FROM parcel_document pd LEFT JOIN document d USING (document_id)
        WHERE pd.bbl IN ({qs}) ORDER BY dt, d.document_id""", list(bbls))
    # ⚠ DEDUPE ACROSS THE FAMILY. One instrument routinely names both a parent lot and
    # its children; counting it twice would inflate every merged parcel's record.
    seen, out = set(), []
    for r in q:
        if r[0] in seen:
            continue
        seen.add(r[0]); out.append(r)
    con.close()
    return out


def store_path(doc):
    """⚠ ONE STORE, TWO REGISTERS, TWO FORMATS. ACRIS ships bitonal page TIFFs which we
    assemble into a multi-page PDF. Richmond's viewer serves ONE whole-document JPEG PDF
    per document, compressed on arrival to a bitonal G4 TIFF — storing Richmond's PDFs
    as served is 20.3 TB against 1.2 TB compressed, so the .tif IS the stored form.

    ⚠ SHARDED THE SAME WAY ON PURPOSE. `rc_urls_ALL.csv` writes store_at flat
    (documents/RC_2825429.tif); this shards it (documents/RC/RC_2825429.tif) to match
    every other document in the store. Both sides must agree or acquired Richmond
    documents are invisible to every parcel folder — the index would print
    "not acquired" for a file sitting on disk."""
    ext = ".tif" if doc.startswith("RC_") else ".pdf"
    return STORE / doc[:2] / f"{doc}{ext}"


ACRIS_VIEW = "https://a836-acris.nyc.gov/DS/DocumentSearch/DocumentImageView?doc_id="
RC_VIEW = ("https://www.richmondcountyclerk.com/ViewVscmsDocument/"
           "ViewContent?p_endorsementId=")


def endpoint(doc):
    """The document's address at its custodian — DERIVED from the id, never stored.

    ⚠ TWO CUSTODIANS, TWO ROUTES, AND THEY ARE NOT INTERCHANGEABLE. ACRIS serves
    page images to any client; Richmond serves a whole-document PDF through a
    viewer that requires a real browser. The manifest prints the address so a
    parcel folder is self-sufficient — you can open any row without going back to
    the database — but WHICH client can follow it is a property of the source.

    ⚠ Derived, so it cannot go stale. The Richmond URL in particular must keep the
    `p_endorsementId` form: a resolved `?token=v2…` carries a signature that dies
    within minutes."""
    return (RC_VIEW + doc[3:]) if doc.startswith("RC_") else (ACRIS_VIEW + doc)


def link_name(dt, doc, ty, reel, pg):
    d = (dt or "0000-00-00")[:10] or "0000-00-00"
    t = SAFE.sub("-", ty or "UNK")[:24].strip("-") or "UNK"
    r = f"__{reel}-{pg}" if reel and pg and reel != "0" else ""
    ext = ".tif" if doc.startswith("RC_") else ".pdf"   # ⚠ must match store_path
    return f"{d}__{doc}__{t}{r}{ext}"


def build(bbl, dry=False, quiet=False):
    if not DB.exists():
        sys.exit(f"  no spec db at {DB} — run parcel_spec_db.py --build first")
    # ⚠ RESOLVE AT READ TIME. Acquisition files under the name the document states;
    # the walk gathers every name this parcel has ever had. family() is bbl + all
    # predecessors — never successors, which are a later, different parcel.
    fam = lineage.family(bbl)
    rs = rows(fam)
    if not rs:
        # ⚠ NOT AN ERROR IN BULK. A lot with no documents is an ordinary fact
        # (2,818 Richmond block numbers are genuinely empty); only the one-BBL
        # call treats it as a mistake worth stopping for.
        if quiet:
            return None
        sys.exit(f"  BBL {bbl} has no documents in the specification")
    terminal_empty, pending_scan = empty_ids()
    noimg = noimage_ids() | terminal_empty
    out = BYPARCEL / bbl[0] / bbl[1:6] / bbl[6:]
    if not dry:
        out.mkdir(parents=True, exist_ok=True)

    linked = held = missing = noimage = pending = 0
    lines = [f"# PARCEL {bbl[0]}-{int(bbl[1:6])}-{int(bbl[6:])}  ({bbl})", "",
             f"**{len(rs)} documents** in the ACRIS specification, oldest first.", "",
             (f"⚠ LINEAGE: this record spans **{len(fam)} lot names** — {bbl} plus "
              f"{len(fam)-1} predecessor lot(s) DOF records as having become it. "
              "Documents filed under a predecessor are marked `via <bbl>`."
              if len(fam) > 1 else
              "This parcel has no recorded predecessor lots in DOF's Alteration Book."),
             "",
             "⚠ `no image` is a STATUS, not a gap — for those documents the index is the",
             "whole record. `not acquired` means the image exists and has not been fetched.",
             "`pending scan` means we asked and got the placeholder while the document is",
             f"still inside the {image_policy.TERMINAL_DAYS}-day lag window — the scan may",
             "yet attach, so it counts as OUTSTANDING and this parcel is not complete.",
             "",
             "| doc id | index | endpoint | state |",
             "|---|---|---|---|"]

    for i, (doc, dt, ty, amt, reel, pg, part, esmt, air, under) in enumerate(rs, 1):
        if doc is None:
            continue
        src = store_path(doc)
        if doc in noimg:
            state = "**no image** — index is the record"; noimage += 1
        elif not src.exists():
            # ⚠ ORDER MATTERS: a pending document has no file on disk either, and if it
            # fell through to "not acquired" the parcel would at least stay outstanding
            # — but the manifest would assert "the image exists", which we do not know.
            if doc in pending_scan:
                state = "pending scan"; pending += 1
            else:
                state = "not acquired"; missing += 1
        else:
            dst = out / link_name(dt, doc, ty, reel, pg)
            if dst.exists():
                state = "acquired"; held += 1
            elif dry:
                state = "acquired"; linked += 1
            else:
                try:
                    os.link(src, dst)          # ⚠ hardlink: no bytes copied
                    state = "acquired"; linked += 1
                except OSError as e:
                    # ⚠ 1023-link ceiling, or a cross-volume store. The manifest still
                    # names the document; only the convenience link is absent.
                    state = f"acquired — not linked ({e.errno})"; held += 1
        flags = " ".join(x for x in (
            f"P:{part}" if part and part != "N" else "",
            "E" if esmt == "Y" else "", "A" if air == "Y" else "",
            # ⚠ NAME THE LOT IT WAS FILED UNDER when that is not this one. Without it a
            # predecessor's deed looks like a clerical error rather than lineage.
            f"via {under}" if under != bbl else "") if x)
        # index = the index details, one cell: date · type · amount · reel/pg · flags
        idx = " · ".join(x for x in (
            (dt or "")[:10], ty or "", (f"${amt}" if amt and amt not in ("0", "0.00") else ""),
            f"reel {reel}/{pg}" if reel and reel != "0" else "", flags) if x)
        lines.append(f"| `{doc}` | {idx or '—'} | [open]({endpoint(doc)}) | {state} |")

    lines += ["", "## COUNTS", "",
              f"- documents in specification: **{len(rs)}**",
              f"- acquired and linked here: **{linked + held}**",
              f"- image-less (index is the record): **{noimage}**",
              f"- image exists, not yet acquired: **{missing}**",
              f"- pending scan (inside the {image_policy.TERMINAL_DAYS}-day lag "
              f"window, re-ask): **{pending}**",
              f"- lot names in this parcel's lineage: **{len(fam)}**"]
    text = "\n".join(lines) + "\n"
    if not dry:
        (out / "_INDEX.md").write_text(text, encoding="utf-8")

    if not quiet:
        print(f"  BBL {bbl} -> {out}")
        print(f"    {len(rs)} documents   linked {linked}   already {held}   "
              f"no-image {noimage}   not-acquired {missing}   pending-scan {pending}")
    return out


def build_all(boro=None, skip_existing=True, limit=0, quiet=True):
    """MATERIALISE THE WHOLE MAP — every parcel in the specification, not just the
    ones acquisition happened to touch.

    ⚠ WHY THIS EXISTS. `--bbl` builds one parcel, so folders only ever appeared for
    parcels a walk had already reached: 7,624 of 1,346,101 (0.6%) as of 2026-08-19.
    That makes the by-parcel view a record of what was FETCHED rather than a map of
    what EXISTS — and the map is the thing you want to click into before deciding
    what to fetch.

    ⚠ THE MANIFEST IS BUILT FROM THE SPECIFICATION, so a parcel with nothing
    acquired still gets a complete _INDEX.md listing every document, each marked
    `not acquired` with its endpoint. That is the point: the folder answers "what
    is here and how do I reach it" before a single byte is pulled.

    ⚠ COVERS BOTH CUSTODIANS. store_path/link_name already branch on the RC_
    prefix, so Richmond documents land in the same parcel folders as ACRIS ones —
    which is the whole argument for the second source: on Staten Island the deed
    and its transfer-tax return live in different systems and belong in one folder.

    ⚠ RESUMABLE, because this is hours of work. `skip_existing` leaves a parcel
    whose manifest is already written; a landing that changes reachability DELETES
    the affected manifests (live_land.py, rc_detail_land.py), so skipping is safe —
    an absent manifest is the signal to rebuild."""
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    q = ("SELECT bbl FROM parcel WHERE bbl LIKE ? ORDER BY n_docs DESC"
         if boro else "SELECT bbl FROM parcel ORDER BY n_docs DESC")
    args = (f"{boro}%",) if boro else ()
    bbls = [r[0] for r in con.execute(q, args)]
    con.close()
    if limit:
        bbls = bbls[:limit]

    print(f"  parcels to materialise: {len(bbls):,}"
          + (f"  (borough {boro})" if boro else ""), flush=True)
    made = skipped = empty = failed = 0
    t0 = _time.time()
    for i, b in enumerate(bbls, 1):
        out = BYPARCEL / b[0] / b[1:6] / b[6:]
        if skip_existing and (out / "_INDEX.md").exists():
            skipped += 1
        else:
            try:
                if build(b, dry=False, quiet=quiet) is None:
                    empty += 1
                else:
                    made += 1
            except SystemExit:
                empty += 1          # no documents — not a failure, just an empty lot
            except Exception as e:
                failed += 1
                if failed <= 20:
                    print(f"    ⚠ {b}: {type(e).__name__}: {e}", flush=True)
        if i % 5000 == 0:
            el = _time.time() - t0
            rate = i / max(el, 1e-9)
            print(f"    {i:,}/{len(bbls):,} · made {made:,} · skipped {skipped:,} · "
                  f"empty {empty:,} · failed {failed:,} · {rate:.0f}/s · "
                  f"{(len(bbls)-i)/max(rate,1e-9)/60:.0f} min left", flush=True)
    # ⚠ denominators, always — and `failed` printed even at 0 so the line states
    # the check ran rather than staying silent.
    print(f"\n  DONE {(_time.time()-t0)/60:.1f} min")
    print(f"    materialised {made:,} · skipped {skipped:,} · "
          f"no documents {empty:,} · FAILED {failed:,}  of {len(bbls):,}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bbl", action="append")
    ap.add_argument("--all", action="store_true",
                    help="materialise every parcel in the specification")
    ap.add_argument("--boro", help="restrict --all to one borough digit (1-5)")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--rebuild", action="store_true",
                    help="rewrite manifests that already exist")
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    if a.all:
        build_all(boro=a.boro, skip_existing=not a.rebuild, limit=a.limit)
        return
    if not a.bbl:
        ap.error("--bbl or --all")
    for b in a.bbl:
        build(b.strip(), a.dry)


if __name__ == "__main__":
    main()
