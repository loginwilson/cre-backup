"""THE FUNCTIONS ACRIS ACTUALLY PERFORMS — derived from the document types present.

LOGIN, 2026-08-06: "that's one function — you need to determine the functions
that ACRIS touches on GIVEN THE DOCUMENTS."

    The instruction matters. A function list imported from what a broker wants to
    know produces boxes ACRIS cannot fill, and silence in those boxes reads as
    "nothing there". The list below is built the other way round: every document
    type present in lot 49's 96 was asked WHAT DOES THIS INSTRUMENT DO, and the
    functions are what fell out.

    Doing it this way immediately produced three functions I would not have
    written down from intuition:

      PRIORITY   16 SAGE + subordinations. Not "who is owed" but WHO IS SENIOR.
                 A second mortgage behind $120M is a different asset from a
                 first, and no amount of DEBT data distinguishes them.
      INCOME     9 AL&R + 8 TL&R + 3 AALR = 20 instruments, the third-largest
                 group on the parcel, doing nothing but pledging and releasing
                 the building's CASHFLOW. It is a distinct function from the
                 lien on the land.
      CONSENT    5 CERT. A title company certifying WHO THE PARTIES IN INTEREST
                 ARE and that each waived or joined. This is the function that
                 tells you whose signature a future deal needs.

⚠ AND THE FUNCTIONS ACRIS DOES **NOT** PERFORM, stated so silence is not read
  as absence:
      PERMIT · ASBUILT · COST · OCCUPANCY-IN-FACT · PHYSICAL CONDITION
  ACRIS never records that a building exists. The 40-storey hotel appears in
  this parcel's 96 documents only as collateral.
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
create table if not exists acris_functions (
  function     text primary key,
  question     text not null,     -- what a person is actually asking
  doc_types    text[] not null,   -- the instruments that perform it
  carries      text not null,     -- VALUES | TERMS | BOTH
  note         text
);

create table if not exists acris_function_events (
  bbl          text not null,
  function     text not null,
  effective    date not null,
  document_id  text not null,
  page         text,
  value_change text,              -- what NUMBER moved
  term_change  text,              -- what OBLIGATION changed
  running      text,              -- the state after
  evidence     text not null,
  primary key (bbl, function, effective, document_id)
);
create index if not exists afe_fn on acris_function_events(bbl, function, effective);
"""

# ---------------------------------------------------------------------------
# Derived by asking each doc type present on lot 49: WHAT DOES THIS DO?
# counts are lot 49's own 96 documents.
# ---------------------------------------------------------------------------
FUNCTIONS = [
 ("TITLE", "who owns it, and who owned it before",
  ["DEED"], 9, "BOTH",
  "9 deeds. Carries a VALUE (the price, via tax stamps) and TERMS (what it is "
  "taken subject to). A $0 deed may be a reorganisation, not a sale"),

 ("ENVELOPE", "what can be built here",
  ["DEVR", "EASE", "SMIS", "DECL", "ZONE"], 16, "BOTH",
  "The function with the richest terms. VALUES are sf and $/sf; TERMS are the "
  "alteration bars, plan-review rights and light/air/view easements that decide "
  "whether the sf can actually be used"),

 ("ENCUMBRANCE", "what is recorded against it, and who can lift it",
  ["EASE", "SMIS", "DECL", "AGMT"], 16, "TERMS",
  "Almost pure TERMS. The decisive field is CONSENT_OF — a burden the benefited "
  "owner can release is a negotiation; one naming the Department of Buildings "
  "is not"),

 ("DEBT", "what is owed, to whom, secured on what",
  ["MTGE", "AGMT", "ASST", "REL", "PREL"], 51, "BOTH",
  "The largest function by count. VALUES are principal and position; TERMS are "
  "the covenants and the §255-a affidavits. ⚠ face across a batch is not debt"),

 ("PRIORITY", "who is senior, and to whom",
  ["SAGE", "AGMT"], 16, "TERMS",
  "⚠ A FUNCTION I WOULD NOT HAVE LISTED FROM INTUITION. 16 subordination and "
  "supporting agreements do nothing but ORDER the claims. A second position "
  "behind $120M is a different asset from a first, and no amount of DEBT data "
  "says which you are looking at"),

 ("INCOME", "is the building's cashflow pledged, and to whom",
  ["AL&R", "TL&R", "AALR"], 20, "BOTH",
  "⚠ THE THIRD-LARGEST GROUP ON THE PARCEL and functionally invisible until "
  "you separate it. AL&R pledges leases and rents, TL&R releases them, AALR "
  "amends. The lien on the LAND and the pledge of the INCOME are different "
  "instruments answering different questions"),

 ("VALUE", "what did it trade for",
  ["DEED", "DEVR", "RPTT&RET"], 15, "VALUES",
  "Pure VALUES, and almost never in the index. Recovered from cover-page tax "
  "stamps: every DEVR on this parcel indexes at $0 and four of them had prices"),

 ("CONSENT", "whose signature does a future deal need",
  ["CERT"], 5, "TERMS",
  "⚠ ALSO NOT FROM INTUITION. A title company certifying the parties in "
  "interest under ZR 12-10 and whether each waived or joined. This is the "
  "function that names who must sign next time"),

 ("PARCEL", "what IS this lot, and what was it before",
  ["EASE", "DEED", "SMIS"], 12, "BOTH",
  "Lot geometry, metes and bounds, and lineage. The 2019 subdivision is stated "
  "in a RECITAL inside an instrument typed EASE"),

 ("TENANCY", "who is recorded as occupying it",
  ["MLEA"], 2, "BOTH",
  "Only 2 instruments, and ACRIS sees tenancy only when a lease is memorialised "
  "— which is rare. ⚠ NEAR-BLIND: absence here is not evidence of vacancy"),
]

NOT_ACRIS = [
 ("PERMIT", "DOB — what was filed to build"),
 ("ASBUILT", "DOB — what actually got built, and when it was delivered"),
 ("COST", "DOB/private — what building it cost"),
 ("OCCUPANCY", "HPD/DOF — who is in it now, at what rent"),
 ("CONDITION", "DOB/HPD — violations, physical state"),
]

# ---------------------------------------------------------------------------
# THE ENVELOPE FUNCTION, chronologically — value change AND term change per
# document. This is the shape every function narrative takes.
# ---------------------------------------------------------------------------
ENVELOPE_EVENTS = [
 ("2010-10-14", "2010102601040006", "p008,p038",
  "+53,578 sf from lots 53/55/56 · $5,000,000 bundle · balance 209,968",
  "FIRST TERMS ATTACH. Lot 53 alone grants a perpetual LIGHT, AIR AND VIEW "
  "easement (rear lot line, 20 ft north, above 23 ft). Owner barred from any "
  "alteration that encroaches, creates non-compliance, uses Developer rights, "
  "or amends a CO so as to reduce them. Developer gets plan review 10 business "
  "days before any DOB filing, a 30-day cure trigger, and a LICENSE TO ENTER "
  "lot 53 to cure.",
  "envelope 209,968 · lot 53 burdened, lots 55/56 rights-stripped only", "read"),

 ("2012-12-19", "2012122701550003", "p043",
  "+22,845 sf from lot 23 · $4,614,690 · $202.00/sf · balance 232,813",
  "TERMS NOT YET READ — 55 pp, body unexamined. The through-block linchpin's "
  "covenants are unknown.",
  "envelope 232,813", "value only"),

 ("2013-05-17", "2013052101674004", "p040,p042",
  "+10,726 sf from lot 22 · $1,450,000 · $135.19/sf · balance 243,539",
  "Light-and-air easement over the WHOLE of lot 22 above elev. 130 ft, in the "
  "DOB FORM — which names the DEPARTMENT OF BUILDINGS as a required consenting "
  "party, so the parties cannot release it between themselves. Breach risks "
  "revocation of a permit or CO. Explicitly may NOT satisfy light and air on an "
  "adjacent ZONING lot in lieu of the ZR.",
  "envelope 243,539 · lot 22 has a height plane no private deal can lift", "read"),

 ("2013-05-17", "2013052101674008", "p041",
  "+10,722 sf from lot 21 · $1,340,250 · $125.00/sf · balance 254,261",
  "Lot 21 CAPPED AT SEVEN DWELLING UNITS in perpetuity — a use restriction "
  "independent of the floor-area transfer. Wells Fargo as CMBS trustee "
  "consented. Operative clause NOT YET READ; cap taken from the chart page.",
  "envelope 254,261 · lot 21 capped", "partial"),

 ("2013-08-07", "2013080901116002", "p040",
  "+14,703 sf from lot 20 airspace · NO PRICE ON THIS PARCEL · balance 268,964",
  "Self-dealt: one entity in two capacities, so no arm's-length terms and zero "
  "tax. The airspace above elev. 130 ft is SEVERED from lot 20's ground. TERMS "
  "NOT READ.",
  "envelope 268,964 — the assemblage complete", "value only"),

 ("2013-08-07", "2013080901116001", "p003",
  "no sf moves",
  "THE ZONING LOT IS DECLARED over all EIGHT lots by a SINGLE DECLARANT. From "
  "here lot 49 cannot be zoned independently of the other seven. ⚠ INDEXED AS "
  "'SMIS'. Full terms NOT READ.",
  "envelope 268,964 · eight lots bound as one", "partial"),

 ("2015-03-31", "2015041300292001", "p001",
  "no sf moves — ZERO TAX",
  "The 2010 grantor CONFIRMS the earlier transfer to the new owner. A DEVR that "
  "is not a purchase. Terms unread.",
  "envelope 268,964 unchanged", "value only"),

 ("2019-05-20", "2019071700601003", "p044",
  "-127,035 sf to lot 50 (71,120 land-generated + 55,915 acquired) · balance 141,929",
  "The envelope is SPLIT between two Lam entities, Jeffrey Lam signing both "
  "sides. Terms of the split NOT READ — whether the light/air easements follow "
  "lot 49, lot 50, or both is UNKNOWN and matters: lot 22's height plane was "
  "bought for a tower that now sits on only one of the two lots.",
  "lot 49: 85,270 own + 56,659 acquired = 141,929", "partial"),
]


def main():
    fns = [dict(function=f, question=q, doc_types=t, documents=n, carries=c,
                note=note) for f, q, t, n, c, note in FUNCTIONS]

    print("THE FUNCTIONS ACRIS PERFORMS — derived from lot 49's own doc types\n")
    print(f"  {'function':<13}{'docs':>5}  {'carries':<8} question")
    print("  " + "-" * 74)
    for f in sorted(fns, key=lambda x: -x["documents"]):
        print(f"  {f['function']:<13}{f['documents']:>5}  {f['carries']:<8} "
              f"{f['question']}")
        print(f"  {'':<13}{'':>5}  {'':<8} {', '.join(f['doc_types'])}")

    print("\n  ⚠ THREE OF THESE WOULD NOT HAVE BEEN ON AN INTUITED LIST:")
    print("     PRIORITY  16 docs — who is SENIOR, not who is owed")
    print("     INCOME    20 docs — the cashflow pledge, separate from the lien")
    print("     CONSENT    5 docs — whose signature the NEXT deal needs")

    print("\n  WHAT ACRIS DOES NOT DO (so silence is not read as absence):")
    for f, who in NOT_ACRIS:
        print(f"     {f:<11} {who}")

    print("\n" + "=" * 78)
    print("FUNCTION NARRATIVE · ENVELOPE · lot 49 — value AND term, chronological")
    print("=" * 78)
    for eff, doc, page, val, term, run, ev in ENVELOPE_EVENTS:
        flag = {"read": "✓", "partial": "~", "value only": "✗"}[ev]
        print(f"\n{eff}  {doc} {page}   [{flag} terms {ev}]")
        print(f"   VALUE  {val}")
        print(f"   TERM   {term}")
        print(f"   STATE  {run}")

    rd = sum(1 for e in ENVELOPE_EVENTS if e[6] == "read")
    print(f"\n  ⚠ TERMS FULLY READ ON {rd} OF {len(ENVELOPE_EVENTS)} ENVELOPE "
          f"EVENTS.")
    print("    The VALUE column is complete and closes to the square foot.")
    print("    The TERM column is a third done — and the terms are what decide")
    print("    whether the square feet can be used.")

    ev_rows = [dict(bbl=L49, function="ENVELOPE", effective=e[0],
                    document_id=e[1], page=e[2], value_change=e[3],
                    term_change=e[4], running=e[5], evidence=e[6])
               for e in ENVELOPE_EVENTS]
    for name, data in (("acris_functions", fns),
                       ("acris_function_events", ev_rows)):
        fp = HERE / f"{name}.csv"
        with open(fp, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(data[0].keys()))
            w.writeheader()
            for r in data:
                r = dict(r)
                if isinstance(r.get("doc_types"), list):
                    r["doc_types"] = "|".join(r["doc_types"])
                w.writerow(r)
        print(f"\n  wrote {fp.name} ({len(data)} rows)")


if __name__ == "__main__":
    if "--ddl" in sys.argv:
        print(DDL); sys.exit(0)
    main()
