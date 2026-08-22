"""THE CURRENT LIEN, 2023 AND 2025. 53 of 53 pages read across six documents.

⚠ AND THE GAP THAT MATTERS MOST: THE $120,000,000 CEMA IS NOT IN THE CORPUS.
  I have been calling 2023110100486011 "the 2023 CEMA" for hours. Its own
  cover page says ASSIGNMENT OF LEASES AND RENTS. The actual consolidated
  mortgage is CRFN 2023000287582 and it was never fetched.
"""
import pathlib
import re

NEW = '''
 # ---- ⚠ the operative instrument was never fetched -----------------------
 C("c2023-cema-missing", "2025101700864002", "p011", "defect",
   text="⚠ THE $120,000,000 CONSOLIDATED MORTGAGE ITSELF IS NOT IN THIS "
        "CORPUS. It is CRFN 2023000287582, recorded 2023-11-06, and no "
        "folder on disk holds it. Every figure I have for the current lien "
        "comes from OTHER instruments RECITING it - the companion assignment "
        "of rents, the section 255 affidavit, and the 2025 assignment's "
        "Exhibit B",
   eff="2023-11-06", stated="2025-10-23", ev="derived", ans=["DEBT", "IDENTIFY"],
   note="⚠ AND I MISNAMED THE SUBSTITUTE. I have been calling document "
        "2023110100486011 'the 2023 CEMA' for hours; its own cover page reads "
        "'Document Type: ASSIGNMENT OF LEASES AND RENTS'. The recitals are "
        "consistent across two law firms two years apart, so the numbers hold "
        "- but the operative granting language, the maximum-principal clause "
        "and any representations of the actual mortgage remain UNREAD. This "
        "is the single largest hole in the decode"),

 # ---- ⚠ Chelsea 25 Hotel LLC — answered, and the answer is a hole --------
 C("c2023-chelsea-entry", "2023110100486011", "p019", "unresolved",
   text="CHELSEA 25 HOTEL LLC ENTERS THE CHAIN EXACTLY ONCE, AT ITEM 10: "
        "'Gap Mortgage dated as of October 16, 2023, made by Chelsea 25 Hotel "
        "LLC and Lam Gen 25 LLC to MetLife Commercial Mortgage Originator, "
        "LLC, in the principal amount of $25,490,000.00 (Mortgage Tax Paid: "
        "$713,720.00)'. It appears in NONE of items 1 through 9, which run "
        "112 West 25 Company (1990) to Edelman Family LP (1998) to 112-118 "
        "West 25th LLC (2007, 2012) to Lam Gen 25 LLC (2013-2020)",
   eff="2023-10-16", stated="2023-11-06", ans=["TITLE", "DEBT"],
   note="⚠ IT BECOMES A MORTGAGOR BY SIGNING A NEW MORTGAGE, NOT BY TAKING "
        "TITLE. No recorded deed or conveyance anywhere in this corpus shows "
        "Chelsea 25 Hotel LLC acquiring the fee from its predecessors. "
        "Confirmed independently by two firms two years apart - Dentons in "
        "2023 (p019) and Nelson Mullins in 2025 (2025101700864002 p010), "
        "same CRFN 2023000287581. ⚠ HOW IT HOLDS FEE TITLE IS STILL "
        "UNANSWERED and the instrument that would answer it is not here"),
 C("c2023-chelsea-swears", "2023110100486006", "p008", "defect",
   text="⚠ the section 275 affidavit swears 'That I am the Manager of CHELSEA "
        "25 HOTEL LLC ... and LAM GEN 25 LLC ... THE MORTGAGOR UNDER THE "
        "MORTGAGE WHICH IS BEING ASSIGNED' - but the mortgage being assigned "
        "is the 2015 Building Loan Mortgage 'made by LAM GEN 25 LLC' ALONE. "
        "Chelsea 25 Hotel LLC is not a party to that 2015 instrument on its "
        "face",
   eff="2023-10-12", stated="2023-11-06", ans=["TITLE", "IDENTIFY"],
   note="sworn the same week as the gap mortgage that first brings Chelsea 25 "
        "into privity. By October 2023 the drafters treat Chelsea 25 Hotel "
        "LLC and Lam Gen 25 LLC as ONE 'Mortgagor' unit - fee plus leasehold "
        "- even on instruments that predate Chelsea 25 entirely"),
 C("c2023-operating-lessee", "2023110100486011", "p003", "unresolved",
   text="the recorded text names LAM GEN 25 LLC as the 'OPERATING LESSEE' and "
        "CHELSEA 25 HOTEL LLC as the borrower - the security instrument is "
        "'executed by Assignor and LAM GEN 25 LLC ... (Operating Lessee)' and "
        "the loan agreement is 'executed by and between Assignor and "
        "Assignee, AND JOINED BY THE OPERATING LESSEE'",
   eff="2023-10-16", ans=["TENANCY", "TITLE"],
   note="⚠ THIS IS THE STRUCTURE. A fee owner and an operating lessee, both "
        "signing. It is the standard hotel split - propco holds the real "
        "estate, opco holds the operating lease and the franchise. It also "
        "explains the 2007 estate merger in reverse: the estates were merged "
        "to build, then re-split to operate"),

 # ---- 2025: MetLife was PAID IN FULL -------------------------------------
 C("c2025-metlife-paid", "2025101700864001", "p002", "unresolved",
   text="MetLife 'having received FULL PAYMENT of the obligations mentioned "
        "in and secured by that certain Assignment of Leases described on "
        "SCHEDULE I ... does hereby consent that said Assignment of Leases be "
        "terminated' - dated 2025-10-16",
   eff="2025-10-16", stated="2025-10-23", ans=["DEBT", "INCOME"],
   note="⚠ METLIFE WAS TAKEN OUT, NOT MERELY ASSIGNED. The same day it "
        "assigns the mortgages to Deutsche Bank it also terminates its rents "
        "assignment for full payment. This is the terminate-and-rebuild "
        "grammar again (c-tlr-assignment-grammar), now on its fourth "
        "observed cycle: 2013, 2014, 2023, 2025"),
 C("c2025-db-norecourse", "2025101700864002", "p004", "unresolved",
   text="MetLife assigns to Deutsche Bank 'without recourse ... without "
        "covenant, warranty or representation ... including but not limited "
        "to, the enforceability or collectability' - representing only that "
        "it owns the debt, was authorised to assign, and made no prior "
        "conflicting assignment",
   eff="2025-10-16", stated="2025-10-23", ans=["DEBT", "PRIORITY"],
   note="⚠ NO BORROWER-DEFAULT REPRESENTATION ANYWHERE. Across all six "
        "documents and 53 pages, nothing asserts the borrower is not "
        "currently in default. The only sworn statements are 'no new "
        "indebtedness', 'no reloans or readvances' and 'not acting as a "
        "nominee'. Compare the 2013 spreader, which DID carry a dated "
        "no-default representation - the record got weaker over twelve years"),
 C("c2025-275-artifact", "2025101700864002", "p004", "defect",
   text="⚠ two sentences that contradict each other in the same paragraph: "
        "'This Assignment is not subject to the requirements of Section 275 "
        "of the Real Property Law. The assignee set forth on the assignment "
        "of mortgage TO WHICH THIS AFFIDAVIT IS ATTACHED is not acting as a "
        "nominee of the mortgagor' - leftover section 275 affidavit "
        "boilerplate pasted into a document that disclaims section 275, and "
        "there is no affidavit attached",
   eff="2025-10-23", ans=["IDENTIFY"],
   note="a drafting artifact, not a representation. Third instance of the "
        "same species this session, with the 2014 'NINETEEN MILLION' template "
        "carry-over and the 2014 'Termination of Assignment' word swap"),
 C("c2023-gap-tax", "2023110100486011", "p013", "tax_paid",
   num=713_720.00, unit="USD",
   text="'secures additional indebtedness ... in the amount of $25,490,000.00 "
        "... upon which a mortgage tax of $713,720.00 is being paid "
        "simultaneously ... and consolidates the Existing Mortgage with the "
        "Gap Mortgage to form a single lien in the consolidated amount of "
        "$120,000,000.00'",
   eff="2023-11-06", ans=["DEBT", "VALUE"],
   note="$713,720 / $25,490,000 = 2.800% exactly - the commercial rate, paid "
        "on the new money only, with the other $94,510,000 exempt under 255. "
        "The same grammar as 1998, 2007, 2012, 2013, 2014 and 2015"),
 C("c2023-firstlien", "2023110100486011", "p003", "unresolved",
   text="'Loan: A first mortgage loan in an amount of $120,000,000.00 from "
        "Assignee to Assignor'",
   eff="2023-10-16", ans=["PRIORITY", "DEBT"],
   note="an express first-lien statement in the DEFINED TERMS of the "
        "companion instrument - not in the mortgage, which is not in the "
        "corpus"),
 C("c2023-norate-again", "2023110100486011", "p003", "unresolved",
   text="NO interest rate and NO maturity date appear in any of the 53 pages "
        "across all six 2023 and 2025 documents. The Note is defined only as "
        "being 'in the amount of the Loan'",
   eff="2023-10-16", ans=["DEBT"],
   note="⚠ THIRTY-FIVE YEARS UNBROKEN. 1990, 2007, 2013, 2014, 2023, 2025 - "
        "every generation of this lien states its size and withholds its "
        "price. A decoder that expects to find a rate in ACRIS will never "
        "find one on this parcel"),
 C("c2025-marriott-silent", "2025101700864002", "p001", "unresolved",
   text="NO mention of Marriott, a franchise agreement, or a right of first "
        "refusal appears anywhere in the 2023 or 2025 paperwork - all 53 "
        "pages read. 'Renaissance Chelsea' appears only as a running page "
        "footer, not as a party or a contractual reference",
   eff="2025-10-23", ans=["ENCUMBRANCE", "TENANCY"],
   note="⚠ THE 2014 SUBORDINATION IS CONDITIONAL - Marriott's ROFR is "
        "subordinate only 'for so long as ... the Bank is not a Competitor or "
        "Affiliate of a Competitor'. Two lender changes have since occurred "
        "and NEITHER addresses that condition on the record. ⚠ The running "
        "footer is the only trace in the current paperwork that this is a "
        "branded hotel at all"),
 C("c2023-lender-chain-end", "2025101700864002", "p004", "party_role",
   text="the current holder is DEUTSCHE BANK AG, NEW YORK BRANCH, taking "
        "assignment from MetLife Commercial Mortgage Originator LLC on "
        "2025-10-16, recorded 2025-10-23 as CRFN 2025000287678",
   eff="2025-10-16", stated="2025-10-23",
   parties=["DEUTSCHE BANK AG, NEW YORK BRANCH (assignee)",
            "METLIFE COMMERCIAL MORTGAGE ORIGINATOR, LLC (assignor)",
            "Brett Ulrich (Senior Director, MetLife Commercial Mortgage "
            "Income Fund GP, LLC - signs for the assignor)"],
   ans=["DEBT", "CONSENT"],
   note="THIRTEEN HOLDERS, THIRTY-FIVE YEARS, ONE LIEN: Apple Bank -> Queens "
        "County Savings -> New York Community -> Anglo Irish -> Irish Bank "
        "Resolution -> LSREF2 Clover Trust -> Wells Fargo -> LSREF2 Clover "
        "Trust -> UBS -> Goldman Sachs -> Shanghai Commercial -> MetLife -> "
        "Deutsche Bank"),
'''


def main():
    p = pathlib.Path("claims.py")
    t = p.read_text(encoding="utf-8")
    m = re.search(r"^ # ---- 2025.*$", t, re.M)
    if not m:
        m = re.search(r"^ # ---- 202[0-9].*$", t, re.M)
    assert m, "no anchor"
    t = t.replace(m.group(0), NEW + m.group(0), 1)
    p.write_text(t, encoding="utf-8")
    print("recorded 12 claims for the current lien")


main()
