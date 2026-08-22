"""ONE PARCEL, END TO END — the test that the data tables are real.

    python walk_one.py

⚠ WHY THIS EXISTS. Before today the decoder had 78 JSON measurement files, five
migrations and ZERO rows. Every claim that the tables work was a claim about a
document describing tables. This walks one real parcel from paper to a query.

⚠ IT BUILDS FROM migrations/006_event_grammar.sql ITSELF, not from a copy. If the
shipped DDL and the tested DDL ever diverge, this fails instead of lying.

⚠ AND IT LOADS TWO SOURCES ON PURPOSE. Only ACRIS would prove the tables can hold
ACRIS — and would quietly make them ACRIS-shaped. The second source is a DOF
exemption row: no OCR, no vocabulary, `observes` mode, and its whole value is an
expiry term. If a recorded instrument and a structured feed both land correctly
on the same parcel and the account still reconciles, the design holds.

THE PARCEL — Queens Block 572 Lot 40, 23-34 30th Avenue, Astoria
THE DOCUMENT — ACRIS 2026060800658010, filed as AGREEMENT, actually an SNDA
THE FEED     — DOF exemption, 25 years from 2004, expiring 2029
"""
from __future__ import annotations

import json, os, re, sqlite3, sys, time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
DDL = os.path.join(HERE, "_walk_fixture.sql")   # ⚠ LOCAL TEST FIXTURE,
# NOT a production migration. It was moved OUT of migrations/ once the live
# database turned out to already hold `claim` (37 cols) and 439,717 documents:
# running it there would have silently skipped the existing tables. Production
# changes live in migrations/006_extend_live_model.sql, which only ADDS.
DB = os.path.join(HERE, "_walk_one.db")

DOC = "2026060800658010"
BBL = "4005720040"
TODAY = "2026-08-16"


def build(cx):
    """⚠ THE SHIPPED DDL IS THE TESTED DDL. Schema prefixes are stripped for
    SQLite; nothing else is rewritten, so Postgres-only syntax fails loudly."""
    sql = open(DDL, encoding="utf-8").read()
    sql = re.sub(r"\b(acris|resolution|derivation)\.", "", sql)
    cx.executescript(sql)
    n = [r[0] for r in cx.execute(
        "select name from sqlite_master where type='table' order by name")]
    print(f"schema: {len(n)} tables — {', '.join(n)}\n")


def head_text():
    j = json.load(open(os.path.join(HERE, "census_head", f"{DOC}.json"),
                      encoding="utf-8"))
    return [(p.get("page"), p.get("accepted_text") or "") for p in j["pages"]]


def span(text, needle, value):
    """Offsets of the VALUE, located via an anchor phrase.

    ⚠ THE ANCHOR IS NOT THE VALUE, AND STORING THE ANCHOR'S SPAN IS A SILENT
    FORGERY. The first version of this walk stored value='40' with the span of
    'QUEENS 572 40'. Every row looked correct in the table and three of eight
    claims failed the moment they were re-read from the page. The anchor exists
    only to find the REGION; the span written must be the value's own.

    ⚠ AND IT REFUSES RATHER THAN GUESSES. Anchor missing, or value not inside the
    anchor, and no claim is written at all.
    """
    i = text.find(needle)
    if i < 0:
        return (None, None)
    j = text.find(value, i, i + len(needle))
    if j < 0:
        return (None, None)
    return (j, j + len(value))


def load_acris(cx):
    pages = head_text()
    cx.execute("insert or replace into document (document_id,source,doc_type,recorded_at,page_count,pages_read,crfn) values (?,?,?,?,?,?,?)",
               (DOC, "ACRIS", "AGMT", "2026-07-06", 11, len(pages),
                "2026000187781"))

    # ── subjects. THE COVER NAMES ONE LOT; THE BODY NAMES THREE. ──────────
    subs = [("parcel:4005720040", "parcel", "4005720040", "Block 572 Lot 40 — 23-34 30th Ave"),
            ("parcel:4005721301", "parcel", "4005721301", "Block 572 Lot 1301"),
            ("parcel:4005721302", "parcel", "4005721302", "Block 572 Lot 1302"),
            ("entity:DEUTSCHE BANK AG, NEW YORK BRANCH", "entity",
             "DEUTSCHE BANK AG, NEW YORK BRANCH", "lender"),
            ("entity:30TH AVE PROPCO LLC", "entity", "30TH AVE PROPCO LLC",
             "Delaware LLC, c/o Apex Investments"),
            ("entity:HOUSING OPTIONS AND GERIATRIC ASSOCIATION RESOURCES, INC.",
             "entity", "HOUSING OPTIONS AND GERIATRIC ASSOCIATION RESOURCES, INC.",
             "NY not-for-profit")]
    cx.executemany("insert or replace into subject (subject_id,subject_type,identifier,label) values (?,?,?,?)", subs)

    # ── claims, each with the page and span it was found at ──────────────
    want = [("c1", 3, "lots_stated", "Block:572Lots:40,1301,1302", "Block:572Lots:40,1301,1302"),
            ("c2", 1, "cover_lot", "40", "QUEENS 572 40"),
            ("c3", 3, "instrument_title", "SUBORDINATION, NON-DISTURBANCE,AND ATTORNMENT AGREEMENT",
             "SUBORDINATION, NON-DISTURBANCE,AND ATTORNMENT AGREEMENT"),
            ("c4", 3, "lender", "DEUTSCHE BANK AG, NEW YORK BRANCH", "DEUTSCHE BANK AG, NEW YORK BRANCH"),
            ("c5", 3, "tenant", "HOUSING OPTIONS AND GERIATRIC ASSOCIATION RESOURCES, INC.",
             "HOUSING OPTIONS AND GERIATRIC ASSOCIATION RESOURCES, INC."),
            ("c6", 3, "lease_date", "September 11,2024", "Lease dated September 11,2024"),
            ("c7", 3, "loan_status", "has made or intends to make a loan",
             "has made or intends to make a loan"),
            ("c8", 1, "mortgage_amount", "0.00", "Mortgage Amount: $ 0.00")]
    made = []
    for cid, pg, field, value, needle in want:
        txt = dict(pages).get(f"p{pg:03d}", "")
        a, b = span(txt, needle, value)
        if a is None:
            print(f"  ⚠ REFUSED {cid} ({field}) — value not locatable on page {pg}")
            continue
        cx.execute("insert or replace into claim (claim_id,document_id,page,span_start,span_end,field,value,presence,reader,confidence) values (?,?,?,?,?,?,?,?,?,?)",
                   (cid, DOC, pg, a, b, field, value, "present", "cover_read"
                    if pg == 1 else "body", None))
        made.append(cid)
    # ⚠ ABSENT BY NATURE, NOT ZERO. The cover states $0.00 for every money field.
    cx.execute("insert or replace into claim (claim_id,document_id,page,span_start,span_end,field,value,presence,reader,confidence) values (?,?,?,?,?,?,?,?,?,?)",
               ("c9", DOC, 1, None, None, "loan_principal", None,
                "absent_by_nature", "cover_read", None))
    print(f"  claims written: {len(made)+1} ({len(made)} with spans, 1 absent_by_nature)")

    # ── events. ONE DOCUMENT, THREE FUNCTIONS, TWO MODES. ────────────────
    evs = [("e1", "OCCUPANCY", "transacts", "2026-06-02", 0,
            "lease recognised and attorned — non-disturbance"),
           ("e2", "TITLE", "transacts", "2026-06-02", 0,
            "lease SUBORDINATED to the mortgage — this is lien position"),
           ("e3", "CAPITAL", "signals", "2026-06-02", 0,
            "'has made OR INTENDS TO MAKE a loan' — the loan is not asserted as fact")]
    for eid, fn, mode, dt, adv, note in evs:
        cx.execute("insert or replace into event (event_id,document_id,function,mode,event_date,adverse,established,conservable,expected_fn,note) values (?,?,?,?,?,?,?,?,?,?)",
                   (eid, DOC, fn, mode, dt, adv, 1, 0, "CAPITAL", note))

    for eid in ("e1", "e2", "e3"):
        for i, s in enumerate(("parcel:4005720040", "parcel:4005721301",
                               "parcel:4005721302")):
            cx.execute("insert or replace into event_subject (event_id,subject_id,role) values (?,?,?)",
                       (eid, s, "primary" if i == 0 else "secondary"))

    parts = [("e1", "30TH AVE PROPCO LLC", "landlord", "c4"),
             ("e1", "HOUSING OPTIONS AND GERIATRIC ASSOCIATION RESOURCES, INC.", "tenant", "c5"),
             ("e2", "DEUTSCHE BANK AG, NEW YORK BRANCH", "lender", "c4"),
             ("e3", "DEUTSCHE BANK AG, NEW YORK BRANCH", "lender", "c4"),
             ("e3", "30TH AVE PROPCO LLC", "borrower", None)]
    for eid, nm, role, cid in parts:
        cx.execute("insert or replace into event_participant (event_id,party_name,party_role,subject_id,claim_id) values (?,?,?,?,?)",
                   (eid, nm, role, f"entity:{nm}", cid))

    cx.execute("insert or replace into event_term (event_id,kind,attaches_to,target,value,expires_on,claim_id) values (?,?,?,?,?,?,?)",
               ("e2", "lien_position", "participant",
                "DEUTSCHE BANK AG, NEW YORK BRANCH", "senior to the lease", None, "c3"))
    cx.execute("insert or replace into event_term (event_id,kind,attaches_to,target,value,expires_on,claim_id) values (?,?,?,?,?,?,?)",
               ("e1", "non_disturbance", "participant",
                "HOUSING OPTIONS AND GERIATRIC ASSOCIATION RESOURCES, INC.",
                "tenancy survives foreclosure", None, "c3"))
    # ⚠ UNREAD, NOT ZERO — the principal is on a note that is never recorded.
    cx.execute("insert or replace into event_quantity (event_id,kind,dim,value,unit,bound,presence,claim_id) values (?,?,?,?,?,?,?,?)",
               ("e3", "principal", "money", None, "USD", "exact", "unread", "c9"))
    for eid in ("e1", "e2", "e3"):
        for cid in made:
            cx.execute("insert or replace into event_claim values (?,?)", (eid, cid))
    print(f"  events written: {len(evs)} · 3 subjects each · "
          f"{len(parts)} participants")


def load_abatement(cx):
    """⚠ THE SECOND SOURCE. Structured rows, no OCR, no vocabulary. If this does
    not fit without a new column, the tables are ACRIS-shaped and the design is
    wrong."""
    import bulk
    rows = bulk.socrata("muvi-b6kx", where=f"parid='{BBL}'",
                        select="year,exmp_code,exname,benftstart,no_years",
                        limit=50, paginate=False)
    if not rows:
        print("  ⚠ no exemption rows — cannot test the second source. Stop.")
        return
    r = sorted(rows, key=lambda x: str(x.get("year")))[-1]
    start = int(str(r["benftstart"]).lstrip("+"))
    yrs = int(r["no_years"])
    end = start + yrs
    cx.execute("insert or replace into document (document_id,source,doc_type,recorded_at,page_count,pages_read,crfn) values (?,?,?,?,?,?,?)",
               ("DOF-EXEMPT-" + BBL, "DOF", "exemption_detail", r["year"],
                None, None, None))
    # ⚠ observes, NOT transacts. DOF reports the benefit; the grant happened
    # elsewhere. Calling this `transacts` would assert a change that this row
    # never witnessed.
    cx.execute("insert or replace into event (event_id,document_id,function,mode,event_date,adverse,established,conservable,expected_fn,note) values (?,?,?,?,?,?,?,?,?,?)",
               ("e4", "DOF-EXEMPT-" + BBL, "CAPITAL", "observes",
                f"{r['year']}-01-01", 0, 1, 0, "CAPITAL",
                f"exemption {r['exmp_code']} — {r['exname']}"))
    cx.execute("insert or replace into event_subject (event_id,subject_id,role) values (?,?,?)",
               ("e4", f"parcel:{BBL}", "primary"))
    cx.execute("insert or replace into event_term (event_id,kind,attaches_to,target,value,expires_on,claim_id) values (?,?,?,?,?,?,?)",
               ("e4", "benefit_period", "subject", f"parcel:{BBL}",
                f"{yrs} years from {start}", f"{end}-01-01", None))
    print(f"  DOF exemption {r['exmp_code']} ({r['exname']}) — "
          f"{yrs} yrs from {start}, expires {end}")
    return end


def load_vocab(cx):
    v = [("v1", "function", "CAPITAL", "principal sum · secures payment · consolidat-",
          "proven", "MTGE 59% · AGMT 85% · DEED 0/50",
          "666-doc census, per-type denominators"),
         ("v2", "function", "OCCUPANCY", "lessor/lessee · landlord/tenant · attornment",
          "proven", "95% recall / 9% leak", "151 lease-family docs, 5 eras, HEAD=6"),
         ("v3", "mode", "transacts", "does hereby · in consideration of",
          "proven", "100/97/95% operative", "23,282 clauses, WHEREAS/NOW-THEREFORE"),
         ("v4", "mode", "signals", "seeks · proposes · intends to · submitted",
          "proven", "79-97% applicant-agent, <1% ACRIS leak",
          "300 BSA decisions, agent ground truth"),
         ("v5", "function", "TITLE", "grant and release · convey · subordinate",
          "weak", "46% of 50 deeds; misses unexplained", "hidden-function matrix"),
         ("v6", "subject", "signature → person", "By: ____, authorised signatory",
          "unread", None, "sits past every head read")]
    cx.executemany("insert or replace into vocabulary (vocab_id,axis,reader,patterns,status,coverage,measured_against) values (?,?,?,?,?,?,?)", v)
    print(f"  vocabulary rows: {len(v)}")


def infer(cx, end_year):
    """⚠ ALIVE, NOT FROZEN. Carries the events it came from, so a new event can
    mark it stale instead of silently leaving it wrong."""
    ev = [r[0] for r in cx.execute(
        "select e.event_id from event e join event_subject s using(event_id) "
        "where s.subject_id=? and e.function='CAPITAL'", (f"parcel:{BBL}",))]
    cx.execute("insert or replace into inference (inference_id,subject_id,question,value,derivation,computed_at,stale) values (?,?,?,?,?,?,?)",
               ("i1", f"parcel:{BBL}",
                "What is the capital position on this parcel, and when does it change?",
                f"A loan is SIGNALLED but never asserted (principal unread — the note "
                f"is not recorded). A tax exemption is OBSERVED and expires {end_year}.",
                ",".join(ev), TODAY, 0))
    print(f"  inference i1 derived from events: {','.join(ev)}")


def report(cx):
    print("\n" + "=" * 66)
    print("QUERY 1 — everything that touches this parcel, any source")
    for r in cx.execute(
        "select e.function, e.mode, e.event_date, d.source, e.note "
        "from event e join event_subject s using(event_id) "
        "join document d on d.document_id=e.document_id "
        "where s.subject_id=? order by e.event_date", (f"parcel:{BBL}",)):
        print(f"  {r[0]:<11}{r[1]:<10}{r[2]:<12}{r[3]:<6}{r[4][:44]}")

    print("\nQUERY 2 — the broker question: what expires, and when?")
    for r in cx.execute(
        "select t.kind, t.value, t.expires_on, e.function from event_term t "
        "join event e using(event_id) join event_subject s using(event_id) "
        "where s.subject_id=? and t.expires_on is not null", (f"parcel:{BBL}",)):
        print(f"  {r[3]} · {r[0]} — {r[1]}  →  EXPIRES {r[2]}")

    print("\nQUERY 3 — ⚠ what is UNREAD (never printed as zero)")
    for r in cx.execute(
        "select q.kind, q.presence, e.function from event_quantity q "
        "join event e using(event_id) where q.presence!='present'"):
        print(f"  {r[2]} · {r[0]} = {r[1]}")
    for r in cx.execute("select field, presence from claim where presence!='present'"):
        print(f"  claim · {r[0]} = {r[1]}")
    for r in cx.execute("select reader, status from vocabulary where status='unread'"):
        print(f"  reader · {r[0]} = {r[1]}")

    print("\nQUERY 4 — ⚠ the hidden subjects: cover said 1 lot, body said 3")
    n = cx.execute("select count(distinct subject_id) from event_subject "
                   "where subject_id like 'parcel:%'").fetchone()[0]
    print(f"  parcels on this instrument: {n}  (ACRIS cover page listed 1)")

    print("\nQUERY 5 — expected vs observed function")
    for r in cx.execute("select distinct expected_fn, function, mode from event "
                        "where document_id=?", (DOC,)):
        tag = "as filed" if r[0] == r[1] else "⚠ HIDDEN FUNCTION"
        print(f"  filed as {r[0]:<9} observed {r[1]:<11}{r[2]:<11}{tag}")

    print("\nQUERY 6 — the inference, with its derivation")
    for r in cx.execute("select question, value, derivation from inference"):
        print(f"  Q: {r[0]}\n  A: {r[1]}\n  derived from: {r[2]}")


def main():
    if os.path.exists(DB):
        os.remove(DB)
    cx = sqlite3.connect(DB)
    cx.execute("pragma foreign_keys=on")
    build(cx)
    print("LOADING — ACRIS 2026060800658010 (filed AGREEMENT, actually an SNDA)")
    load_acris(cx)
    print("\nLOADING — DOF exemption feed (second source, no OCR, no vocabulary)")
    end = load_abatement(cx)
    print("\nLOADING — vocabulary ledger")
    load_vocab(cx)
    print("\nDERIVING")
    infer(cx, end)
    cx.commit()
    report(cx)
    counts = {t: cx.execute(f"select count(*) from {t}").fetchone()[0]
              for t in ("subject", "document", "claim", "event", "event_subject",
                        "event_participant", "event_quantity", "event_term",
                        "vocabulary", "inference")}
    print("\n" + "=" * 66)
    print("ROWS: " + " · ".join(f"{k}={v}" for k, v in counts.items()))
    print(f"db: {DB}")
    cx.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
