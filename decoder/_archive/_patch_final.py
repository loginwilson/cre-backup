"""THE AIR-RIGHTS PRICES, PER LOT — and the 130-foot plane fully resolved."""
import pathlib
import re

NEW = '''
 C("c2013-lot22-price", "2013052101674004", "p001", "consideration",
   num=1_450_000, unit="USD", subject="1008000022",
   text="LOT 22 AIR RIGHTS: cover stamps 'NYC Real Property Transfer Tax: "
        "$38,062.50' and 'NYS Real Estate Transfer Tax: $5,800.00'. $5,800 / "
        "0.400% = $1,450,000, and $38,062.50 / 2.625% agrees within "
        "rounding. Against 10,726 sf that is about $135 PER BUILDABLE FOOT",
   eff="2013-05-17", ev="derived", ans=["VALUE", "ENVELOPE"],
   note="⚠ SELLER IS BRICK FARMS COOPERATIVE LTD, a residential co-op. "
        "Bilateral - one co-op, one developer, one stamp pair, NOT bundled"),
 C("c2013-lot21-price", "2013052101674008", "p001", "consideration",
   num=1_340_500, unit="USD", subject="1008000021",
   text="LOT 21 AIR RIGHTS: 'NYC Real Property Transfer Tax: $35,181.56' and "
        "'NYS Real Estate Transfer Tax: $5,362.00'. $5,362 / 0.400% = "
        "$1,340,500. Against 10,722 sf that is about $125 PER BUILDABLE FOOT",
   eff="2013-05-17", ev="derived", ans=["VALUE", "ENVELOPE"],
   note="seller 133 West 24th Street Corporation. ⚠ TWO COMPARABLE SALES TEN "
        "DAYS APART AT $135 AND $125 A FOOT - the first real air-rights comps "
        "on this block. The 2010 bundle across lots 53/55/56 was $93/sf"),
 C("c2013-lot20-internal", "2013080901116002", "p001", "defect",
   subject="1008000020",
   text="⚠ THE LOT 20 TRANSFER IS NOT A SALE. The cover names "
        "'GRANTOR/SELLER: 112-118 WEST 25TH LLC' and 'GRANTEE/BUYER: 112-118 "
        "WEST 25TH LLC' - the same entity - and Marc Kwestel signs BOTH "
        "signature blocks as Vice President. Both transfer taxes read $0.00",
   eff="2013-08-07", ans=["VALUE", "TITLE"],
   note="⚠ NO PRICE EXISTS TO FIND HERE. The real acquisition from an "
        "unrelated party - 351 E 61 REALTY LLC, the physical building owner - "
        "happened in the 2008 Lot 20 ZLDA at CRFN 2008000078652. A $0/$0 "
        "stamp pair is a POSITIVE FINDING: it identifies an internal "
        "reassignment rather than an unpriced sale"),
 C("c2013-plane-both-sides", "2013080901116002", "p036", "easement",
   subject="1008000020", vto=130.0,
   vdatum="Topographical Bureau, Borough of Manhattan",
   text="THE 130-FOOT PLANE, BOTH SIDES QUOTED OUT OF ONE DOCUMENT. p029, "
        "Airspace Parcel: 'ALL that portion ... LYING ABOVE a lower limiting "
        "plane drawn at an elevation of 130 feet'. p036, Lower Parcel: 'ALL "
        "that portion ... LYING BELOW an upper limiting plane drawn at an "
        "elevation of 130 feet'",
   eff="2013-08-07", ans=["ENVELOPE", "ENCUMBRANCE"],
   note="⚠ THERE WAS NEVER A CONTRADICTION. One plane, two parcels, each "
        "described from its own side - 'upper limiting' bounds the parcel "
        "below it, 'lower limiting' bounds the parcel above it. ⚠ AND LOT 49 "
        "GOT BOTH THINGS: the 14,703 sf of Excess Development Rights come "
        "from the LOWER parcel (Exhibit D p040) while the light/air/view "
        "easement is granted ABOVE the plane. You buy the floor area the "
        "lower owner cannot use AND the guarantee that nobody builds over it. "
        "My 'owns air above an elevation' was right about the easement and "
        "wrong about the rights"),
 C("c2012-lot23-plane", "2012122701550003", "p008", "easement",
   subject="1008000023", vfrom=155.24,
   vdatum="Datum Level = 2.75 ft above US Coast and Geodetic Survey, mean "
          "sea level Sandy Hook NJ",
   dur="perpetual",
   text="'Owner hereby grants to Developer a perpetual easement for LIGHT, "
        "AIR AND VIEW above the Lower Limiting Plane' - lot 23's plane sits "
        "at 155.24 FEET above Datum Level",
   eff="2012-12-19", ans=["ENCUMBRANCE", "ENVELOPE"],
   note="⚠ EVERY LOT HAS ITS OWN PLANE: lot 23 at 155.24 ft, lot 21 at 150 "
        "ft, lot 22 at 130 ft, lot 20 at 130 ft. Not one blanket height "
        "across the block. And lot 23's plane is VARIABLE - it can be RAISED "
        "if the owner acquires bonus rights and undertakes an Alteration"),
 C("c2013-datum-conflict", "2013080901116002", "p004", "defect",
   text="⚠ THE SAME INSTRUMENT GIVES THE DATUM TWO VALUES. Body section I.E "
        "at p004: 'which is 2.75 FEET above the United States Coast and "
        "Geodetic Survey Datum'. Exhibits at p029 and p036: 'which is 2.78 "
        "FEET above National Geodetic Survey vertical datum 1929'",
   eff="2013-08-07", ans=["PARCEL", "IDENTIFY"],
   note="⚠ 0.03 FEET AND A DIFFERENT DATUM STANDARD, INSIDE ONE RECORDED "
        "DOCUMENT. Immaterial at 130 feet, but it proves the body and the "
        "exhibits were drafted from different sources - and the exhibits are "
        "what a surveyor would actually use"),
 C("c-pagecount-rule", "2013052101674004", "p001", "unresolved",
   text="THE COVER-PAGE COUNTER RULE, measured on four documents: 'Document "
        "Page Count' is ALWAYS EXACTLY 2 LESS than 'PAGE 1 OF N', and PAGE 1 "
        "OF N always matches the files on disk. 55/53, 45/43, 41/39, 40/38",
   eff="2013-05-21", ev="derived", ans=["IDENTIFY"],
   note="⚠ THE 2-PAGE GAP IS THE COVER SHEET AND ITS CONTINUATION. Document "
        "Page Count describes the INSTRUMENT; PAGE 1 OF N describes the FILED "
        "SUBMISSION. ⚠ CONFLATING THEM IS EXACTLY WHAT PRODUCED FIVE FALSE "
        "TRUNCATION POSITIVES out of my own integrity check. Always store "
        "PAGE 1 OF N"),
 C("c-forms-drop-view", "2012122701550003", "p045", "defect",
   text="⚠ THE ANNEXED FORMS DROP 'VIEW', TWICE MORE. Exhibit G in both the "
        "lot 23 and the lot 22 agreements is an UNEXECUTED blank 'Form of "
        "Light and Air Easement' whose body says only 'unrestricted LIGHT AND "
        "AIR' - while the operative grant in each agreement's own section II "
        "says 'light, air AND VIEW'",
   eff="2012-12-19", ans=["ENCUMBRANCE", "IDENTIFY"],
   note="⚠ FOUR INSTANCES ACROSS FOUR AGREEMENTS - 2010, 2012, and both 2013 "
        "sets. THE OPERATIVE TEXT GRANTS VIEW AND EVERY ANNEXED FORM OMITS "
        "IT. A systematic drafting divergence, not a typo, and it decides "
        "whether a neighbour may build something that blocks the view without "
        "blocking light"),
 C("c2013-psa-unrecorded", "2013052101674004", "p012", "unresolved",
   text="the price MECHANISM is stated while the price is not: Developer may "
        "buy future upzoning rights 'AT THE SAME PRICE PER SQUARE FOOT PAID "
        "FOR THE ACQUISITION OF THE EXCESS DEVELOPMENT RIGHTS', confirming a "
        "per-square-foot price exists in an unrecorded Development Rights "
        "Purchase and Sale Agreement",
   eff="2013-05-17", ans=["VALUE"],
   note="⚠ THE DOCUMENT ADMITS THE NUMBER EXISTS AND DECLINES TO STATE IT. "
        "Every ZLDA references that PSA and none attaches it; the "
        "'Confirmation of Termination' exhibit that would name it is an "
        "unexecuted blank. THE TAX STAMP REMAINS THE ONLY WITNESS"),
 C("c2013-construction-easement", "2013080901116002", "p016", "easement",
   subject="1008000020",
   text="section XIII grants Developer a Construction Easement over the Lower "
        "Parcel 'for the purpose of providing construction protection ... and "
        "of facilitating the safe and timely construction of and necessary "
        "support for the Developer Building' - foundation support, "
        "underpinning, fencing, protective sheds and bridges over the "
        "neighbour's roof and facade, plus maintenance of all of it. Entry "
        "needs 5 days notice except in an Emergency Situation",
   eff="2013-08-07", ans=["ENCUMBRANCE", "PERMIT"],
   note="⚠ THE ONLY CONSTRUCTION EASEMENT IN THE SET - absent from the lot "
        "21, 22 and 23 agreements, which the agent read end to end. Lot 20 is "
        "the neighbour lot 49 actually had to build against"),
 C("c2023-owner-agreement", "2023102700753001", "p006", "cross_reference",
   text="THE MISSING CONVEYANCE IS NAMED. Recital F of the Second Amended and "
        "Restated Memorandum of Right of First Refusal: the parties execute "
        "it 'to document FRANCHISEE'S TRANSFER OF ITS FEE OWNERSHIP OF THE "
        "REAL PROPERTY TO OWNER', and Recital D names the instrument - 'an "
        "OWNER AGREEMENT dated October 16, 2023'",
   eff="2023-10-16", ans=["TITLE"],
   note="⚠ THIS CLOSES ONE OF THE TWO GENUINELY MISSING ACRIS FACTS. Lam Gen "
        "25 LLC transferred the fee to Chelsea 25 Hotel LLC by an Owner "
        "Agreement, not a deed - which is why no deed was ever found. ⚠ AND "
        "IT WAS HIDING IN A DOCUMENT TYPED 'SUNDRY MISCELLANEOUS'. The Owner "
        "Agreement itself is still not in the corpus"),
 C("c2025-maxsecured", "2025101700864004", "p025", "consolidation",
   num=85_000_000, unit="USD",
   text="section 15.02(c), all-caps in the original: 'THE MAXIMUM AMOUNT OF "
        "PRINCIPAL INDEBTEDNESS SECURED BY THIS MORTGAGE ... IS EIGHTY-FIVE "
        "MILLION AND NO/100 DOLLARS ($85,000,000.00)' - against a "
        "$123,000,000 consolidated lien at section 15.02(g)",
   eff="2025-10-16", ans=["DEBT"],
   note="⚠ THE $85,000,000 I HAD BEEN RECONSTRUCTING IS STATED OUTRIGHT, "
        "under RPL 254. Three figures coexist and all are true of different "
        "things: $123,000,000 consolidated lien, $120,000,000 unpaid balance "
        "of the existing mortgages, $85,000,000 MAXIMUM ACTUALLY SECURED. "
        "Words and numerals agree at every occurrence"),
 C("c2020-collateral", "2020081400407001", "p021", "easement",
   text="the 2020 assignment of rents is COLLATERAL, not absolute: 'The "
        "Mortgagee hereby WAIVES THE RIGHT TO ENTER upon the Property for the "
        "purpose of collecting the Rents, and the Mortgagor SHALL HAVE A "
        "LICENSE to collect and receive the Rents, until an Event of Default "
        "shall have occurred'",
   eff="2020-08-05", ans=["INCOME", "ENCUMBRANCE"],
   note="⚠ CONFIRMS THE STRUCTURAL DIFFERENCE I FLAGGED. The 2025 Deutsche "
        "Bank assignment says 'present, absolute assignment ... and not an "
        "assignment for additional security only'; this one waives entry "
        "until default. Absolute puts the rents outside the borrower's estate "
        "from day one; collateral does not"),
 C("c2018-splitter-severs", "2018113000347001", "p011", "consolidation",
   num=25_500_000, unit="USD",
   text="Schedule B: 'The lien of the mortgages as consolidated shall remain "
        "a lien in the principal amount of $25,500,000.00 made by Lam Gen 25 "
        "LLC ... (Block: 800, Lot: 49) ... as Parcel 1' and a 'Split "
        "Replacement Mortgage ... in the principal amount of $22,500,000.00 "
        "made by LG Chelsea LLC ... (Block: 800, Lot: 50) ... as Parcel 2'",
   eff="2018-11-19", ans=["DEBT", "PARCEL"],
   note="⚠ A FULL SEVERANCE, NOT AN ALLOCATION. Lot 49 keeps the ORIGINAL "
        "mortgage with Lam Gen 25 still as mortgagor; lot 50 gets a BRAND NEW "
        "instrument with LG Chelsea substituted. No cross-liability either "
        "way. Independently corroborated by the 2025 schedule item 6C: "
        "'Splits Mortgages into two liens: $22,500,000.00, not affecting "
        "premises and $25,500,000.00, affecting premises'"),
 C("c2020-hotel-manager", "2020081400407001", "p019", "party_role",
   text="'income statements for the operation of the RENAISSANCE NEW YORK "
        "CHELSEA HOTEL (the Hotel) ... managed by REAL HOSPITALITY GROUP, LLC "
        "(the Hotel Manager) ... Management Agreement dated MARCH 1, 2018'",
   eff="2018-03-01", stated="2020-08-14",
   parties=["REAL HOSPITALITY GROUP, LLC (hotel manager)",
            "MARRIOTT INTERNATIONAL, INC. (franchisor)"],
   ans=["TENANCY", "PERMIT"],
   note="⚠ THE OPERATOR, NAMED AT LAST, AND IT IS NOT MARRIOTT. Marriott is "
        "the FRANCHISOR under a July 14, 2014 agreement; Real Hospitality "
        "Group actually runs the building under a separate March 2018 "
        "management agreement. Two different relationships that a franchise "
        "flag on a building hides"),
 C("c2026-foreign-docs", "2026052800492001", "p001", "defect",
   text="⚠ TWO DOCUMENTS IN THIS PARCEL'S FOLDER ARE NOT THIS PARCEL. "
        "2026052800492001 is a POWER OF ATTORNEY covering 'BROOKLYN 7027 54 "
        "Entire Lot 3735 OCEANIC AVENUE' between EKATERINA and OLGA "
        "YUMAKAEVA. 2026062301264001 is a POWER OF ATTORNEY covering "
        "'BROOKLYN 2350 1016 Entire Lot 214 85 NORTH 3 STREET' between ELI "
        "and SABRINA WACHT",
   eff="2026-06-01", ans=["IDENTIFY"],
   note="⚠ FOREIGN DOCUMENTS IN THE PARCEL FOLDER, AND I REPORTED THEM TO THE "
        "USER AS 'NEW 2026 ACTIVITY ON THIS PARCEL'. Neither mentions Block "
        "800, lot 49, or any party in this chain. ⚠ NO CHECK I BUILT ASKS "
        "'IS THIS DOCUMENT EVEN THIS PARCEL'S?' - every one asks whether a "
        "document is complete and read. The cover page prints its own "
        "borough, block and lot; one page gates the entire pipeline. Both "
        "folders are also short, 3 of 9 and 1 of 10"),
 C("c2023-folder-mismatch", "2023102700777001", "p003", "defect",
   text="⚠ A FOLDER HOLDING A DIFFERENT DOCUMENT'S BODY. Pages p001-p002 are "
        "the cover for 2023102700777001 ('SUNDRY AGREEMENT', Document Page "
        "Count 11). Pages p003-p013 are the complete cover AND body of "
        "2023102700753001 ('SUNDRY MISCELLANEOUS', its own PAGE 1 OF 11) - a "
        "different document ID. The actual body of 777001 was never fetched",
   eff="2023-10-27", ans=["IDENTIFY"],
   note="⚠ AND A PAGE-COUNT CHECK PASSES: 13 files against 13 claimed. The "
        "document is still wrong. Counting pages cannot detect a substituted "
        "body - only reading the document ID printed on each cover can"),
'''


def main():
    p = pathlib.Path("claims.py")
    t = p.read_text(encoding="utf-8")
    m = (re.search(r"^ # ---- 2014.*$", t, re.M)
         or re.search(r"^ # ---- 201[4-9].*$", t, re.M))
    assert m, "no anchor"
    t = t.replace(m.group(0), NEW + m.group(0), 1)
    p.write_text(t, encoding="utf-8")
    print("recorded 17 claims")


main()
