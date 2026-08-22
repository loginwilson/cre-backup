"""⚠ THE 2010 ZLDA CLAIMS THAT WERE REPORTED BUT NEVER RECORDED.

_patch_zlda.py died on a bash heredoc error ("unexpected EOF"). I saw the
error, switched to the Write tool for the NEXT patch, and never went back to
re-run the one that failed. So the 2010 ZLDA findings — the $5,000,000 price
derived from two tax stamps, the light/air/view granting words, the
deliberately unrecorded purchase agreement — went into a message to the user
and into no table.

⚠ IT SURFACED ONLY BECAUSE A SUPERSESSION EDGE POINTED AT A CLAIM THAT DID
NOT EXIST. Nothing else would have caught it: the narrative was right, the
scope file said ANSWERED, and the claim count kept rising from other patches.
A ledger that cannot detect its own missing rows is not a ledger — the edge
integrity check is what makes it one.
"""
import pathlib
import re

NEW = '''
 C("c2010-zlda-price", "2010102601040006", "p001", "consideration",
   num=5_000_000, unit="USD",
   text="THE 2010 AIR-RIGHTS PRICE. The ZLDA cover page is typed "
        "'DEVELOPMENT RIGHTS' and carries two PREPAID stamps: NYC RPTT "
        "$131,250.00 (Ref# 2010000376481) and NYS RETT $20,000.00 (Ref# "
        "3801156). $131,250 / 2.625% = $5,000,000 and $20,000 / 0.400% = "
        "$5,000,000",
   eff="2010-10-14", stated="2010-11-16", ev="derived",
   ans=["VALUE", "ENVELOPE"],
   note="TWO INDEPENDENT WITNESSES. BUNDLED across lots 53, 55 and 56 - one "
        "stamp pair for the whole four-lot transaction, no per-lot breakout. "
        "$5,000,000 / 53,578 sf = $93.32 per buildable square foot, against "
        "$135 and $125 a foot for lots 22 and 21 three years later"),
 C("c2010-price-hidden", "2010102601040006", "p096", "defect",
   text="⚠ THE PRICE IS KEPT OFF THE RECORD BY DESIGN. Exhibit H is a "
        "'Memorandum of DEVELOPMENT RIGHTS PURCHASE AND SALE AGREEMENT' "
        "dated December 2009 which states no price - 'reference should be "
        "made to the Contract' - and Exhibit I is a prepared 'Termination of "
        "Memorandum' that releases even that notice at closing",
   eff="2010-10-14", ans=["VALUE", "IDENTIFY"],
   note="⚠ A MEMORANDUM GIVES NOTICE A CONTRACT EXISTS WHILE RECORDING NONE "
        "OF ITS TERMS, AND THE TERMINATION ERASES THE NOTICE. So the ONLY "
        "route to an air-rights price in this corpus is the tax stamp. Both "
        "exhibits are UNEXECUTED blank forms"),
 C("c2010-lav-easement", "2010102601040006", "p008", "easement",
   subject="1008000053", vfrom=23.0, vdatum="curb level", dur="perpetual",
   hext="20 feet north of the lot 53 rear lot line",
   text="'120 Owner hereby grants to Developer a perpetual easement for "
        "LIGHT, AIR AND VIEW above the portion of the 120 Owner Land "
        "beginning at the rear lot line and extending ... a distance of "
        "TWENTY (20') FEET to the north of such rear lot line, beginning at "
        "a height of TWENTY-THREE (23') FEET above curb level' - with 120 "
        "Owner permitted to keep its existing building in the easement area",
   eff="2010-10-14", ans=["ENCUMBRANCE", "ENVELOPE"],
   note="⚠ ONE-DIRECTIONAL: lot 53 burdened, lot 49 benefited, NOT mutual. "
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
   note="the operative body text and the annexed form disagree on what was "
        "granted. The form binds only 'if requested in writing by Developer' "
        "- contingent, not live"),
 C("c2010-pagecount-three", "2010102601040006", "p001", "defect",
   text="⚠ THREE DIFFERENT PAGE COUNTS, NONE AGREEING. The cover header says "
        "'PAGE 1 OF 116', a separate field says 'Document Page Count: 114', "
        "and 110 images exist on disk",
   eff="2010-11-16", ans=["IDENTIFY"],
   note="⚠ my integrity check assumes ONE authoritative count per cover. "
        "This document has two that disagree with each other AND with disk"),
'''


def main():
    p = pathlib.Path("claims.py")
    t = p.read_text(encoding="utf-8")
    have = re.findall(r'C\("([^"]+)"', t)
    hdrs = list(re.finditer(r"^ # ---- .*$", t, re.M))
    anchor = hdrs[-1].group(0)
    t = t.replace(anchor, NEW + anchor, 1)
    p.write_text(t, encoding="utf-8")
    added = [c for c in re.findall(r'C\("([^"]+)"', NEW)]
    print(f"recorded {len(added)} claims that existed only as prose: "
          f"{', '.join(added)}")


main()
