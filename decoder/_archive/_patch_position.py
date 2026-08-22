"""⚠ FOUR CORRECTIONS TO THE DEBT POSITION AND THE LENDER LIST.

1 · THE 2018 "AGMT" IS A SPLITTER. IT DOES THE OPPOSITE OF A CONSOLIDATION.
    2018113000347001 is a MORTGAGE AND NOTE SPLITTER AGREEMENT. It severs the
    $48,000,000 lien into two:
        $25,500,000  on Parcel 1 = LOT 49
        $22,500,000  on Parcel 2 = LOT 50, assumed by LG Chelsea LLC
    My ledger carried "2018-11-19 CONSOLIDATION $48,000,000" as lot 49's
    position. ⚠ THAT OVERSTATES LOT 49'S DEBT BY $22,500,000 for five years,
    from 2018 until the 2023 recapitalisation.

    ⚠ AND ITS COVER PAGE INDEXES IT TO LOT 50. The instrument that halves lot
    49's debt names lot 50 in its PROPERTY DATA block - the block whose own
    text says it "will control for indexing purposes in the event of any
    conflict with the rest of the document". Lot 49 appears only inside
    recorded Schedules B and C.

2 · THE 2025 LENDER IS DEUTSCHE BANK, NOT METLIFE.
    2025101700864005 assigns leases and rents to DEUTSCHE BANK AG, NEW YORK
    BRANCH as administrative agent for a lender group. Schedule 1 item 11 is a
    $3,000,000 GAP MORTGAGE to Deutsche Bank, tax $84,000. MetLife's $120M
    position is the thing being consolidated INTO, not the new money.
    I had recorded the 2025 event with no lender at all.

3 · THE 2015 CONSTRUCTION LOAN IS CONFIRMED, NAMED, AND GENUINELY ADDITIVE.
        item 7  BUILDING LOAN MORTGAGE  $31,930,000  tax $894,040  "Affects
                Tax Lots 49 and 50"
        item 8  PROJECT LOAN MORTGAGE   $33,780,000  tax $945,840
    Both taxed in full at 2.800%, neither exempt. So they ARE additive and the
    $65,710,000 figure holds - and the instruments call themselves Building
    Loan and Project Loan, so "the construction loan" was never an inference.

4 · METLIFE ARRIVED BY ASSIGNMENT, NOT BY REFINANCING.
    Shanghai Commercial assigned all four of its facilities to MetLife
    Commercial Mortgage Originator LLC on 2023-10-16 (CRFNs 2023000287577,
    578, 579, 580 - one per facility). MetLife then added a $25,490,000 gap
    and consolidated to $120,000,000. The pattern is identical to 2007, 2012,
    2013 and 2014: acquire the paper, add a gap, consolidate.
"""
import pathlib

NEW = '''
 # ---- the 2018 splitter — the correction that halves lot 49's debt -------
 C("c2018-splitter", "2018113000347001", "p003", "unresolved",
   text="⚠ THIS IS A MORTGAGE AND NOTE SPLITTER AGREEMENT, NOT A "
        "CONSOLIDATION. It severs the $48,000,000 lien into $25,500,000 on "
        "LOT 49 and $22,500,000 on LOT 50, the latter assumed by LG Chelsea "
        "LLC",
   eff="2018-11-19", stated="2018-12-03", ans=["CAPITAL", "PARCEL"],
   note="⚠ I carried $48,000,000 as lot 49's position from 2018 to 2023. It "
        "was $25,500,000. Overstated by $22,500,000 for five years"),
 C("c2018-l49position", "2018113000347001", "p011", "consolidation",
   num=25_500_000, unit="USD",
   text="lot 49's actual mortgage position after the 2018 split",
   eff="2018-11-19", ans=["CAPITAL"],
   note="Schedule B: 'shall remain a lien in the principal amount of "
        "$25,500,000.00 ... (Block: 800, Lot: 49)'"),
 C("c2018-l50position", "2018113000347001", "p011", "consolidation",
   num=22_500_000, unit="USD", subject="1008000050",
   text="the severed lien that moved to lot 50, assumed by LG Chelsea LLC",
   eff="2018-11-19", ans=["CAPITAL"]),
 C("c2018-indexdefect", "2018113000347001", "p001", "defect",
   text="⚠ the cover page PROPERTY DATA names MANHATTAN 800 LOT 50 — the "
        "instrument that halves lot 49's debt is indexed to lot 50. Lot 49 "
        "appears only inside recorded Schedules B and C",
   eff="2018-12-03", ans=["IDENTIFY", "CAPITAL"],
   note="the cover page's own text says it 'will control for indexing purposes "
        "in the event of any conflict with the rest of the document'. A "
        "BBL-keyed pull can miss the operative event for a parcel's debt"),

 # ---- the 2015 construction stack, confirmed and named -------------------
 C("c2015-building", "2015091001439003", "p001", "mortgage", num=31_930_000,
   unit="USD",
   text="BUILDING LOAN MORTGAGE — the instrument's own name — affecting Tax "
        "Lots 49 AND 50",
   eff="2015-09-02", ev="index", ans=["CAPITAL", "PERMIT"],
   note="mortgage tax paid $894,040 = 2.800% on the full face, no exemption. "
        "Confirms this is genuinely new money, not a restatement"),
 C("c2015-project", "2015091001439004", "p001", "mortgage", num=33_780_000,
   unit="USD", text="PROJECT LOAN MORTGAGE — the instrument's own name",
   eff="2015-09-02", ev="index", ans=["CAPITAL", "PERMIT"],
   note="mortgage tax paid $945,840 = 2.800% on the full face. Building Loan + "
        "Project Loan both taxed in full, so the $65,710,000 total is real. "
        "⚠ 'the construction loan' was never an inference — the instruments "
        "say Building and Project Loan outright"),

 # ---- MetLife arrives by assignment --------------------------------------
 C("c2023-assignments", "2025101700864005", "p026", "cross_reference",
   text="SHANGHAI COMMERCIAL BANK assigned ALL FOUR facilities to METLIFE "
        "COMMERCIAL MORTGAGE ORIGINATOR LLC on 2023-10-16 — CRFN 2023000287577 "
        "(the consolidated mortgages), 578 (building loan), 579 (project "
        "loan), 580 (the 2020 mortgage)",
   eff="2023-10-16", ans=["CAPITAL", "PARTY"],
   note="⚠ MetLife did not refinance out an incumbent — it BOUGHT the paper, "
        "then added a $25,490,000 gap and consolidated to $120,000,000. The "
        "same acquire-gap-consolidate pattern as 2007, 2012, 2013 and 2014"),

 # ---- the 2025 lender -----------------------------------------------------
 C("c2025-lender", "2025101700864005", "p004", "party_role",
   text="DEUTSCHE BANK AG, NEW YORK BRANCH, as administrative agent for a "
        "lender group — the 2025 lender",
   eff="2025-10-16", ans=["CAPITAL", "PARTY"],
   note="⚠ I recorded the 2025 event with no lender named. Deutsche Bank took "
        "a $3,000,000 gap mortgage (tax $84,000) and the whole position "
        "consolidated to $123,000,000. Borrower is now LAM GEN 25 LLC AND "
        "CHELSEA 25 HOTEL LLC jointly"),
 C("c2025-absolute", "2025101700864005", "p006", "unresolved",
   text="the 2025 assignment of rents is a PRESENT, ABSOLUTE assignment — "
        "'not an assignment for additional security only' — with a revocable "
        "licence back that terminates automatically on an Event of Default, "
        "without notice",
   eff="2025-10-16", ans=["INCOME", "CAPITAL"],
   note="⚠ structurally different from the 2020 Shanghai assignment, which was "
        "expressly collateral. An absolute assignment puts the rents outside "
        "the borrower's estate from day one"),
 C("c2025-unrecorded", "2025101700864005", "p010", "unresolved",
   text="'In case of any conflict between the terms of this Assignment and the "
        "terms of the Loan Agreement, the terms of the Loan Agreement shall "
        "prevail' — and the Loan Agreement, Cash Management Agreement and "
        "Clearing Account Agreement are all UNRECORDED",
   eff="2025-10-16", ans=["CAPITAL"],
   note="⚠ the same off-register structure as MetLife. Every borrower-side "
        "leasing covenant — amendment, termination, prepaid rent, major-lease "
        "consent — is absent from the recorded text and pulled in wholesale by "
        "reference. The public record cannot tell you what the borrower may do "
        "with its leases"),
 C("c2019-blanket-zlda", "2025101700864005", "p015", "cross_reference",
   text="CRFN 2019000231248, recorded 2019-07-22 — a zoning lot development "
        "and easement agreement covering ALL NINE lots: 20, 21, 22, 23, 49, "
        "50, 53, 55 and 56",
   eff="2019-07-22", stated="2025-10-16", ans=["ENVELOPE"],
   note="the easement schedule every later lender recites"),
'''


def main():
    p = pathlib.Path("claims.py")
    t = p.read_text(encoding="utf-8")
    anchor = " # ---- 2020 --------------------------------------------------------------"
    assert anchor in t, "anchor not found"
    t = t.replace(anchor, NEW + anchor, 1)
    p.write_text(t, encoding="utf-8")
    print("recorded 12 claims; corrected the 2018 position, the 2025 lender, "
          "and confirmed the 2015 stack")


main()
