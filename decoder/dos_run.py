"""The DOS run — party names in, a DOCUMENT LEDGER out.

⚠⚠ THIS RUN WRITES NO FACTS, AND THAT IS DELIBERATE

    The first version of this file emitted `entity_registered`,
    `entity_dissolved` and `service_address_known` straight from the Socrata
    register. RULE_DOCUMENTS_NOT_INDEXES forbids it, and is right to:

        an index row tells you a document EXISTS. Only the document tells you
        what it SAYS.

    Every DOS column read here — corp_name, date_filed, documenttype, film_num,
    dos_process_address_1 — is the register's SUMMARY of a filed instrument that
    has never been opened. "1000 SECOND AVENUE LLC dissolved 2002-08-21" is not
    a decode of the ARTICLES OF DISSOLUTION; it is a citation to somebody else's
    abstract of a document I have not read.

    ⚠ ACCESS IS UNRESOLVED. The filing images live on apps.dos.ny.gov, which
    closes the connection on its own robots.txt — no published policy, exactly
    like the DOB hosts. Absence of a policy is not permission, and this project
    does not probe to find a limit. So the documents stay unread until the
    question is ASKED, and until then this run does the one thing an index is
    legitimately for: recording WHAT EXISTS so the gap is countable.

    What that buys, per LEDGER_SCHEMA: "no facts from DOS" and "these filings
    exist and none has been opened" stop looking alike.

WHY THE INPUT IS NOT THE SINK
    The kickoff says "resolve every party name already in the sink". Measured
    2026-08-06: the sink held 3,131 facts, all BSA, and ZERO parties — the BSA
    decoder writes premises and job numbers, not names. Resolving that set would
    have produced a 0/0 match rate, which reads as success.

    So the names come from ACRIS's FREE party index (636b-3b5g), scoped to the
    1,879 rights instruments that LEDGER_SCHEMA ranks priority 1. That is a
    denominator that can be printed.

WHAT A DOS DOCUMENT IS
    Not a property document — no DOS filing names a block or lot. Each is a
    corporate instrument with a microfilm number: ARTICLES OF ORGANIZATION,
    APPLICATION OF AUTHORITY, CERTIFICATE OF AMENDMENT, ARTICLES OF DISSOLUTION,
    SURRENDER OF AUTHORITY, CERTIFICATE OF MERGER. The parcels ride along
    because the entity signed an ACRIS instrument about them.

THREE OUTCOMES, ALWAYS
    ok / empty / FAILED. An entity absent from the ACTIVE index is not a
    failure and not a blank — it is very often DISSOLVED, and the filings table
    says so with a date.
"""
import json, pathlib, re, sys, time, collections

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import bulk, dos, facts, sink

MASTER, LEGALS, PARTIES = "bnx9-e6tj", "8h5j-fqxa", "636b-3b5g"
RIGHTS = ("DEVR", "AIRRIGHT", "LIC", "DEED, RC")

# Classification runs on the RAW name — every one of these tests needs the
# punctuation that normalize() removes. Three bugs in one session came from
# forgetting that; see the dos.py docstring.
CORP = re.compile(r"\b(LLC|L\.L\.C|INC|CORP|CORPORATION|COMPANY|CO|LP|L\.P|LLP|LTD|"
                  r"LIMITED|ASSOCIATES|ASSOCIATION|PARTNERS|HOLDINGS|REALTY|TRUST|"
                  r"FUND|GROUP|PROPERTIES|DEVELOPMENT)\b", re.I)
PERSON = re.compile(r"^[A-Z][A-Za-z'’\- ]+,\s*[A-Z][A-Za-z'’\-. ]*$")
GOVT = re.compile(r"\b(CITY OF NEW YORK|HOUSING AUTHORITY|TRANSPORTATION AUTHORITY|"
                  r"STATE OF NEW YORK|PORT AUTHORITY|BOARD OF EDUCATION|UNITED STATES|"
                  r"DEPARTMENT OF|BOARD OF MANAGERS|MTA )\b", re.I)
CHURCH = re.compile(r"\b(CHURCH|SYNAGOGUE|TEMPLE|DIOCESE|PARISH|CEMETERY|CONGREGATION|"
                    r"MOSQUE|MINISTR)\b", re.I)
ESTATE = re.compile(r"\b(ESTATE OF|DECEASED|AS TRUSTEE|EXECUTOR|HEIRS)\b", re.I)


def classify(raw):
    if ESTATE.search(raw):
        return "estate / trustee capacity"
    if GOVT.search(raw):
        return "government or public authority"
    if CHURCH.search(raw):
        return "religious or cemetery corporation"
    if PERSON.match(raw) and not CORP.search(raw):
        return "individual"
    return "corporate entity"


def universe():
    """The rights instruments, their parcels, and their party names."""
    docs = []
    for t in RIGHTS:
        docs += bulk.socrata(MASTER, where=f"doc_type='{t}'",
                             select="document_id,doc_type,document_date,"
                                    "recorded_datetime,document_amt")
    ids = [d["document_id"] for d in docs]
    legals = bulk.socrata_in(LEGALS, "document_id", ids,
                             select="document_id,borough,block,lot")
    parties = bulk.socrata_in(PARTIES, "document_id", ids)
    bbls = collections.defaultdict(set)
    for l in legals:
        try:
            b = f"{int(l['borough'])}{int(l['block']):05d}{int(l['lot']):04d}"
        except Exception:
            continue
        bbls[l["document_id"]].add(b)
    return docs, parties, {k: sorted(v) for k, v in bbls.items()}


def resolve_active_stream(names, page_size=50000):
    """Scan the whole ACTIVE register, normalising BOTH sides. AUTHORITATIVE.

    4,260,763 rows, ~8 minutes, 86 requests. Slow, and correct, and the reason
    it is the default is below.
    """
    want = {}
    for n in names:
        want.setdefault(dos.normalize(n), []).append(n)
    hits, off = collections.defaultdict(list), 0
    while True:
        rows = dos.soql(dos.ENTITIES, limit=page_size, offset=off, order=":id",
                        select="dos_id,current_entity_name,initial_dos_filing_date,"
                               "entity_type,county,jurisdiction,dos_process_name,"
                               "dos_process_address_1,dos_process_city,"
                               "dos_process_state,dos_process_zip")
        if not rows:
            break
        for r in rows:
            k = dos.normalize(r.get("current_entity_name"))
            if k in want:
                hits[k].append(r)
        off += len(rows)
        if off % 1000000 == 0:
            print(f"      scanned {off:,} · matched {len(hits):,}")
        if len(rows) < page_size:
            break
    return hits, 0, [], off


def resolve_active(names, chunk=20):
    """Prefix-batched lookup in the ACTIVE entity index — the FAST path.

    ⚠ MEASURED SHORTFALL, 2026-08-06. Over the same 2,486 corporate names this
    finds 1,518 where the full stream finds 1,695 — it misses 177, about 7% of
    the denominator, because 121 names reduce to a prefix too short to search
    and others sit behind prefixes broad enough to truncate.

    An earlier docstring here claimed the two methods "find the same set". They
    do not, and nothing in the output would have shown it: the fast path returns
    a large plausible number and no error. Kept only for a quick pass, never for
    a reported rate.
    """
    want = {}
    for n in names:
        want.setdefault(dos.normalize(n), []).append(n)
    pre = {}
    for k in want:
        p = dos.search_prefix(k)
        if p:
            pre.setdefault(p, []).append(k)
    unreachable = [k for k in want if not dos.search_prefix(k)]
    hits, capped = collections.defaultdict(list), 0
    keys = sorted(pre)
    for i in range(0, len(keys), chunk):
        part = keys[i:i + chunk]
        clause = " OR ".join("starts_with(upper(current_entity_name),'"
                             + p.replace("'", "''") + "')" for p in part)
        rows = dos.soql(dos.ENTITIES, where=clause, limit=5000)
        if len(rows) >= 5000:
            capped += 1
        for r in rows:
            k = dos.normalize(r.get("current_entity_name"))
            if k in want:
                hits[k].append(r)
    return hits, capped, unreachable


def run(scope_limit=None, fast=False):
    run_id = f"dos-{int(time.time())}"
    print(f"run {run_id}\n")

    docs, parties, doc_bbls = universe()
    names = sorted({p["name"].strip() for p in parties if (p.get("name") or "").strip()})
    print(f"universe: {len(docs):,} rights instruments · {len(parties):,} party rows "
          f"· {len(names):,} distinct names")
    print(f"          {sum(len(v) for v in doc_bbls.values()):,} document-parcel links "
          f"on {len(doc_bbls):,} documents")

    kind = {n: classify(n) for n in names}
    for k, c in collections.Counter(kind.values()).most_common():
        print(f"   {c:>5}  ({c/len(names):>5.1%})  {k}")
    corps = [n for n in names if kind[n] == "corporate entity"]
    if scope_limit:
        corps = corps[:scope_limit]
    by_key = {}
    for n in corps:
        by_key.setdefault(dos.normalize(n), []).append(n)
    TOTAL = len(by_key)
    print(f"\nDENOMINATOR: {TOTAL:,} distinct corporate names "
          f"(individuals and public bodies are not DOS registrants)")
    sink.heartbeat("DOS", run_id, done=0, total=TOTAL, note="resolving")

    # name -> parcels, via the documents it appears on
    name_docs = collections.defaultdict(set)
    for p in parties:
        if p.get("name"):
            name_docs[dos.normalize(p["name"])].add(p["document_id"])
    name_bbls = {k: sorted({b for d in ds for b in doc_bbls.get(d, ())})
                 for k, ds in name_docs.items()}

    if fast:
        print("\n[1/2] ACTIVE entity index — FAST prefix path "
              "(⚠ measured to miss ~7%; not for a reported rate) ...")
        active, capped_a, unreachable = resolve_active(list(by_key))
        scanned = None
    else:
        print("\n[1/2] ACTIVE entity index — full scan, both sides normalised ...")
        active, capped_a, unreachable, scanned = resolve_active_stream(list(by_key))
    exact = {k: v[0] for k, v in active.items() if len(v) == 1}
    multi = {k: v for k, v in active.items() if len(v) > 1}
    print(f"      exact {len(exact):,} · multiple {len(multi):,} (never auto-selected)"
          + (f" · prefix-unreachable {len(unreachable)} · capped {capped_a}"
             if fast else f" · scanned {scanned:,} register rows"))

    # ⚠ Run the filings pull over EVERY corporate name, not only the ones the
    # active index missed. An entity being alive says nothing about how many
    # documents it has filed, and the ledger's job is to count what exists —
    # scoping it to the misses would catalogue the dead thoroughly and the
    # living not at all, then report the total as if it were the corpus.
    print(f"\n[2/2] FILINGS for all {len(by_key):,} corporate names ...")
    f = dos.filings_for(list(by_key))
    all_filings = f["filings"]
    missing = [k for k in by_key if k not in active]
    lives = {k: dos.lifecycle(v) for k, v in all_filings.items() if k in missing}
    print(f"      names with filings {len(all_filings):,} · filing rows "
          f"{sum(len(v) for v in all_filings.values()):,} · capped chunks "
          f"{f['capped_chunks']} · prefix-unreachable {len(f['unreachable'])}")
    print(f"      of the {len(missing):,} absent from the ACTIVE index, "
          f"{len(lives):,} have filings -> dissolved rather than nonexistent")
    if f["capped_chunks"]:
        print(f"      ⚠ {f['capped_chunks']} prefix(es) still truncate after subdividing: "
              f"{f.get('capped_prefixes')} — those names are UNDER-found, not absent")

    # ── the ledger. Documents that EXIST, all of them unread.
    n_docs = done = 0
    entity_rows = 0
    for k in by_key:
        done += 1
        raw = by_key[k][0]
        bbls = name_bbls.get(k, [])
        ent = exact.get(k)
        if ent:
            # the register row is not a document — it is the state's current
            # summary. Catalogued so the entity is addressable, and marked as
            # what it is.
            entity_rows += 1
        for r in all_filings.get(k, ()):
            if not r.get("film_num"):
                continue
            sink.ledger("DOS", r["film_num"], bbls=bbls,
                        doc_type=r.get("documenttype"),
                        happened=(r.get("eff_date") or r.get("date_filed") or "")[:10] or None,
                        recorded=(r.get("date_filed") or "")[:10] or None,
                        decode_status="unread", pages_read=0, run_id=run_id,
                        dos_id=r.get("corpid_num"), dos_name=r.get("corp_name"),
                        acris_name=raw, entity_type=r.get("entitytype"),
                        note="NY DOS filing; image not retrieved — apps.dos.ny.gov "
                             "publishes no crawl policy, access unresolved")
            n_docs += 1
        if done % 250 == 0:
            sink.heartbeat("DOS", run_id, done=done, total=TOTAL,
                           note=f"{n_docs} documents catalogued, 0 read")

    resolved = len(exact) + len(multi) + len(lives)
    sink.heartbeat("DOS", run_id, done=TOTAL, total=TOTAL, status="complete",
                   note=f"catalogued {n_docs} documents, read 0; "
                        f"resolved {resolved}/{TOTAL} names")

    print(f"\nNAMES RESOLVED {resolved:,}/{TOTAL:,} = {resolved/TOTAL:.1%}")
    print(f"  active exact        {len(exact):>5}  ({len(exact)/TOTAL:.1%})")
    print(f"  active multiple     {len(multi):>5}  (reported, never auto-selected)")
    print(f"  filings: dissolved  {sum(1 for v in lives.values() if v['ended']):>5}")
    print(f"  filings: formation  {sum(1 for v in lives.values() if v['formed']):>5}")
    print(f"  UNRESOLVED          {TOTAL-resolved:>5}  ({(TOTAL-resolved)/TOTAL:.1%})")
    print(f"\nDOCUMENTS  catalogued {n_docs:,}   READ 0   "
          f"(coverage 0.0% — access unresolved, not attempted)")
    print(f"FACTS      0 — an index row is not a decode "
          f"(RULE_DOCUMENTS_NOT_INDEXES)")
    print(f"\nrun {run_id}")
    return run_id


if __name__ == "__main__":
    lim = None
    for a in sys.argv[1:]:
        if a.startswith("--limit="):
            lim = int(a.split("=", 1)[1])
    run(lim, fast="--fast" in sys.argv)
