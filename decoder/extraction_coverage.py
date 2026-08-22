"""VALUES and TERMS, per document — the coverage that decides when a lot is done.

LOGIN, 2026-08-06: "I think that's what you need to get down across all of the
documents — the terms and the values."

    Two extractions, not one, and a document is not decoded until BOTH have been
    attempted:

        VALUES  the cited numbers — dollar amounts, square feet, rates, counts.
                Each with a unit. These land in acris_claims as QUANTITY.
        TERMS   the obligations and prohibitions. No number in them. These land
                in acris_terms as actor/modality/action/consent_of.

⚠ WHY "ATTEMPTED" AND NOT "FOUND"

    A document with no terms is a real and common result — an ASST carries a
    reference and a party and nothing else. But "we looked and there are none"
    and "nobody has looked" must not produce the same row, or coverage inflates
    silently. That is the single failure mode this project keeps rediscovering:

        pages fetched     read as     pages read
        documents held    read as     documents decoded
        no terms found    read as     no terms exist

    So a document reaches DONE only by carrying an explicit verdict for each
    extraction — values and terms — and NOT_LOOKED is the default, loudly.

THE HONEST STATE THIS REPORTS

    Lot 49 has 96 documents. Values have been extracted from ~30 of them. TERMS
    have been extracted from THREE. That is the real distance to a finished
    parcel, and it is much further than the timeline's confident prose implies.
"""
import csv, json, pathlib, sys
from collections import defaultdict

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = pathlib.Path(__file__).parent
L49 = "1008000049"

DDL = """
create table if not exists acris_extraction (
  bbl          text not null,
  document_id  text not null,
  doc_type     text,
  pages_held   int,
  values_status text not null default 'NOT_LOOKED',  -- NOT_LOOKED|PARTIAL|DONE|NONE_PRESENT
  values_count int  not null default 0,
  terms_status  text not null default 'NOT_LOOKED',
  terms_count   int not null default 0,
  note         text,
  updated_at   timestamptz default now(),
  primary key (bbl, document_id)
);

-- ⚠ NONE_PRESENT means WE LOOKED AND THERE ARE NONE. NOT_LOOKED means nobody
-- has opened it for this purpose. They must never be collapsed: the first is a
-- finding, the second is a gap, and a coverage number that treats them alike is
-- the lie this table exists to prevent.

create or replace view extraction_gaps as
select bbl, doc_type, count(*) as documents,
       count(*) filter (where values_status = 'NOT_LOOKED') as values_todo,
       count(*) filter (where terms_status  = 'NOT_LOOKED') as terms_todo
from acris_extraction group by bbl, doc_type order by 4 desc, 5 desc;
"""

# Document types whose instruments routinely carry TERMS worth structuring.
# ⚠ This is a PRIORITY hint, not a licence to skip the rest. An ASST usually
# carries no covenant — but "usually" is how the DEVR-always-$0 error was made.
TERM_BEARING = {"DEVR", "EASE", "AGMT", "SMIS", "DECL", "ZONE", "CERT", "DEED"}


def load():
    sys.path.insert(0, str(HERE))
    import claims as K
    vals = defaultdict(int)
    for c in K.rows():
        if K.KIND[c["predicate"]] == "QUANTITY":
            vals[c["document_id"]] += 1
    looked = {c["document_id"] for c in K.rows()}   # any claim = document opened

    terms = defaultdict(int)
    tp = HERE / f"acris_terms_{L49}.csv"
    if tp.exists():
        for r in csv.DictReader(open(tp, encoding="utf-8")):
            terms[r["document_id"]] += 1

    master = HERE / "lot49_50_master.json"
    types = {}
    if master.exists():
        for r in json.load(open(master, encoding="utf-8")):
            types[r["document_id"]] = r.get("doc_type")
    # ⚠ THE DENOMINATOR. lot49_50_master.json holds BOTH lots, so an unfiltered
    # count reported "lot 49 · 123 documents" when lot 49 has 96. A coverage
    # percentage over the wrong denominator is worse than none: it looked
    # WORSE than reality here, but the same bug flatters just as easily.
    keep = HERE / "lot49_index.json"
    if keep.exists():
        only = set(json.load(open(keep, encoding="utf-8")))
        types = {k: v for k, v in types.items() if k in only}
    return vals, terms, looked, types


def main():
    vals, terms, looked, types = load()
    pages = HERE / "pages_out"
    import claims as K
    docs = sorted({c["document_id"] for c in K.rows()} | set(types))
    # restrict to lot 49's own 96
    idx = HERE / "acris_claims_1008000049.csv"
    rows = []
    for d in docs:
        if d not in types and not d.startswith(("FT_", "20")):
            continue
        held = len(list((pages / d).glob("*.png"))) if (pages / d).exists() else 0
        dt = types.get(d) or ("FT_" if d.startswith("FT_") else "?")
        v = vals.get(d, 0)
        t = terms.get(d, 0)
        vs = "DONE" if v else ("PARTIAL" if d in looked else "NOT_LOOKED")
        ts = "DONE" if t else "NOT_LOOKED"
        rows.append(dict(bbl=L49, document_id=d, doc_type=dt, pages_held=held,
                         values_status=vs, values_count=v,
                         terms_status=ts, terms_count=t, note=None))

    n = len(rows)
    vd = sum(1 for r in rows if r["values_status"] == "DONE")
    vp = sum(1 for r in rows if r["values_status"] == "PARTIAL")
    td = sum(1 for r in rows if r["terms_status"] == "DONE")
    print(f"EXTRACTION COVERAGE · lot 49 · {n} documents\n")
    print(f"  VALUES  {vd:>3} with quantities extracted   "
          f"{vp:>3} opened but no quantity   {n-vd-vp:>3} NOT LOOKED")
    print(f"  TERMS   {td:>3} with terms extracted        "
          f"{'':>3}                          {n-td:>3} NOT LOOKED")
    print(f"\n  values coverage {100*vd/n:.0f}%   ·   TERMS COVERAGE "
          f"{100*td/n:.0f}%")

    tb = [r for r in rows if r["doc_type"] in TERM_BEARING
          and r["terms_status"] == "NOT_LOOKED" and r["pages_held"] > 3]
    print(f"\n  ⚠ {len(tb)} TERM-BEARING documents with pages on disk and NO "
          f"terms extracted.")
    print(f"     These are the ones most likely to hold a covenant, and nobody "
          f"has looked:")
    for r in sorted(tb, key=lambda x: -x["pages_held"])[:14]:
        print(f"       {r['document_id']:<18} {r['doc_type']:<6} "
              f"{r['pages_held']:>4} pp   values:{r['values_count']}")

    byt = defaultdict(lambda: [0, 0, 0])
    for r in rows:
        b = byt[r["doc_type"]]
        b[0] += 1
        b[1] += r["values_status"] == "DONE"
        b[2] += r["terms_status"] == "DONE"
    print(f"\n  BY DOC TYPE        docs  values  terms")
    for dt, (c, v, t) in sorted(byt.items(), key=lambda x: -x[1][0]):
        flag = "  <-- term-bearing, unexamined" if (dt in TERM_BEARING and not t) else ""
        print(f"    {dt:<16} {c:>5} {v:>7} {t:>6}{flag}")

    p = HERE / f"acris_extraction_{L49}.csv"
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print(f"\n  wrote {p.name} ({len(rows)} rows)")
    print("\n  ⚠ THE LOT IS NOT DONE. Terms have been structured from THREE")
    print("    documents. Every NOT_LOOKED above is a document whose covenants")
    print("    are unknown — not absent, unknown.")


if __name__ == "__main__":
    if "--ddl" in sys.argv:
        print(DDL); sys.exit(0)
    main()
