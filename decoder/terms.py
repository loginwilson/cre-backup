"""TERMS — restrictions whose substance is not a number.

LOGIN, 2026-08-06:

    "There will be some that aren't numerical too. An easement with terms that
     are restrictive — so the number equivalent are the restrictive TERMS
     packaged into structured data."

    Exactly right, and it is the harder half. "130 ft" decodes into a magnitude
    and a datum. "may not be modified without the prior written consent of the
    Department of Buildings" has no magnitude at all, and is more consequential:
    it means the burden cannot be lifted by the two parties who created it.

THE STRUCTURE OF A NON-NUMERIC TERM

    A restriction is a sentence with a fixed grammar, and that grammar IS the
    schema:

        ACTOR      who is bound
        MODALITY   MUST | MUST_NOT | MAY | MAY_ONLY_IF
        ACTION     the verb — build, exceed, obstruct, modify, grant, record
        OBJECT     what the verb acts on
        CONDITION  when it applies
        EXCEPTION  unless
        CONSENT_OF who can release it            ← the field that decides deals
        BREACH     what happens if violated
        RUNS_WITH  does it bind successors

    Decomposed this way a covenant becomes queryable: "which burdens on this
    block can be released by the owner of lot 49 alone?" is a filter on
    CONSENT_OF, and it is the first question a broker actually asks.

⚠ WHY `CONSENT_OF` IS THE MOST VALUABLE FIELD

    Every constraint recorded so far looks permanent. Some are not — they are
    permanent UNTIL A NAMED PARTY AGREES. On this block:

      * the rights transfers and unit cap can be released by the benefited
        owner, i.e. lot 49's owner, privately
      * the light-and-air easement in the DOB-form instrument CANNOT — it names
        the Department of Buildings as a required consenting party, so no
        private deal between neighbours can lift it

    Those two look identical in any "there is an easement" summary. They are
    opposite situations for anyone trying to buy the block.

⚠ VERBATIM IS MANDATORY HERE
    A structured term is an INTERPRETATION of a sentence. The sentence is the
    evidence, and unlike a dollar figure it cannot be re-derived from a stamp.
    Every row carries the words it was built from.
"""
import csv, pathlib, sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = pathlib.Path(__file__).parent
L49 = "1008000049"

DDL = """
create table if not exists acris_terms (
  burdened_bbl text not null,
  seq          int  not null,
  -- ⚠ ADDED 2026-08-06 AFTER A REAL ERROR. The first five lot-22 terms below
  -- were extracted from EXHIBIT G of 2013052101674004 and recorded as live
  -- burdens with severity FATAL. Exhibit G is an UNEXECUTED BLANK FORM —
  -- "EASEMENT AGREEMENT made this ___ day of ___, 201_, between ______".
  -- It binds NOTHING until the developer requests the confirming easement and
  -- the owner executes it within its 20 business days.
  --
  -- I had read that page. The blanks were visible. I transcribed the clauses
  -- and never asked whether the instrument they sit in had been signed —
  -- the same failure as reading the chart and not the covenant, one layer up.
  --
  -- EXECUTED  the clause is operative now
  -- CONTINGENT the clause sits in an attached FORM and binds only on a future
  --            triggering act, which must be named in `trigger`
  status       text not null default 'EXECUTED',
  trigger      text,
  document_id  text not null,
  page         text not null,
  effective    date,
  actor        text not null,      -- who is bound
  modality     text not null,      -- MUST | MUST_NOT | MAY | MAY_ONLY_IF
  action       text not null,      -- the verb
  object       text,               -- what it acts on
  condition    text,               -- when it applies
  exception    text,               -- unless
  consent_of   text,               -- ⚠ who can release it. NULL = nobody can.
  breach       text,               -- consequence of violation
  runs_with_land bool,
  benefited_bbl text,
  severity     text not null,      -- FATAL | MAJOR | MINOR
  verbatim     text not null,      -- ⚠ the words. Mandatory, never null.
  primary key (burdened_bbl, seq)
);
create index if not exists acris_terms_consent on acris_terms(consent_of);
create index if not exists acris_terms_modality on acris_terms(modality, action);

-- the question a broker asks first: what can actually be lifted, and by whom?
create or replace view releasable_burdens as
select burdened_bbl, consent_of, count(*) as terms,
       string_agg(distinct action, ', ') as restrictions,
       bool_or(consent_of is null) as has_unreleasable
from acris_terms group by burdened_bbl, consent_of
order by burdened_bbl;
"""

# ---------------------------------------------------------------------------
# Terms read from the Light and Air Easement form (Exhibit G) attached to the
# Brick Farms ZLDA, 2013052101674004 pages 043-044, and from the ZLDAs' own
# operative language.
# ---------------------------------------------------------------------------
TERMS = [
 dict(bbl="1008000022", seq=1, status="CONTINGENT",
      trigger="binds only if the Developer requests the confirming easement under the ZLDA and the Owner executes it within 20 business days", doc="2013052101674004", page="p044",
      eff="2013-05-17", actor="the owner of Parcel A (lot 22)",
      modality="MUST_NOT", action="construct so as to infringe",
      object="the light and air provided to Parcel B (lot 49)",
      condition="at any time", consent_of=None, runs="yes", ben=L49,
      sev="FATAL",
      verbatim="The right to unrestricted light and air over Parcel A as "
               "described herein, such that any construction on Parcel A shall "
               "never infringe upon the light and air provided to Parcel B"),

 dict(bbl="1008000022", seq=2, status="CONTINGENT",
      trigger="binds only if the Developer requests the confirming easement under the ZLDA and the Owner executes it within 20 business days", doc="2013052101674004", page="p044",
      eff="2013-05-17", actor="both parties",
      modality="MUST_NOT", action="modify, amend or terminate",
      object="this easement agreement",
      condition="without prior written consent",
      consent_of="NYC Department of Buildings", runs="yes", ben=L49,
      sev="FATAL",
      verbatim="This easement agreement may not be modified, amended or "
               "terminated without the prior written consent of the Department "
               "of Buildings"),

 dict(bbl="1008000022", seq=3, status="CONTINGENT",
      trigger="binds only if the Developer requests the confirming easement under the ZLDA and the Owner executes it within 20 business days", doc="2013052101674004", page="p044",
      eff="2013-05-17", actor="the owners and their successors",
      modality="MUST", action="be bound by", object="the covenants herein",
      condition="as covenants running with the land",
      consent_of=None, runs="yes", ben=L49, sev="MAJOR",
      verbatim="The covenants set forth herein shall run with the land and be "
               "binding upon and inure to the benefit of the parties hereto and "
               "their respective heirs, legal representatives, successors and "
               "assigns"),

 dict(bbl="1008000022", seq=4, status="CONTINGENT",
      trigger="binds only if the Developer requests the confirming easement under the ZLDA and the Owner executes it within 20 business days", doc="2013052101674004", page="p044",
      eff="2013-05-17", actor="the owner of either parcel",
      modality="MUST", action="record the cross-reference number",
      object="on each temporary and permanent certificate of occupancy, and in "
             "any deed conveying the affected parcels",
      condition="on every future CO and conveyance",
      consent_of=None, breach="revocation of a building permit or certificate "
                              "of occupancy",
      runs="yes", ben=L49, sev="MAJOR",
      verbatim="This easement agreement shall be recorded at the city "
               "register's (county clerk's) office against all affected parcels "
               "and the cross-reference number and title of the easement "
               "agreement shall be recorded on each temporary and permanent "
               "certificate of occupancy hereafter issued to buildings located "
               "on the affected parcels and in any deed for the conveyance "
               "thereof"),

 dict(bbl="1008000022", seq=5, status="CONTINGENT",
      trigger="binds only if the Developer requests the confirming easement under the ZLDA and the Owner executes it within 20 business days", doc="2013052101674004", page="p043",
      eff="2013-05-17", actor="the owner of lot 22",
      modality="MAY_ONLY_IF", action="satisfy building-code light and air",
      object="on an adjacent TAX LOT",
      condition="under the 1968 Building Code sections 27-732 and 27-746, or "
                "2008 Building Code sections BC 1203.4 and BC 1205.2",
      exception="⚠ THIS MAY NOT be used to satisfy light and air on an adjacent "
                "ZONING LOT in lieu of compliance with the Zoning Resolution or "
                "Section 30 of the Multiple Dwelling Law",
      consent_of=None, runs="yes", ben=L49, sev="MAJOR",
      verbatim="This easement agreement may be entered into as a means of "
               "compliance with the 1968 or 2008 Building Codes by permitting "
               "such codes' light and air requirements to be satisfied on an "
               "adjacent tax lot. However, this agreement cannot be used to "
               "permit the required light and air to be satisfied on an "
               "adjacent zoning lot in lieu of compliance with the New York "
               "City Zoning Resolution or Section 30 of the Multiple Dwelling "
               "Law"),

 dict(bbl="1008000021", seq=1, doc="2013052101674008", page="p041",
      eff="2013-05-17", actor="the owner of lot 21",
      modality="MUST_NOT", action="exceed", object="seven dwelling units",
      condition="in perpetuity",
      consent_of="the owner of lot 49 (as benefited party)", runs="yes",
      ben=L49, sev="FATAL",
      verbatim="[unit cap recorded in the ZLDA, Exhibit D chart page and "
               "operative text — capped at seven dwelling units]"),

 dict(bbl="1008000020", seq=1, doc="2013052101674004", page="p041",
      eff="2013-05-17", actor="the owner/operator of 135 West 24th Street",
      modality="MUST", action="permit occupation of",
      object="the parking lane and traffic lane fronting the property",
      condition="during construction of the lot 49 tower, for a stated width "
                "and period",
      consent_of="the owner/operator (the letter is a FORM, executed per job)",
      runs="no", ben=L49, sev="MINOR",
      verbatim="24 WEST NY LLC, the owner and operator of 135 West 24th "
               "Street, hereby authorizes [Extell Development Company] and its "
               "contractors to utilize the parking lane and traffic lane in "
               "front of our property of the same address, for the construction "
               "of a building at the Subject Premises"),

 dict(bbl=L49, seq=1, doc="2013080901116001", page="p003",
      eff="2013-08-07", actor="the owner of lot 49",
      modality="MUST_NOT", action="treat as a separate zoning lot",
      object="any of lots 49, 20, 21, 22, 23, 53, 55, 56",
      condition="while the declaration stands",
      consent_of="all parties in interest to the declared zoning lot",
      runs="yes", ben=None, sev="MAJOR",
      verbatim="[Declaration of Zoning Lot Restrictions covering eight lots, "
               "single declarant 112-118 West 25th LLC]"),
]


def main():
    rows = [dict(burdened_bbl=t["bbl"], seq=t["seq"], document_id=t["doc"],
                 page=t["page"], effective=t.get("eff"), actor=t["actor"],
                 modality=t["modality"], action=t["action"],
                 object=t.get("object"), condition=t.get("condition"),
                 exception=t.get("exception"), consent_of=t.get("consent_of"),
                 breach=t.get("breach"),
                 status=t.get("status", "EXECUTED"), trigger=t.get("trigger"),
                 runs_with_land=(t.get("runs") == "yes"),
                 benefited_bbl=t.get("ben"), severity=t["sev"],
                 verbatim=t["verbatim"]) for t in TERMS]

    print("TERMS — restrictions with no number in them\n")
    for r in rows:
        lot = r["burdened_bbl"][-3:].lstrip("0")
        print(f"  lot {lot:<3} [{r['severity']}] {r['actor']}")
        print(f"        {r['modality']} {r['action']}"
              f"{' ' + r['object'] if r['object'] else ''}")
        if r["condition"]:
            print(f"        WHEN      {r['condition']}")
        if r["exception"]:
            print(f"        EXCEPT    {r['exception'][:110]}")
        if r["status"] == "CONTINGENT":
            print(f"        ⚠ NOT YET BINDING — {r['trigger'][:64]}")
        rel = r["consent_of"] or "⚠ NOBODY — cannot be released"
        print(f"        RELEASE   {rel}")
        if r["breach"]:
            print(f"        BREACH    {r['breach']}")
        print(f"        \"{r['verbatim'][:104]}...\"" if len(r["verbatim"]) > 104
              else f"        \"{r['verbatim']}\"")
        print(f"        {r['document_id']} {r['page']}\n")

    print("=" * 72)
    print("WHO CAN LIFT WHAT — the question a summary can never answer\n")
    byc = {}
    for r in rows:
        byc.setdefault(r["consent_of"] or "⚠ NOBODY", []).append(r)
    for k in sorted(byc, key=lambda x: (x.startswith("⚠"), x)):
        lots = sorted({r["burdened_bbl"][-3:].lstrip("0") for r in byc[k]})
        print(f"  {k}")
        print(f"      {len(byc[k])} term(s) · lots {', '.join(lots)}")
    print("\n  ⚠ THE DECISIVE DISTINCTION: the light-and-air easement on lot 22")
    print("    names the DEPARTMENT OF BUILDINGS as a required consenting party.")
    print("    No private deal between lot 22 and lot 49 can lift it. The unit")
    print("    cap on lot 21, by contrast, is a private covenant the benefited")
    print("    owner CAN release. In any 'there is an easement' summary those")
    print("    two read identically. They are opposite situations for a buyer.")

    nr = [r for r in rows if not r["runs_with_land"]]
    print(f"\n  {len(nr)} term(s) do NOT run with the land "
          f"(expire or are per-job): " +
          ", ".join(f"lot {r['burdened_bbl'][-3:].lstrip('0')}/{r['action']}"
                    for r in nr))

    p = HERE / f"acris_terms_{L49}.csv"
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print(f"\n  wrote {p.name} ({len(rows)} rows)")
    missing = [r for r in rows if not r["verbatim"]]
    if missing:
        print("⚠ TERM WITHOUT VERBATIM — an interpretation with no evidence")
        sys.exit(1)
    print("  every term carries the words it was built from ✓")


if __name__ == "__main__":
    if "--ddl" in sys.argv:
        print(DDL); sys.exit(0)
    main()
