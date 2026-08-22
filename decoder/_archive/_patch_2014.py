"""THE 2014 SHANGHAI COMMERCIAL BATCH. 62 of 62 pages read.

⚠ AND THE FINDING THAT ONLY APPEARS BY CROSSING TWO AGENTS' WORK:
   THREE INSTRUMENTS STATE THREE DIFFERENT FIGURES FOR THE SAME 1990 TAX
   PAYMENT, AND EACH ONE IS HIGHER THAN THE LAST.
"""
import pathlib
import re

NEW = '''
 # ---- ⚠ THE DRIFT: the same tax payment, three different figures ---------
 C("c-taxcredit-drift", "2014112601161005", "p029", "defect",
   text="⚠ THREE INSTRUMENTS STATE THREE DIFFERENT FIGURES FOR THE TAX PAID "
        "ON THE SAME 1990 MORTGAGE, EACH HIGHER THAN THE LAST. The 1990 "
        "instrument itself records $22,500.00 (margin note p001 AND machine "
        "stamp p026). The 2003 section-255 affidavit claims $27,500.00. The "
        "2014 section-255 affidavit claims $28,000.00",
   eff="2014-12-02", ev="derived", ans=["CAPITAL", "IDENTIFY"],
   note="⚠ EACH FIGURE IS THE BASIS OF AN EXEMPTION FROM PAYING TAX AGAIN. "
        "The 1998 mortgage drifts too: the instrument endorsement says "
        "$4,528.00 (components summing exactly), the 2003 affidavit says "
        "$4,527.56, the 2014 affidavit says $4,641.20. OBSERVATION, NOT "
        "PROOF OF INTENT: $28,000 is exactly 2.800% of $1,000,000 - the 2014 "
        "commercial rate, not the 1990 one - and $27,500 is exactly 2.750%. "
        "Both later figures look RECOMPUTED at the then-current rate rather "
        "than READ off the original instrument. The $4,641.20 does not fit "
        "that pattern and is unexplained. ALL FIGURES ARE HANDWRITTEN. "
        "⚠ NO SINGLE DOCUMENT REVEALS THIS - it only appears by crossing the "
        "microfilm read against the 2014 read"),

 # ---- 2014: the Shanghai Commercial arrival ------------------------------
 C("c2014-split", "2014112601161005", "p004", "consolidation",
   num=7_500_000, unit="USD",
   text="the $48,000,000 is $40,500,000 EXISTING plus $7,500,000 NEW - and "
        "both figures appear ONLY IN HANDWRITING. p004 margin: 'New money # "
        "7,500,000 is forwarded to me.' p022 beside Schedule items 5A and 5B: "
        "'Current unpaid principal $40,500,000.00'",
   eff="2014-11-25", stated="2014-12-02", ans=["CAPITAL"],
   note="⚠ THE TYPED TEXT SAYS $48,000,000.00 EVERYWHERE AND WOULD READ AS "
        "$48M OF NEW LENDING TO ANYONE WHO SKIPS THE MARGINALIA. The tax "
        "record proves the split: taxable $0.00 / exemption 255 / MRT $0.00 "
        "on this instrument, with $210,000 (= 2.800% x $7,500,000) paid on "
        "the companion gap mortgage 2014112601161004"),
 C("c2014-nineteen-million", "2014112601161005", "p014", "defect",
   text="⚠ 'THE MAXIMUM AMOUNT OF PRINCIPAL INDEBTEDNESS SECURED BY THIS "
        "MORTGAGE ... IS NINETEEN MILLION AND 00/100 DOLLARS "
        "($48,000,000.00)' - the words and the figures disagree by "
        "$29,000,000, and the SAME defect is recorded a second time in the "
        "companion assignment of rents at 2014112601161006 p003",
   eff="2014-12-02", ans=["CAPITAL"],
   note="⚠ a template carry-over from an unrelated $19M deal that survived "
        "two rounds of review and got recorded TWICE. Under NY construction "
        "the WRITTEN WORDS normally prevail over figures - so as recorded, "
        "the maximum-principal clause of the operative lien is internally "
        "contradictory on $29,000,000. Not repaired here; recorded as a "
        "defect. Compare the 1998 CEMA's own words/numerals conflict "
        "(c1998-cema-typo) - the same class of error, sixteen years apart"),
 C("c2014-lender", "2014112601161005", "p001", "party_role",
   text="the 2014 lender is SHANGHAI COMMERCIAL BANK LTD., NEW YORK BRANCH - "
        "'a banking corporation organized under laws of the Hong Kong Special "
        "Administrative Region of the People's Republic of China'. Goldman "
        "Sachs Bank USA is the OUTGOING holder, assigning out at Schedule "
        "item 5B",
   eff="2014-11-25", stated="2014-12-02",
   parties=["SHANGHAI COMMERCIAL BANK LTD., NEW YORK BRANCH (mortgagee)",
            "LAM GEN 25 LLC (mortgagor)",
            "GOLDMAN SACHS BANK USA (outgoing holder)"],
   ans=["CAPITAL", "PARTY"],
   note="any debt-stack read still showing Goldman on this lot after "
        "2014-12-02 is stale. Shanghai Commercial holds it for nine years, "
        "until the 2023 MetLife assignment"),
 C("c2014-loanagt-controls", "2014112601161005", "p014", "unresolved",
   text="section 8.07: 'Wherever there is any conflict or inconsistency "
        "between any terms or provisions of this Mortgage and the Loan "
        "Agreement, the terms and provisions of the Loan Agreement shall "
        "control' - and Article 1 sends every undefined term there too",
   eff="2014-11-25", ans=["CAPITAL"],
   note="⚠ NOTHING ECONOMIC IS ON THE RECORD. No rate, no maturity, no "
        "first-lien representation, NO REPRESENTATIONS ARTICLE AT ALL, no "
        "no-default representation, no spreader. This mortgage is a LIEN "
        "NOTICE, NOT A TERMS DOCUMENT. Section 8.04 refers to 'INTEREST ... "
        "AT THE RATES SET FORTH IN THE LOAN AGREEMENT' without stating them. "
        "The unbroken line runs 1990 -> 2007 -> 2014 -> 2023 -> 2025"),
 C("c2014-devrights-mortgaged", "2014112601161005", "p005", "easement",
   text="section 3.01(c) mortgages 'air rights and development rights' along "
        "with the fee - the transferred floor area is itself collateral",
   eff="2014-11-25", ans=["ENVELOPE", "CAPITAL"],
   note="⚠ THE LOT'S DEVELOPMENT RIGHTS ARE BORROWED AND THEN PLEDGED. "
        "Exhibit A ties five separate zoning-lot development and easement "
        "agreements into this parcel - Tax Lot 20 (CRFN 2008000078652), Lot "
        "21 (2013000241549), Lot 22 (2013000241545), Lot 23 (2013000007933), "
        "and Lots 53/55/56 (2010000384312). Any buildable-SF read on this lot "
        "must clear all five AND this lien"),
 C("c2014-alr-absolute", "2014112601161006", "p004", "easement",
   text="'IT IS THE INTENTION OF ASSIGNOR AND ASSIGNEE THAT THE FOREGOING "
        "ASSIGNMENT ESTABLISH A PRESENT AND ABSOLUTE TRANSFER ... This "
        "Agreement is an absolute assignment to Assignee and not an "
        "assignment as security' - with a licence back that revokes "
        "automatically on default, 'without the necessity of the appointment "
        "of a receiver and whether or not Assignee has taken possession'",
   eff="2014-11-25", ans=["INCOME", "ENCUMBRANCE"],
   note="the assignment reaches security deposits, lease TERMINATION fees, "
        "loss-of-rents insurance proceeds, and 'all claims and sums paid as "
        "damages ... with respect to a rejection of a Lease in bankruptcy'. "
        "⚠ CONDEMNATION PROCEEDS ARE NOT IN THE GRANT - they appear only at "
        "p010 section 15 as something whose collection does not waive a "
        "default. Condemnation is carried by the mortgage, not by this"),
 C("c2014-lease-lock", "2014112601161006", "p008", "easement",
   text="section 11: without prior written consent the borrower shall not "
        "(a) enter into or extend any Lease, (b) cancel, terminate or accept "
        "surrender, (c) reduce rent or accept rent more than one month in "
        "advance, (d) materially modify, or (e) consent to assignment or "
        "subletting unless the tenant remains liable - and any such act 'at "
        "the option of Assignee ... shall be of no force or effect and shall "
        "constitute an Event of Default'",
   eff="2014-11-25", ans=["ENCUMBRANCE", "TENANCY"],
   note="⚠ ONE GAP: 'subordinate' is NOT among the prohibitions, and the "
        "agent found no subordination bar anywhere in p003-p016. The 2007 "
        "CEMA had an absolute ground-lease subordination bar; this one does "
        "not"),
 C("c2014-note-lien-gap", "2014112601161005", "p023", "defect",
   text="⚠ Exhibit C item (4) states a $67,258,543 consolidated NOTE against "
        "a same-day $39,229,334 consolidated MORTGAGE - the 2007 note/lien "
        "gap, carried forward on the face of a 2014 instrument and still "
        "unreconciled seven years later",
   eff="2014-11-25", ans=["CAPITAL"],
   note="INDEPENDENT CORROBORATION of c2007-facility, found by a different "
        "agent in a different document seven years downstream. Also in the "
        "same exhibit: the 2007 gap note is $38,311,287.14 in Exhibit C but "
        "$38,311,287.86 in Exhibit B - a 72-cent disagreement inside one "
        "instrument"),
 C("c2014-onesided", "2014112601161006", "p016", "defect",
   text="the assignment of leases and rents is EXECUTED ONE-SIDED - only the "
        "assignor signs. There is no assignee signature block anywhere in "
        "p003 to p016, notwithstanding section 31 contemplating signature 'by "
        "or on behalf of each of the parties hereto'",
   eff="2014-11-25", ans=["IDENTIFY"],
   note="also: same signer, same day, same room, TWO NOTARIES - Suchuan "
        "Wangyu took the mortgage acknowledgment, Helen Eng took the "
        "assignment and both section 255 affidavits. Wangyu's commission "
        "expired 2014-12-06, eleven days after the acknowledgment and four "
        "days after recording - valid, but the tightest date in the file"),
 C("c2014-alr-termination", "2014112601161006", "p012", "easement",
   text="section 20: the assignment 'shall be released and terminated as, "
        "when and to the extent the Security Instrument is released and "
        "discharged WITHOUT THE NEED TO EXECUTE AND DELIVER FURTHER "
        "INSTRUMENTS' - a standalone recorded satisfaction is optional and "
        "borrower-funded",
   eff="2014-11-25", ans=["INCOME", "IDENTIFY"],
   note="⚠ TERMINATION IS AUTOMATIC AND DERIVATIVE, SO IT LEAVES NO RECORD. "
        "A reader watching for a recorded satisfaction of the assignment will "
        "never see one. And 'indefeasibly paid in full' means a later "
        "preference clawback reanimates the obligation - the indemnity at "
        "section 28 and expenses at section 27 are not carved out of the "
        "release"),
'''


def main():
    p = pathlib.Path("claims.py")
    t = p.read_text(encoding="utf-8")
    m = re.search(r"^ # ---- 2015.*$", t, re.M) or re.search(
        r"^ # ---- 201[5-9].*$", t, re.M)
    assert m, "no anchor"
    anchor = m.group(0)
    t = t.replace(anchor, NEW + anchor, 1)
    p.write_text(t, encoding="utf-8")
    print("recorded 11 claims from the 2014 batch above:", anchor.strip())


main()
