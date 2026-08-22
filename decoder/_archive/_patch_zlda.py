import pathlib, re
NEW = '''
 C("c2010-zlda-price", "2010102601040006", "p001", "consideration",
   num=5_000_000, unit="USD",
   text="THE AIR-RIGHTS PRICE, ANSWERED. The 2010 ZLDA cover page is typed "
        "'DEVELOPMENT RIGHTS' and carries two PREPAID stamps: NYC RPTT "
        "$131,250.00 (Ref# 2010000376481) and NYS RETT $20,000.00 (Ref# "
        "3801156). $131,250 / 2.625% = $5,000,000 and $20,000 / 0.400% = "
        "$5,000,000",
   eff="2010-10-14", stated="2010-11-16", ev="derived",
   ans=["VALUE", "ENVELOPE"],
   note="⚠ TWO INDEPENDENT WITNESSES, so this is no longer the one-witness "
        "figure I flagged earlier. BUNDLED across lots 53, 55 and 56 - one "
        "stamp pair for the whole four-lot transaction, no per-lot breakout. "
        "$5,000,000 / 53,578 sf = $93.32 per buildable square foot"),
 C("c2010-price-hidden", "2010102601040006", "p096", "defect",
   text="⚠ THE PRICE IS KEPT OFF THE RECORD BY DESIGN. Exhibit H is a "
        "'Memorandum of DEVELOPMENT RIGHTS PURCHASE AND SALE AGREEMENT' "
        "dated December 2009 which states no price - 'reference should be "
        "made to the Contract' - and Exhibit I is a prepared 'Termination of "
        "Memorandum' that releases the notice at closing",
   eff="2010-10-14", ans=["VALUE", "IDENTIFY"],
   note="⚠ A MEMORANDUM GIVES NOTICE A CONTRACT EXISTS WHILE RECORDING NONE "
        "OF ITS TERMS, AND THE TERMINATION ERASES EVEN THAT. So the ONLY "
        "route to an air-rights price on this corpus is the tax stamp. "
        "Both exhibits are UNEXECUTED blank forms"),
 C("c2010-lav-easement", "2010102601040006", "p008", "easement",
   subject="1008000053",
   text="'120 Owner hereby grants to Developer a perpetual easement for "
        "LIGHT, AIR AND VIEW above the portion of the 120 Owner Land "
        "beginning at the rear lot line and extending ... a distance of "
        "TWENTY (20') FEET to the north of such rear lot line, beginning at "
        "a height of TWENTY-THREE (23') FEET above curb level' - with 120 "
        "Owner permitted to maintain its existing building in the easement "
        "area",
   eff="2010-10-14", vfrom=23.0, vdatum="curb level",
   hext="20 feet north of the lot 53 rear lot line", dur="perpetual",
   ans=["ENCUMBRANCE", "ENVELOPE"],
   note="⚠ ONE-DIRECTIONAL: lot 53 burdened, lot 49 benefited. NOT mutual. "
        "And the grant is from 120 Owner (lot 53) ONLY - no light/air/view "
        "grant from 124-26 W 25 Street LLC for lots 55 or 56 exists anywhere "
        "in the 110 pages"),
 C("c2010-form-drops-view", "2010102601040006", "p093", "defect",
   text="⚠ THE UNEXECUTED FORM DROPS 'VIEW' AND CHANGES THE METRICS. Exhibit "
        "F, 'Form of Light and Air Easement', says only 'The right to "
        "unrestricted light and air over Parcel A' with no view, and "
        "references Manhattan Datum before demolition versus 23 feet above "
        "curb after",
   eff="2010-10-14", ans=["ENCUMBRANCE", "IDENTIFY"],
   note="⚠ THE OPERATIVE BODY TEXT AND THE ANNEXED FORM DISAGREE ON WHAT WAS "
        "GRANTED. I dropped 'view' twice myself from this corpus; here the "
        "DOCUMENT does it. The form binds only 'if requested in writing by "
        "Developer' - contingent, not live"),
 C("c2019-chart", "2019071700601003", "p044", "envelope_balance",
   num=390_160, unit="sf",
   text="the 2019 Development Rights Chart, Exhibit D row 6 'Allocation of "
        "Development Rights After Transfer (sf)': Lot 49 Land 141,929 · Lot "
        "50 Land 127,035 · TOTAL across all nine combined-lot parcels 390,160",
   eff="2019-05-20", ans=["ENVELOPE"],
   note="⚠ THE NINE-LOT TOTAL IS 390,160 sf, NOT 268,964. My chain closed "
        "141,929 + 127,035 = 268,964 and that is the LOT 49 + LOT 50 share; "
        "the other seven lots retain 121,196 sf between them. A separate row "
        "5 gives 'Excess Development Rights' of 56,659 (lot 49) and 55,915 "
        "(lot 50) - excess-only, a different scope, not a conflict"),
 C("c2019-upzoning", "2019071700601003", "p015", "easement",
   text="upzoning and downzoning reallocate by formula: on an Upzoning 'Lot "
        "50 Owner shall be entitled to 45.48% of the Development Rights "
        "resulting from such Upzoning ... and Lot 49 Owner shall be entitled "
        "to 54.52%'. Trigger is 'a validly enacted amendment of the Zoning "
        "Resolution', or a casualty following a Downzoning",
   eff="2019-05-20", ans=["ENVELOPE"],
   note="⚠ A VARIABLE ENVELOPE. Any future rezoning of this block splits "
        "45.48/54.52 automatically. Section III otherwise bars cross-draw: "
        "each owner 'shall retain all rights in and to' its own rights"),
 C("c2019-nonarms", "2019071700601003", "p001", "defect",
   text="the 2019 subdivision paid ZERO transfer tax - NYC RPTT $0.00 and NYS "
        "RETT $0.00 - because grantor LAM GEN 25 LLC and grantee LG CHELSEA "
        "LLC are both 'c/o Lam Generation LLC' and Jeffrey Lam signed for "
        "BOTH as Authorized Signatory",
   eff="2019-05-20", ans=["VALUE", "TITLE"],
   note="⚠ COMMONLY-CONTROLLED ALLOCATION, NOT A SALE. So no price can be "
        "derived here - the stamp trick that works on every arm's-length "
        "transfer in this corpus returns nothing. ⚠ AND ONLY ONE OF THE TWO "
        "ACKNOWLEDGMENT BLOCKS ON p025 WAS NOTARISED"),
 C("c2010-pagecount-three", "2010102601040006", "p001", "defect",
   text="⚠ THREE DIFFERENT PAGE COUNTS, NONE AGREEING. The cover header says "
        "'PAGE 1 OF 116', a separate field says 'Document Page Count: 114', "
        "and 110 images exist on disk",
   eff="2010-11-16", ans=["IDENTIFY"],
   note="⚠ my integrity check assumes ONE authoritative count per cover. This "
        "document has two that disagree with each other AND with disk"),
'''
p = pathlib.Path("claims.py"); t = p.read_text(encoding="utf-8")
m = re.search(r"^ # ---- 2011.*$", t, re.M)
t = t.replace(m.group(0), NEW + m.group(0), 1)
p.write_text(t, encoding="utf-8")
print("recorded 8 ZLDA claims")
