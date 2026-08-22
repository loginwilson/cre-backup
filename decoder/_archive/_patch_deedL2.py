"""FULL L2 EXTRACTION — 2013080901116003, every slot, with clause proofs.

⚠ THE POINT OF THIS RUN: prove the agent EXTRACTS, not just that it reads a
tax block. Nine slots, one page, four clause proofs at 41 KB total.

And three slots differ materially from the 2007 deed on the same parcel —
which is exactly what a slot menu is for. Reading both as prose, six years
apart, I would have called them "a bargain and sale deed" twice.
"""
import patchlib

NEW = '''
 C("c2013-deed-recital", "2013080901116003", "p002", "consideration_recited",
   num=10, unit="USD",
   text="'WITNESSETH, that Grantor, in consideration of TEN DOLLARS ($10.00) "
        "and other valuable consideration paid by Grantee, the receipt and "
        "sufficiency of which are hereby acknowledged, does hereby grant and "
        "release unto Grantee'",
   eff="2013-08-07", ans=["VALUE"],
   note="⚠ THE TRAP, CONFIRMED AT SCALE. $10 recited against $67,500,000 of "
        "stamps on the same document — a 6,750,000x error for anyone reading "
        "the grant instead of the cover. Proof "
        "proofs/51ee410748d55a7a.png"),
 C("c2013-deed-nocovenants", "2013080901116003", "p002", "unresolved",
   text="⚠ THIS DEED IS A 'BARGAIN AND SALE DEED WITHOUT COVENANTS' — the "
        "title says so outright. Its ONLY covenant is the statutory Lien Law "
        "section 13 trust-fund clause: Grantor 'will receive the "
        "consideration for this conveyance and will hold the right to "
        "receive such consideration as a trust fund'",
   eff="2013-08-07", ans=["TITLE"],
   note="⚠ MATERIALLY WEAKER THAN THE 2007 DEED ON THE SAME LAND, which was "
        "a 'Bargain and Sale Deed WITH Covenant Against Grantor's Acts'. "
        "Extell gave Lam LESS warranty than Edelman gave Extell — the "
        "grantor does not even promise it has not itself encumbered the "
        "property. Two deeds, six years apart, that read identically as "
        "prose and differ where it counts. Proof "
        "proofs/ea19b03e1ce47ddc.png"),
 C("c2013-deed-devrights", "2013080901116003", "p002", "easement",
   text="the grant expressly carries the assemblage: 'TOGETHER with any "
        "rights of way, appendages, appurtenances, easements, sidewalks, "
        "alleys, gores or strips of land adjoining or appurtenant to the "
        "above described premises and used in conjunction therewith, ANY "
        "DEVELOPMENT RIGHTS APPURTENANT to the above described premises'",
   eff="2013-08-07", ans=["ENVELOPE", "TITLE"],
   note="⚠ THE 2007 DEED SAID NOTHING ABOUT DEVELOPMENT RIGHTS — I recorded "
        "that absence as a finding. By 2013 the assemblage existed (53,578 "
        "sf in 2010, 22,845 in 2012, three more transfers in 2013) and the "
        "deed conveys it explicitly. THE DEED LANGUAGE TRACKS WHAT THE "
        "PARCEL HAD BECOME. Proof proofs/288af62f05938866.png"),
 C("c2013-deed-prior", "2013080901116003", "p002", "cross_reference",
   text="'The premises herein described are intended to be the same, no "
        "more, no less, as that described in: Deed recorded in "
        "CRFN2007000336512'",
   eff="2013-08-07", ans=["TITLE"],
   note="a clean prior-deed recital pointing at the 2007 Edelman-to-Extell "
        "conveyance — ⚠ CONTRAST THE 1998 DEED, whose recital fused the date "
        "of one 1971 instrument with the reel/page of another running the "
        "opposite way. Proof proofs/2b600143b0830623.png"),
 C("c2013-deed-nosubject", "2013080901116003", "p002", "unresolved",
   text="⚠ NO 'SUBJECT TO' CLAUSE AND NO SCHEDULE OF PERMITTED EXCEPTIONS. "
        "The whole grant was read: parties, witnesseth, the Exhibit A "
        "reference, the two TOGETHER-WITH clauses, habendum, Lien Law 13, "
        "signature line. Nothing is taken subject to",
   eff="2013-08-07", ans=["TITLE", "ENCUMBRANCE"],
   note="⚠ THE SAME ABSENCE AS THE 2007 DEED. A $67,500,000 conveyance of a "
        "parcel carrying seven air-rights agreements, a Marriott franchise "
        "ROFR and a $40,500,000 mortgage discloses NONE of it. ABSENT is a "
        "finding here, not a gap — anyone representing that the deed shows "
        "the encumbrances is wrong twice over"),
 C("c2013-deed-handwritten", "2013080901116003", "p002", "defect",
   text="the transfer tax is written by hand in the left margin — 'TT "
        "270,000' — alongside the typed body",
   eff="2013-08-07", ans=["VALUE", "IDENTIFY"],
   note="⚠ IT CORROBORATES THE COVER STAMP ($270,000 NYS RETT) AND NO OCR "
        "REACHES IT. Fifth instance on this parcel of a material figure "
        "existing only as handwriting — after the 2003 and 2014 prior-tax "
        "affidavits, the 2013 and 2014 new-money splits, and the 2012 "
        "$1,000 schedule conflict"),
'''

patchlib.apply(NEW)
