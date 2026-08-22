"""Push the local JSONL sink into Supabase — the query surface.

WHY THIS EXISTS, AND WHY IT DID NOT UNTIL NOW

    `sink.py` writes append-only JSONL because that is the only format N
    concurrent decoders can share without locks or a server. Its docstring says
    "Supabase remains the query surface" — and then nobody built the bridge. As
    of 2026-08-06 there were **11,068 facts across BSA, DCP and LPC covering
    4,185 parcels**, plus a 1,175,952-row spine, entirely on local disk and
    invisible to the app.

    Local JSONL is the WRITE path. Supabase is the READ path. Both are needed;
    neither substitutes for the other.

⚠ IDEMPOTENT BY CONSTRUCTION

    Decoders re-run. A sync that INSERTs would multiply every fact by the number
    of times it was pushed, and nothing downstream could tell a duplicated fact
    from a repeated event — a parcel would appear to have been mortgaged four
    times because the sync ran four times.

    So every table has a natural key and every write is an UPSERT on it:

        parcels    bbl
        documents  (source, source_doc_id, bbl)
        facts      (source, source_doc_id, page, predicate, bbl)
        runs       (run_id, at)

    Re-running this script is always safe and always converges.

⚠ IT REPORTS DENOMINATORS

    "pushed 11,068 rows" is unverifiable. This prints rows read, rows sent, rows
    Supabase now holds, and whether those reconcile — because a partial push that
    reports success is the failure this project keeps meeting.
"""
import json, os, pathlib, sys, time, urllib.error, urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).parent))

ENV = r"C:/dev/acris-decoder.env"
SINK = pathlib.Path(os.environ.get("DECODER_SINK", r"C:\dev\decoder-sink"))
SPINE = pathlib.Path(os.environ.get("DECODER_SPINE",
                                    pathlib.Path(__file__).with_name("spine")))
BATCH = 500

# ---------------------------------------------------------------------------
# Run this ONCE in the Supabase SQL editor. PostgREST cannot create tables.
# ---------------------------------------------------------------------------
DDL = """
create table if not exists decoder_parcels (
  bbl text primary key,
  boro text, block int, lot int,
  kind text,                       -- tax_lot | condo_unit | condo_billing
  has_condo bool, has_reuc bool, has_air bool, has_sub bool, has_easement bool,
  status text default 'live',
  parent text, children text[],
  source text, unitsres numeric, address text,
  updated_at timestamptz default now()
);
create index if not exists decoder_parcels_block on decoder_parcels(boro, block, lot);
create index if not exists decoder_parcels_parent on decoder_parcels(parent);

create table if not exists decoder_documents (
  source text not null,
  source_doc_id text not null,
  bbl text not null default '',
  doc_type text, happened date, recorded date, reel text,
  decode_status text default 'unread',   -- unread|queued|decoding|decoded|FAILED
  pages_total int, pages_read int default 0,
  parser_version int, run_id text,
  updated_at timestamptz default now(),
  primary key (source, source_doc_id, bbl)
);
create index if not exists decoder_documents_bbl on decoder_documents(bbl);
create index if not exists decoder_documents_status on decoder_documents(source, decode_status);

-- ⚠ fact_hash IS PART OF THE KEY, and that is not a detail.
--
-- The first version keyed on (source, doc, page, predicate, bbl). Measured
-- against the real sink: 13,299 fact lines collapsed to 8,032 keys, with 5,857
-- keys holding MORE THAN ONE fact. BSA decision 2024-32-BZ has 52
-- `condition_imposed` rows on page 17, of which 13 are genuinely different
-- conditions — "no vehicle deliveries along Hylan Boulevard" and "451 square
-- feet of accessory signage" are not the same fact. That key would have kept
-- ONE OF THIRTEEN and reported a successful sync.
--
-- The key must do two opposing jobs: COLLAPSE identical re-emissions from
-- decoder re-runs, and PRESERVE distinct facts sharing a page. Only content can
-- tell those apart, so the hash covers the substance (verbatim/value/parties),
-- never the run metadata.
create table if not exists decoder_facts (
  source text not null,
  source_doc_id text not null,
  page text not null,
  predicate text not null,
  bbl text not null default '',
  fact_hash text not null,
  happened date, recorded date,
  value numeric, unit text, parameter text,
  parties jsonb, confidence text, derivation text, verbatim text,
  parser int, run_id text, extra jsonb,
  updated_at timestamptz default now(),
  primary key (source, source_doc_id, page, predicate, bbl, fact_hash)
);
create index if not exists decoder_facts_bbl on decoder_facts(bbl, happened);
create index if not exists decoder_facts_pred on decoder_facts(predicate);
create index if not exists decoder_facts_src on decoder_facts(source, bbl);

-- ---------------------------------------------------------------------------
-- PER-SOURCE SPINE CROSSING (Login, 2026-08-06: "BSA, DCP, LPC get a spine they
-- can attach parcel level information to").
--
-- VIEWS, not tables. A copied table is stale the moment either side changes and
-- gives every decoder its own drifting version of the parcel universe — which
-- is the opposite of a shared spine. A view is always current and costs nothing
-- to keep in step.
-- ---------------------------------------------------------------------------
create or replace view decoder_parcel_source as
select p.bbl, p.boro, p.block, p.lot, p.kind, p.parent, p.address, p.unitsres,
       f.source,
       count(*)                              as facts,
       count(distinct f.source_doc_id)       as documents,
       min(coalesce(f.happened, f.recorded)) as first_event,
       max(coalesce(f.happened, f.recorded)) as last_event,
       array_agg(distinct f.predicate)       as predicates
from decoder_parcels p
join decoder_facts f on f.bbl = p.bbl
group by p.bbl, p.boro, p.block, p.lot, p.kind, p.parent, p.address,
         p.unitsres, f.source;

create or replace view decoder_bsa_parcels as
  select * from decoder_parcel_source where source = 'BSA';
create or replace view decoder_dcp_parcels as
  select * from decoder_parcel_source where source = 'DCP';
create or replace view decoder_lpc_parcels as
  select * from decoder_parcel_source where source = 'LPC';
create or replace view decoder_acris_parcels as
  select * from decoder_parcel_source where source = 'ACRIS';
create or replace view decoder_dob_parcels as
  select * from decoder_parcel_source where source like 'DOB%';

-- every parcel ANY decoder has touched, with per-source coverage side by side.
-- ⚠ a source absent from a row means NOT LOOKED AT, never "nothing there" —
-- that distinction is the whole reason decoder_documents exists separately.
create or replace view decoder_parcel_coverage as
select p.bbl, p.kind, p.address,
       count(distinct f.source)                                as sources,
       count(*) filter (where f.source = 'BSA')                as bsa,
       count(*) filter (where f.source = 'DCP')                as dcp,
       count(*) filter (where f.source = 'LPC')                as lpc,
       count(*) filter (where f.source = 'ACRIS')              as acris,
       count(*) filter (where f.source like 'DOB%')            as dob,
       count(*) filter (where f.source = 'DOS')                as dos
from decoder_parcels p
join decoder_facts f on f.bbl = p.bbl
group by p.bbl, p.kind, p.address;

create table if not exists decoder_runs (
  run_id text not null, at bigint not null,
  source text, done int, total int, status text, note text,
  primary key (run_id, at)
);
"""


def _env():
    v = {}
    for line in open(ENV, encoding="utf-8"):
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, val = line.split("=", 1)
            v[k.strip()] = val.strip()
    return v["ACRIS_SUPABASE_URL"], v["ACRIS_SUPABASE_SERVICE_KEY"]


def _post(table, rows, on_conflict, attempts=5):
    """⚠ A TRANSIENT SSL DROP USED TO ABORT THE WHOLE SYNC.

    Pushing 360,000 document rows takes long enough that one connection will
    fail — measured: `URLError: EOF occurred in violation of protocol` at row
    ~250k. That exception propagated out of push(), out of main, and killed the
    process, so the run reported nothing at all about the 250,000 rows it had
    already landed. A partial success that reports as a total failure is the
    same defect as a partial failure that reports as success: the number you
    are shown does not describe what happened.

    Every write here is an idempotent upsert, so retrying a chunk is always
    safe — it either lands for the first time or merges over itself.
    """
    base, key = _env()
    body = json.dumps(rows).encode("utf-8")
    last = None
    for n in range(attempts):
        try:
            req = urllib.request.Request(
                f"{base}/rest/v1/{table}?on_conflict={on_conflict}", data=body,
                headers={"apikey": key, "Authorization": "Bearer " + key,
                         "Content-Type": "application/json",
                         "Prefer": "resolution=merge-duplicates,return=minimal"},
                method="POST")
            with urllib.request.urlopen(req, timeout=180) as f:
                return f.status
        except urllib.error.HTTPError as e:
            if e.code < 500:
                raise                    # a 4xx is our bug, not the network's
            last = e
        except Exception as e:           # URLError, socket timeout, SSL EOF
            last = e
        time.sleep(min(2 ** n, 30))
    raise last


def count(table):
    base, key = _env()
    req = urllib.request.Request(
        f"{base}/rest/v1/{table}?select=*",
        headers={"apikey": key, "Authorization": "Bearer " + key,
                 "Prefer": "count=exact", "Range": "0-0"})
    try:
        with urllib.request.urlopen(req, timeout=60) as f:
            cr = f.headers.get("Content-Range") or "0-0/0"
            return int(cr.split("/")[-1])
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None                      # table does not exist yet
        raise


def push(table, rows, on_conflict, label):
    """Batched upsert. Reports read / sent / held, and whether they reconcile."""
    before = count(table)
    if before is None:
        print(f"  {label:<20} TABLE MISSING — run the DDL first (--ddl)")
        return False
    sent = 0
    for i in range(0, len(rows), BATCH):
        chunk = rows[i:i + BATCH]
        try:
            _post(table, chunk, on_conflict)
            sent += len(chunk)
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "ignore")[:200]
            print(f"  {label:<20} FAILED at row {i}/{len(rows):,}: "
                  f"{e.code} {detail}")
            print(f"  {label:<20} landed {sent:,} before failing — the push is "
                  f"an upsert, so re-running resumes safely")
            return False
        except Exception as e:
            print(f"  {label:<20} FAILED at row {i}/{len(rows):,} after "
                  f"retries: {type(e).__name__}: {e}")
            print(f"  {label:<20} landed {sent:,} before failing — re-run to "
                  f"resume; every write is idempotent")
            return False
        if sent % 5000 == 0:
            print(f"    {label}: {sent:,}/{len(rows):,}")
    after = count(table)
    print(f"  {label:<20} read {len(rows):>9,}  sent {sent:>9,}  "
          f"held {after:>9,}  (+{after - before:,})")
    return sent == len(rows)


def _read(path, limit=None):
    if not path.exists():
        return []
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            try:
                out.append(json.loads(line))
            except Exception:
                continue
            if limit and len(out) >= limit:
                break
    return out


def fact_hash(r):
    """Identity of a fact's SUBSTANCE — never its run metadata.

    Two emissions of the same reading must collapse; two different conditions on
    one page must not. Only content distinguishes them, so the hash covers what
    the fact ASSERTS (verbatim, value, unit, parameter, parties, dates) and
    deliberately excludes run_id, emitted_at and parser — a re-run under a new
    parser is the same fact, not a new one.
    """
    import hashlib
    payload = json.dumps({
        "verbatim": (r.get("verbatim") or "").strip(),
        "value": r.get("value"), "unit": r.get("unit"),
        "parameter": r.get("parameter"), "parties": r.get("parties") or [],
        "happened": r.get("happened"), "recorded": r.get("recorded"),
        "derivation": (r.get("derivation") or "").strip(),
    }, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def sync_facts(include_retracted=False):
    """⚠ THIS FUNCTION USED TO PUSH RETRACTED FACTS, AND DID SO 20,895 TIMES.

    It read `facts.jsonl` raw. The sink is append-only, so a fact withdrawn by
    `sink.retract()` is still a line in that file — retraction is applied by
    `sink.facts()`, and this bypassed it. Measured 2026-08-06: every one of the
    20,895 rows in decoder_facts was written by a parser that had since been
    retracted, including 10,898 DCP rows sourced from a case-management detail
    screen rather than a document.

    Worse, the push DROPPED the per-source parser stamp. `parser` is
    facts.PARSER (9 for everything) and `extra` was never populated, so nothing
    in the query surface could distinguish a bsa/3 row from a bsa/6 row. The
    local sink could answer "which parser wrote this"; Supabase could not, which
    made the retraction unenforceable exactly where it mattered most — the read
    path the app uses.

    So: retractions are applied here by default, and the per-source parser
    version travels with the row in `extra`.
    """
    import sink as _sink
    rows = _sink.facts(include_retracted=include_retracted)
    raw = len(_sink.facts(include_retracted=True))
    if raw != len(rows):
        print(f"  ({raw - len(rows):,} retracted fact lines withheld — "
              f"see retractions.jsonl for why)")
    seen, out = set(), []
    for r in rows:
        h = fact_hash(r)
        for b in (r.get("bbls") or [""]):
            k = (r.get("source"), r.get("document_id"), str(r.get("page")),
                 r.get("predicate"), str(b), h)
            if k in seen:
                continue          # de-dupe INSIDE the batch too; Postgres rejects
            seen.add(k)           # a batch containing the same key twice
            out.append({"source": r.get("source"), "source_doc_id": r.get("document_id"),
                        "page": str(r.get("page")), "predicate": r.get("predicate"),
                        "bbl": str(b), "fact_hash": h, "happened": r.get("happened"),
                        "recorded": r.get("recorded"), "value": r.get("value"),
                        "unit": r.get("unit"), "parameter": r.get("parameter"),
                        "parties": r.get("parties"), "confidence": r.get("confidence"),
                        "derivation": r.get("derivation"), "verbatim": r.get("verbatim"),
                        "parser": r.get("parser"), "run_id": r.get("run_id"),
                        # per-source parser lineage and the provenance flags a
                        # reader needs to judge the row. `parser` alone is
                        # facts.PARSER and is 9 on every row from every source.
                        "extra": {k: r[k] for k in
                                  ("bsa_parser", "lpc_parser", "dcp_source",
                                   "bbl_provenance", "pages_read", "pages_total",
                                   "scope", "applies_to", "outcome_source",
                                   "zr_section", "work_kinds", "is_enlargement")
                                  if r.get(k) is not None} or None})
    # ⚠ PRINT BOTH REDUCTIONS. The location-only key collapsed 13,299 lines to
    # 8,032 and destroyed 13 distinct conditions on a single BSA page. Showing
    # what each key WOULD keep is how that stayed visible instead of silent.
    loc = len({(r.get("source"), r.get("document_id"), str(r.get("page")),
                r.get("predicate"), str(b))
               for r in rows for b in (r.get("bbls") or [""])})
    print(f"  ({len(rows):,} fact lines -> {len(out):,} kept with content hash; "
          f"a location-only key would have kept {loc:,} — "
          f"{len(out) - loc:,} distinct facts saved)")
    return push("decoder_facts", out,
                "source,source_doc_id,page,predicate,bbl,fact_hash", "facts")


def sync_documents():
    rows = _read(SINK / "documents.jsonl")
    # ⚠ SUPERSEDED DCP KEY FORMAT. DCP document rows written before
    # 2026-08-06 used the bare filename as source_doc_id, and a DCP filename is
    # not unique — `LandUse.pdf` belongs to 2,049 different projects. Those rows
    # merge unrelated documents under one key. The corrected form is
    # "{project_id}/{filename}", so a DCP id with no slash is the old shape and
    # is withheld. The sink is append-only; this is how a bad key is retired.
    dropped = sum(1 for r in rows if r.get("source") == "DCP"
                  and "/" not in str(r.get("source_doc_id") or ""))
    if dropped:
        print(f"  ({dropped:,} DCP document rows withheld — superseded key "
              f"format, bare filename is not unique)")
    rows = [r for r in rows if not (r.get("source") == "DCP"
                                    and "/" not in str(r.get("source_doc_id") or ""))]
    seen, out = set(), []
    for r in rows:
        for b in (r.get("bbls") or [""]):
            k = (r.get("source"), r.get("source_doc_id"), str(b))
            if k in seen:
                continue
            seen.add(k)
            out.append({"source": r.get("source"), "source_doc_id": r.get("source_doc_id"),
                        "bbl": str(b), "doc_type": r.get("doc_type"),
                        "happened": r.get("happened"), "recorded": r.get("recorded"),
                        "reel": r.get("reel"), "decode_status": r.get("decode_status"),
                        "pages_total": r.get("pages_total"),
                        "pages_read": r.get("pages_read"), "run_id": r.get("run_id"),
                        # the join back to HOW this document is retrieved
                        "document_stream": _streams().get(r.get("source"))})
    return push("decoder_documents", out, "source,source_doc_id,bbl", "documents")


def _streams():
    try:
        import retrieval
        return retrieval.DOCUMENT_STREAM
    except Exception:
        return {}


def sync_runs():
    rows = _read(SINK / "runs.jsonl")
    seen, out = set(), []
    for r in rows:
        k = (r.get("run_id"), r.get("at"))
        if k in seen:
            continue
        seen.add(k)
        out.append({"run_id": r.get("run_id"), "at": r.get("at"),
                    "source": r.get("source"), "done": r.get("done"),
                    "total": r.get("total"), "status": r.get("status"),
                    "note": r.get("note")})
    return push("decoder_runs", out, "run_id,at", "runs")


def referenced_bbls():
    """Every BBL any decoder has actually touched — facts + documents.

    ⚠ THIS EXISTS BECAUSE PUSHING THE WHOLE SPINE FILLED THE DATABASE.
    Measured 2026-08-06: the push died at row 93,500 of 1,175,952 with
    `53100: could not extend file — No space left on device`, and the facts
    table referenced only a few thousand distinct parcels. **Over 99% of the
    rows being loaded supported nothing.**

    The spine is 1.17M parcels because NYC has 1.17M parcels — that is correct
    as a local INDEX (274 MB on disk, instant to walk). It is wrong as a hosted
    TABLE, where storage is metered and every row costs. The spine's job is to
    answer "does this BBL exist and what is it"; a decoder asks that locally
    before it writes, and Supabase only ever needs the parcels something points
    at.

    So: materialise on demand. A parcel enters `decoder_parcels` when a fact or
    a document row references it, never before.
    """
    out = set()
    for f in _read(SINK / "facts.jsonl"):
        for b in (f.get("bbls") or []):
            if b:
                out.add(str(b))
    for d in _read(SINK / "documents.jsonl"):
        for b in (d.get("bbls") or []):
            if b:
                out.add(str(b))
    return out


def sync_spine_referenced():
    """Push ONLY the parcels that something references. The default path."""
    want = referenced_bbls()
    if not want:
        print("  no parcels referenced yet — nothing to materialise")
        return True
    rows, seen = [], set()
    with open(SPINE / "spine.jsonl", encoding="utf-8") as f:
        for line in f:
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r["bbl"] in want and r["bbl"] not in seen:
                seen.add(r["bbl"])
                rows.append(r)
    missing = want - seen
    print(f"  {len(want):,} parcels referenced · {len(rows):,} found in the spine"
          + (f" · ⚠ {len(missing):,} REFERENCED BUT NOT IN THE SPINE" if missing else ""))
    if missing:
        # a decoder wrote a fact against a BBL the spine does not contain —
        # that is a finding about the spine (retired lot? bad key?), not a
        # rounding error. Name a few so it can be chased.
        print(f"    e.g. {sorted(missing)[:6]}")
    out = [{"bbl": r["bbl"], "boro": str(r.get("boro") or ""),
            "block": r.get("block"), "lot": r.get("lot"), "kind": r.get("kind"),
            "has_condo": bool(r.get("has_condo")), "has_reuc": bool(r.get("has_reuc")),
            "has_air": bool(r.get("has_air")), "has_sub": bool(r.get("has_sub")),
            "has_easement": bool(r.get("has_easement")),
            "status": r.get("status"), "parent": r.get("parent"),
            "children": r.get("children") or [], "source": r.get("source"),
            "unitsres": r.get("unitsres"), "address": r.get("address")}
           for r in rows]
    return push("decoder_parcels", out, "bbl", "parcels(referenced)")


def sync_spine(limit=None):
    """⚠ THE FULL 1.17M PUSH. This filled the database on 2026-08-06 — use
    sync_spine_referenced() instead unless you have deliberately provisioned
    the storage."""
    rows = _read(SPINE / "spine.jsonl", limit=limit)
    out = [{"bbl": r["bbl"], "boro": str(r.get("boro") or ""),
            "block": r.get("block"), "lot": r.get("lot"), "kind": r.get("kind"),
            "has_condo": bool(r.get("has_condo")), "has_reuc": bool(r.get("has_reuc")),
            "has_air": bool(r.get("has_air")), "has_sub": bool(r.get("has_sub")),
            "has_easement": bool(r.get("has_easement")),
            "status": r.get("status"), "parent": r.get("parent"),
            "children": r.get("children") or [], "source": r.get("source"),
            "unitsres": r.get("unitsres"), "address": r.get("address")}
           for r in rows]
    return push("decoder_parcels", out, "bbl", "parcels")


if __name__ == "__main__":
    a = sys.argv[1:]
    if "--ddl" in a:
        print(DDL)
        print("-- paste the above into the Supabase SQL editor, then re-run "
              "without --ddl")
        raise SystemExit(0)
    print("SUPABASE SYNC\n")
    ok = True
    if "--spine" in a:
        lim = next((int(x) for x in a if x.isdigit()), None)
        ok &= bool(sync_spine(limit=lim))
    else:
        # each table reports independently — one failing must not hide the
        # others' results, and must not stop them being attempted
        results = {}
        for name, fn in (("runs", sync_runs), ("documents", sync_documents),
                         ("facts", sync_facts)):
            try:
                results[name] = bool(fn())
            except Exception as e:
                print(f"  {name:<20} ABORTED: {type(e).__name__}: {e}")
                results[name] = False
            ok &= results[name]
        print("\n  per-table:", ", ".join(
            f"{k}={'ok' if v else 'INCOMPLETE'}" for k, v in results.items()))
        print("\n  (spine is 1.17M rows — push it separately with --spine)")
    print(f"\n  {'✓ all pushes reconciled' if ok else '✗ SOMETHING DID NOT RECONCILE'}")
