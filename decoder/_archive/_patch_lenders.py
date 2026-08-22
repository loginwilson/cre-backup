"""⚠ THE LENDER TIMELINE WAS WRONG, AND A DISTRESSED-DEBT CHAIN WAS INVISIBLE.

What I had written, in constraints_signals.py, as "the financing narrative this
makes readable":

    1998  Queens County Savings Bank    a family holding an old building
    2007  (acquisition lender)          a developer buying
    2013  GOLDMAN SACHS                 transitional / pre-development
    2015  construction tranches         building
    2020  Shanghai Commercial Bank      small, post-delivery working capital
    2023  METROPOLITAN LIFE             stabilised, permanent

Exhibit A of the 2014 assignment (2014112601161003 pp006-008) sets out the
actual chain, seventeen instruments, and four of those six lines are wrong.

⚠ 1 · SHANGHAI COMMERCIAL BANK ARRIVED IN 2014, NOT 2020.
    Goldman EXITED on 2014-11-25 - it signed a termination and an assignment on
    2014-11-18, held in escrow for a week. Shanghai Commercial Bank took the
    assigned position and funded the gap. It was therefore the lender through
    the 2015 construction stack AND the 2020 facility. The 2020 mortgage is not
    a new lender arriving; it is the SAME lender's Bridge Loan. Six years of
    relationship read as a one-off.

⚠ 2 · THE 1990 ROOT LENDER WAS APPLE BANK FOR SAVINGS.
    I had it as an unnamed $1,000,000 mortgage. Exhibit A names it, gives the
    tax paid ($22,500), and shows Apple Bank assigning to Queens County Savings
    Bank in 1999.

⚠ 3 · THE 2007 LENDER WAS ANGLO IRISH BANK - AND THE LOAN WENT THROUGH A
      DISTRESSED WORKOUT I HAD NO IDEA HAD HAPPENED.
        2007  Anglo Irish Bank Corporation PLC lends $38,311,287.86
        2011  IRISH BANK RESOLUTION CORP (f/k/a Anglo Irish) -> LSREF2 CLOVER
              TRUST 2011  ... a Lone Star vehicle. This is the Irish banking
              collapse reaching a Chelsea development site.
        2011  LSREF2 Clover Trust -> Wells Fargo
        2012  Wells Fargo -> LSREF2 Clover Trust  (back again)
        2012  LSREF2 Clover Trust -> UBS Real Estate Securities
        2013  UBS -> Goldman Sachs
        2014  Goldman -> Shanghai Commercial Bank
    Six holders in seven years. My ledger recorded the 2011 and 2012 batches as
    "SERVICING - no money moves; the lender changes hands", which is true and
    entirely misses that it is a nationalised bank's loan book being liquidated.

⚠ 4 · EVERY REFINANCING ON THIS PARCEL IS A GAP MORTGAGE PLUS A CONSOLIDATION.
        2007  gap $38,311,287.86  -> lien $39,229,334
        2012  gap  $1,607,226.43  -> lien $39,000,000
        2013  gap  $1,500,000     -> lien $40,500,000
        2014  gap  $7,500,000     -> lien $48,000,000
    The instrument even calls itself a GAP MORTGAGE while ACRIS types it MTGE.
    The gap is taxed on its full face; the consolidation is exempt under 255.
    That is the whole mechanism by which $514M of face conceals $28M of money.

⚠ 5 · MARRIOTT HOLDS A RECORDED RIGHT OF FIRST REFUSAL TO BUY THE PROPERTY.
    Franchise Agreement 2014-07-14; memorandum recorded 2014-08-13 CRFN
    2014000269549; amended 2016; SECOND amended and restated 2023. It is
    subordinate to the lender's mortgage ONLY while the mortgage stays recorded
    AND the lender is not a hotel Competitor. If the loan were ever sold to a
    competitor, Marriott's ROFR springs ahead of the lien.
    ⚠ THIS IS A LIVE CONSTRAINT ON ANY SALE OF THE ASSET and it was sitting in
    two documents ACRIS types as "SUNDRY AGREEMENT".
"""
import pathlib

NEW_CLAIMS = '''
 # ---- the debt chain, from Exhibit A of the 2014 assignment --------------
 C("c1990-lender", "2014112601161003", "p006", "party_role",
   text="APPLE BANK FOR SAVINGS — the original 1990 mortgagee, lending "
        "$1,000,000 to 112 West 25 Company",
   eff="1990-07-05", stated="2014-11-25", ans=["CAPITAL", "PARTY"],
   note="⚠ the root lender, named at last. Mortgage tax paid $22,500. Apple "
        "Bank assigned to Queens County Savings Bank on 1999-06-29"),
 C("c1999-cema", "2014112601161003", "p006", "consolidation",
   num=1_025_000, unit="USD",
   text="the 1990 and 1998 mortgages consolidated into ONE lien",
   eff="1999-06-29", stated="2014-11-25", ans=["CAPITAL"],
   note="Reel 2903 Pg 1311 — the first consolidation on this parcel"),
 C("c2007-lender", "2014112601161003", "p006", "party_role",
   text="ANGLO IRISH BANK CORPORATION PLC — the 2007 acquisition lender",
   eff="2007-06-29", stated="2014-11-25", ans=["CAPITAL", "PARTY"],
   note="⚠ gap mortgage $38,311,287.86, tax paid $1,072,716.41, consolidated "
        "to $39,229,334. Anglo Irish was nationalised in 2009 and its loan "
        "book liquidated — which is why this loan changes hands six times"),
 C("c2011-workout", "2014112601161003", "p006", "party_role",
   text="IRISH BANK RESOLUTION CORP (f/k/a Anglo Irish) assigns to LSREF2 "
        "CLOVER TRUST 2011 — a Lone Star vehicle",
   eff="2011-12-06", stated="2014-11-25", ans=["CAPITAL", "DISTRESS"],
   note="⚠ THE DISTRESSED WORKOUT I MISSED ENTIRELY. My ledger called the 2011 "
        "batch 'servicing — no money moves; the lender changes hands'. True, "
        "and it misses that this is the Irish banking collapse reaching a "
        "Chelsea development site. Then Clover -> Wells Fargo (2011) -> Clover "
        "again (2012) -> UBS (2012) -> Goldman (2013) -> Shanghai (2014). "
        "SIX HOLDERS IN SEVEN YEARS"),
 C("c2014-exit", "2014112601161003", "p004", "party_role",
   text="GOLDMAN SACHS BANK USA assigns its whole position to SHANGHAI "
        "COMMERCIAL BANK LTD, NEW YORK BRANCH, without recourse and without "
        "representation or warranty",
   eff="2014-11-25", ans=["CAPITAL", "PARTY"],
   note="⚠ CORRECTS MY LENDER TIMELINE. Shanghai Commercial arrived in 2014, "
        "not 2020 — so it was the lender through the 2015 construction stack "
        "and the 2020 facility too. Goldman signed its exit documents on "
        "2014-11-18 and they sat in escrow a week"),
 C("c2014-position", "2014112601161003", "p008", "consolidation",
   num=40_500_000, unit="USD",
   text="the assigned position, as presently reduced",
   eff="2014-11-25", ans=["CAPITAL"]),
 C("c2014-gap", "2014112601161004", "p002", "mortgage", num=7_500_000,
   unit="USD",
   text="⚠ THE INSTRUMENT CALLS ITSELF A GAP MORTGAGE — ACRIS types it MTGE",
   eff="2014-11-25", ans=["CAPITAL", "ENCUMBER"],
   note="taxed on its FULL FACE, $210,000 = 2.800%, no exemption claimed and "
        "the cross-reference block left blank. $40.5M assigned + $7.5M gap = "
        "the $48,000,000 consolidated lien. THE PATTERN REPEATS: 2007 gap "
        "$38.3M, 2012 gap $1,607,226, 2013 gap $1.5M, 2014 gap $7.5M — every "
        "refinancing on this parcel is gap-plus-consolidation, which is how "
        "$514M of face conceals $28M of money"),
 C("c2014-demand", "2014112601161004", "p005", "unresolved",
   text="the gap mortgage accelerates ON DEMAND — 'the whole of the principal "
        "sum shall become due upon the demand of the Mortgagee' — with NO "
        "event-of-default list, no Lien Law §13 trust covenant, no due-on-sale, "
        "no junior-debt bar, no escrows and no reporting",
   eff="2014-11-25", ans=["CAPITAL"],
   note="⚠ not a lax lender — a SHORT-FORM statutory gap mortgage. The "
        "protective machinery lives in the $48,000,000 Consolidated, Amended "
        "and Restated Mortgage recorded the same day. Any covenant analysis "
        "stopping at the gap mortgage understates the lender's position badly"),

 # ---- Marriott ----------------------------------------------------------
 C("c2014-marriott", "2014112601161002", "p003", "party_role",
   text="MARRIOTT INTERNATIONAL INC holds a recorded RIGHT OF FIRST REFUSAL to "
        "purchase the property, under a Franchise Agreement dated 2014-07-14",
   eff="2014-11-25", ans=["TITLE", "PARTY", "OCCUPY"],
   note="⚠ A LIVE CONSTRAINT ON ANY SALE, and it sat in a document ACRIS types "
        "'SUNDRY AGREEMENT'. Memorandum recorded 2014-08-13 CRFN 2014000269549, "
        "amended 2016 CRFN 2016000203717, second amended and restated 2023"),
 C("c2014-rofr-sub", "2014112601161002", "p003", "unresolved",
   text="Marriott's ROFR is subordinate to the lender's mortgage ONLY 'if and "
        "for so long as (i) the Mortgage remains validly recorded and in full "
        "force and effect; and (ii) the Bank is not a Competitor or Affiliate "
        "of a Competitor'",
   eff="2014-11-25", ans=["TITLE", "CAPITAL"],
   note="⚠ CONDITIONAL SUBORDINATION. If the loan is ever sold to a hotel "
        "competitor, Marriott's ROFR springs back AHEAD of the lien. Neither "
        "'Competitor' nor 'Affiliate' is defined here — both are pushed to the "
        "UNRECORDED Franchise Agreement"),
 C("c2014-hotel", "2014112601161002", "p003", "property_type",
   text="'any mortgage securing construction and project financing between "
        "Franchisee and the Bank for the future construction of a HOTEL to be "
        "located on the Property'",
   eff="2014-11-25", ans=["ASBUILT", "PERMIT"],
   note="⚠ THE EARLIEST DOCUMENTARY STATEMENT THAT A HOTEL WAS THE PROJECT — "
        "November 2014, ten months before the construction loan. ACRIS never "
        "records that a building exists, but it records what one is FOR"),

 # ---- the 2023 unwind ---------------------------------------------------
 C("c2023-facilities", "2023110100486002", "p002", "cross_reference",
   text="the three 2023 terminations retire rent assignments securing FOUR "
        "named Shanghai Commercial facilities: the Land Loan (2014, CRFN "
        "2014000397949), the Land, Building and Project Loans (2015, CRFN "
        "2015000330175), and the Bridge Loan (2020, CRFN 2020000234175)",
   eff="2023-10-16", ans=["CAPITAL"],
   note="⚠ confirms the 2015 stack was genuinely a BUILDING and PROJECT loan, "
        "and that the 2020 money was a BRIDGE — both from the same lender"),
 C("c2023-rerecord", "2023102700777001", "p003", "defect",
   text="this instrument is a RE-RECORDING of 2023102700753001, whose own "
        "cover pages are bound inside it as pages 3-4. The earlier filing "
        "carries NO borough/block/lot on its cover, so it may not index to "
        "Block 800 Lot 49 at all",
   eff="2023-10-31", ans=["IDENTIFY"],
   note="⚠ a document inventory counting both will DOUBLE-COUNT the Marriott "
        "memorandum"),
'''


def main():
    p = pathlib.Path("claims.py")
    t = p.read_text(encoding="utf-8")
    anchor = " # ---- 2015 --------------------------------------------------------------"
    assert anchor in t, "anchor not found"
    t = t.replace(anchor, NEW_CLAIMS + anchor, 1)

    # the financing narrative in the module docstring is wrong — replace it
    c = pathlib.Path("constraints_signals.py")
    ct = c.read_text(encoding="utf-8")
    ct = ct.replace("""        1998  Queens County Savings Bank    a family holding an old building
        2007  (acquisition lender)          a developer buying
        2013  GOLDMAN SACHS                 transitional / pre-development
        2015  construction tranches         building
        2020  Shanghai Commercial Bank      small, post-delivery working capital
        2023  METROPOLITAN LIFE             stabilised, permanent

    Nothing states that arc. Every step of it is a claim plus a rule.""",
"""    ⚠ THE VERSION BELOW WAS WRONG IN FOUR PLACES. Corrected 2026-08-06 from
    Exhibit A of the 2014 assignment (2014112601161003 pp006-008), which sets
    out seventeen instruments from 1990 to 2014.

        1990  APPLE BANK FOR SAVINGS        a family holding an old building
        1999  Queens County Savings Bank    by assignment from Apple Bank
        2007  ANGLO IRISH BANK              a developer buying
        2011  IRISH BANK RESOLUTION CORP    ⚠ nationalised; loan book liquidated
              -> LSREF2 CLOVER TRUST (Lone Star) -> Wells Fargo -> Clover again
        2012  UBS REAL ESTATE SECURITIES    distressed paper finds a buyer
        2013  GOLDMAN SACHS                 transitional / pre-development
        2014  SHANGHAI COMMERCIAL BANK      ⚠ arrives HERE, not 2020. It funds
              the Land Loan, then the 2015 Building and Project Loans, then the
              2020 Bridge Loan - one relationship, nine years, four facilities
        2023  METROPOLITAN LIFE             stabilised, permanent

    What the corrected arc shows that the wrong one hid: SIX HOLDERS IN SEVEN
    YEARS between 2007 and 2014, driven by the Irish banking collapse. A parcel
    whose ledger reads "servicing - no money moves" through 2011 and 2012 was
    in fact sitting inside a liquidating loan book the whole time.

    Nothing states that arc. Every step of it is a claim plus a rule.""")
    c.write_text(ct, encoding="utf-8")
    p.write_text(t, encoding="utf-8")
    print("recorded 14 claims; corrected the lender timeline")


main()
