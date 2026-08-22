"""THE 2013 SPREADER, ALL 61 PAGES.

⚠ AND IT CORRECTS MY OWN FRAMING. I told the user this was "the only true
  spreader in the chain" and briefed the agent that a spreader "extends an
  existing lien onto ADDITIONAL land". This one does not. It spreads over
  portions of THE SAME parcel not already covered. No new tax lot enters.
"""
import pathlib
import re

NEW = '''
 # ---- the 2013 spreader — and the correction to what I said it did -------
 C("c2013-spreader-scope", "2013081200922003", "p005", "unresolved",
   text="⚠ THE SPREADER DOES NOT REACH ANY ADDITIONAL TAX LOT. Section 4: the "
        "liens 'are hereby consolidated and coordinated so that together they "
        "shall hereafter constitute in law but one mortgage, a single, first "
        "lien upon the Premises securing the Indebtedness, and, as so "
        "consolidated and coordinated, ARE HEREBY SPREAD OVER THOSE PORTIONS "
        "OF THE PROPERTY NOT ALREADY COVERED THEREBY'",
   eff="2013-08-07", stated="2013-08-28", ans=["DEBT", "PARCEL"],
   note="⚠ CORRECTS MY OWN FRAMING. I called this 'the only true spreader in "
        "the chain' and briefed the agent that a spreader extends a lien onto "
        "ADDITIONAL LAND. It does not. 'Property' is Schedule C's defined "
        "term and 'Premises' is the single parcel in Schedule A - the spread "
        "is over interests in the SAME land the lien already sat on "
        "(fixtures, easements, after-acquired estates), not over new lots. "
        "The word 'spreader' in the title is doing less work than it looks"),
 C("c2013-devrights-contingent", "2013081200922003", "p022", "easement",
   text="development rights enter only as a FUTURE-ACQUISITION catch-all: "
        "'All additional lands, estates and development rights hereafter "
        "acquired by Mortgagor for use in connection with the Land and the "
        "development of the Land ... which may, from time to time, BY "
        "SUPPLEMENTAL MORTGAGE OR OTHERWISE be expressly made subject to the "
        "lien of this Security Instrument'",
   eff="2013-08-07", ans=["ENVELOPE", "DEBT"],
   note="⚠ CONTINGENT, NOT PRESENT. Contrast the companion assignment "
        "2013081200922001 p003, which splits '(i) the real property as "
        "described on Exhibit B-1 AND (ii) the development rights "
        "attributable to the real property as described on Exhibit B-2' into "
        "two parallel scheduled exhibits. The SPREADER has no such "
        "bifurcation - here the rights are boilerplate appurtenance plus a "
        "hook for a later supplemental mortgage. Two instruments in the same "
        "batch treat development rights completely differently"),
 C("c2013-consistent", "2013081200922003", "p052", "consolidation",
   num=40_500_000, unit="USD",
   text="the maximum principal secured is stated FOUR TIMES and every "
        "instance agrees - p004, p005, p006 and Schedule C section 16.7: 'the "
        "maximum amount of principal indebtedness secured by this Security "
        "Instrument at the time of execution hereof or which under any "
        "contingency may become secured ... is $40,500,000.00'",
   eff="2013-08-07", ans=["DEBT"],
   note="⚠ THE CONTROL CASE FOR THE 2014 DEFECT. Same law firm, same "
        "borrower, same lender family, fifteen months apart - this one is "
        "internally consistent four times over, and the 2014 instrument says "
        "'NINETEEN MILLION ... ($48,000,000.00)' twice. The 2014 error is a "
        "template failure, not house style. (This document has its own typo - "
        "'FORTY MILLION FIVE HUDNRED THOUSAND' at p004 - but the numerals "
        "and the intent agree)"),
 C("c2013-nodefault", "2013081200922003", "p005", "unresolved",
   text="section 1(b): 'As of the date hereof, there are no defaults or "
        "events of default under the Existing Notes and Mortgages, nor has "
        "any event occurred that would be a default thereunder with the "
        "passage of time, the giving of notice, or both' - speaking as of "
        "the stated execution date, August 7, 2013",
   eff="2013-08-07", ans=["DEBT", "PRIORITY"],
   note="⚠ THE ONLY DATED NO-DEFAULT REPRESENTATION FOUND IN THE CORPUS SO "
        "FAR. The 2014 CEMA has no representations article at all. A "
        "no-default rep with an as-of date is the single most useful sentence "
        "in a mortgage for reconstructing whether a borrower was in trouble - "
        "and it exists here and nowhere else"),
 C("c2013-firstlien", "2013081200922003", "p005", "unresolved",
   text="'a single, FIRST lien upon the Premises securing the Indebtedness'",
   eff="2013-08-07", ans=["PRIORITY"],
   note="an express first-lien statement. PRIORITY has been the thinnest "
        "function all session because instruments so rarely state their own "
        "rank on the face"),
 C("c2013-offrecord-mechanism", "2013081200922003", "p032", "unresolved",
   text="⚠ THERE IS NO 'THE LOAN AGREEMENT SHALL CONTROL' SENTENCE ANYWHERE "
        "IN 61 PAGES. The off-record mechanism here is different and quieter: "
        "whole CATEGORIES are defined by reference out. Section 4.4: the "
        "lender 'is expressly and primarily relying on the truth and accuracy "
        "of the warranties and representations set forth in ARTICLE 4 OF THE "
        "LOAN AGREEMENT'; section 14: 'All capitalized terms not defined "
        "herein shall have the respective meanings set forth in the Loan "
        "Agreement'; notices go to 'Section 8.12 of the Loan Agreement'",
   eff="2013-08-07", ans=["DEBT", "IDENTIFY"],
   note="⚠ A DISTINCTION WORTH KEEPING. I have been recording 'the unrecorded "
        "agreement controls' as one pattern. There are TWO: an express "
        "conflict clause (2007, 2014, 2023, 2025) and this - definitional "
        "hollowing, where no clause asserts priority but 'Event of Default' "
        "is used throughout Article 7 and DEFINED NOWHERE in the recorded "
        "text. The second is harder to spot and has the same effect"),
 C("c2013-norate", "2013081200922003", "p045", "unresolved",
   text="NO interest rate and NO maturity date appear in any of the 61 pages. "
        "'Maturity Date' is used only as an undefined cross-reference - 'not "
        "less than six (6) months prior to the stated Maturity Date' - and "
        "'Default Rate' likewise recurs with no numeric rate ever stated",
   eff="2013-08-07", ans=["DEBT"],
   note="61 pages, $40,500,000, and the price of the money is not in any of "
        "them. Consistent with 1990, 2007, 2014, 2023 and 2025"),
 C("c2013-notary-before", "2013081200922003", "p053", "defect",
   text="⚠ BOTH NOTARIZATIONS PREDATE THE INSTRUMENT. The mortgage "
        "acknowledgment (p053) and the section 255 affidavit jurat (p059) are "
        "each dated 'the 30 day of July, 2013' - EIGHT DAYS BEFORE the "
        "execution date the instrument recites for itself, 'made as of August "
        "7, 2013' (p004)",
   eff="2013-07-30", stated="2013-08-28", ans=["IDENTIFY"],
   note="⚠ compare the 1999 cancellation, where the notary's commission had "
        "EXPIRED before the acknowledgment date. Two instruments, fourteen "
        "years apart, both with acknowledgment dates that cannot be right. "
        "The 'as of' convention explains it but does not cure it"),
 C("c2013-onesided-again", "2013081200922003", "p053", "defect",
   text="only the mortgagor executes - the agent found NO Goldman Sachs Bank "
        "USA signature block in 61 pages",
   eff="2013-08-07", ans=["IDENTIFY", "CONSENT"],
   note="the same one-sided execution as the 2014 assignment of rents. A "
        "lender that never signs is normal for a mortgage and worth knowing "
        "before treating a signature block as evidence of who agreed"),
 C("c2013-handwritten-advance", "2013081200922003", "p004", "defect",
   text="a handwritten note sits beneath the typed WHEREAS clause reciting "
        "the $40,500,000 aggregate: '$1,500,000 was advanced to me'. A second "
        "handwritten annotation on the schedule at item 4(a) reads 'dated "
        "7/29/2013 by assignment of Mortgage to be recorded together "
        "herewith. unpaid principal $39,000,000.00 further assigned to "
        "Goldman Sachs Bank'",
   eff="2013-08-07", ans=["DEBT", "IDENTIFY"],
   note="⚠ THE NEW-MONEY SPLIT IS HANDWRITTEN AGAIN. $39,000,000 existing + "
        "$1,500,000 new = $40,500,000, and BOTH components exist only as "
        "marginalia - exactly as in 2014, where $40,500,000 + $7,500,000 = "
        "$48,000,000 was also only in handwriting. No OCR or text extraction "
        "finds either. THE MONEY IS IN THE MARGIN, TWICE"),
 C("c2013-pagecount-over", "2013081200922003", "p001", "defect",
   text="⚠ THE STATED PAGE COUNTS ARE ONE SHORT OF THE FILES ON DISK. The "
        "cover says 'Document Page Count: 53' with a banner 'PAGE 1 OF 55'; a "
        "second supporting-document cover at p057 says 'PAGE 1 OF 1' and "
        "lists a 4-page section 255 affidavit. 55 + 1 + 4 = 60. There are 61 "
        "images. The unaccounted page is p056, a continuation of the Exhibit "
        "A easement description covering Tax Lots 22, 23, 53, 55 and 56",
   eff="2013-08-28", ans=["IDENTIFY", "ENVELOPE"],
   note="⚠ MY INTEGRITY CHECK ONLY TESTS FOR TOO FEW PAGES. This is the "
        "opposite defect and it would have passed silently. An UNACCOUNTED "
        "page is as much a signal as a missing one - and this particular "
        "unaccounted page is the one listing the burdened lots"),
 C("c2013-easements-appurtenant", "2013081200922003", "p055", "easement",
   text="Exhibit A carries the light-and-air easements as APPURTENANT RIGHTS, "
        "not as land: 'TOGETHER WITH an easement for light and air over ... "
        "Tax Lot 20 ... Tax Lot 21 ...' and continuing to Lots 22, 23, 53, 55 "
        "and 56",
   eff="2013-08-07", subject="1008000053", ans=["ENVELOPE", "ENCUMBRANCE"],
   note="⚠ AN APPURTENANT EASEMENT IS NOT A FEE INTEREST. The seven burdened "
        "lots are NOT mortgaged - the lien reaches lot 49's RIGHT to light "
        "and air over them. A reader who treats the easement schedule as a "
        "collateral schedule overstates what the lender can foreclose on"),
'''


def main():
    p = pathlib.Path("claims.py")
    t = p.read_text(encoding="utf-8")
    m = re.search(r"^ # ---- 2014.*$", t, re.M)
    assert m, "no anchor"
    t = t.replace(m.group(0), NEW + m.group(0), 1)
    p.write_text(t, encoding="utf-8")
    print("recorded 12 spreader claims; corrected my own spreader framing")


main()
