"""⚠ RECORDING THE 2015 CONSTRUCTION-LOAN TERMS I REPORTED BUT NEVER STORED.

An agent read 2015091001439003 (36 of 37 pages) and 2015091001439004 hours ago
and returned a full covenant table. I summarised it to the user in prose and
moved on. integrity.py then listed both documents as "fetched but never read",
because the only claims I had recorded from them came from the cover page.

That is the failure mode this whole system exists to prevent, committed by me:
the prose was right, and it was not evidence.
"""
import pathlib
import re

NEW = '''
 # ---- the 2015 construction covenants — recorded late, see module docstring
 C("c2015-lienlaw13", "2015091001439003", "p014", "easement",
   text="the Building Loan Mortgage carries the Lien Law section 13 "
        "trust-fund covenant: the borrower 'shall receive the advances "
        "secured hereby and shall hold the right to receive such advances as "
        "a trust fund to be applied first for the purpose of paying the cost "
        "of any improvement ... before using any part of the total of the "
        "same for any other purpose'",
   eff="2015-09-02", ans=["PERMIT", "CAPITAL"],
   note="the covenant exists specifically to police CONSTRUCTION advances. "
        "Present in identical words in the Project Loan Mortgage at "
        "2015091001439004 p014. ⚠ NO Lien Law section 22 building loan "
        "CONTRACT is referenced in any page read - section 22 requires the "
        "contract to be FILED, and it is not in this batch"),
 C("c2015-progress", "2015091001439003", "p017", "easement",
   text="section K.3: 'As soon as available, but not later than the first day "
        "of each calendar month and/or upon request, the Mortgagor shall "
        "provide to the Mortgagee, a progress report of the construction on "
        "the Premises'",
   eff="2015-09-02", ans=["PERMIT"],
   note="⚠ A MONTHLY CONSTRUCTION-PROGRESS OBLIGATION IS THE CLEAREST "
        "RECORDED PROOF THAT THIS IS A REAL BUILD, not an inference from "
        "timing. But the reports themselves are private - the record tells "
        "you they exist and never what they said"),
 C("c2015-demo-consent", "2015091001439003", "p016", "easement",
   text="section H.2: the borrower 'shall not remove or demolish nor alter "
        "the design or structural character of any building now or hereafter "
        "erected upon the Premises without the prior written consent of the "
        "Mortgagee which consent shall not be unreasonably withheld or "
        "delayed' - conditioned on a no-default certificate, evidence the "
        "value will not be diminished, and additional security during works",
   eff="2015-09-02", ans=["ENCUMBRANCE", "PERMIT"],
   note="the reasonableness qualifier matters: most consents in this corpus "
        "are 'sole and absolute discretion'"),
 C("c2015-junior-bar", "2015091001439003", "p018", "easement",
   text="section L.4: 'There shall be no junior financing or junior mortgage/"
        "liens with respect to the Premises (other than for the benefit of "
        "the Mortgagee) without the prior written consent of the Mortgagee, "
        "which consent shall be in the Mortgagee's sole and absolute "
        "discretion'",
   eff="2015-09-02", ans=["ENCUMBRANCE", "CAPITAL"],
   note="with a matching bar on further borrowed money at L.1 and on "
        "transferring substantially all assets at L.2. This is what makes "
        "the 2018 splitter and the 2020 bridge loan lender-consented events "
        "rather than borrower choices"),
 C("c2015-trusts", "2015091001439003", "p017", "person",
   text="section K.1-K.4 requires annual tax returns 'of Mortgagor, and of "
        "each Guarantor and each of six named Trusts, prepared by a CPA' - "
        "the Raymond Lam 2012 Delaware Trust, the Teresa Lam 2012 Delaware "
        "Trust, the Jonathan Lam 2012 Delaware Trust, the Jeffrey Lam trust, "
        "the John Lam 2012 Trust and the Winnie Lam 2015 Trust",
   eff="2015-09-02",
   parties=["Raymond Lam (grantor)", "Teresa Lam (grantor)",
            "Jonathan Lam (grantor)", "Mui Hing Won Lam (grantor)",
            "Kin Chung Lam (grantor)", "Richard Tang (trust committee)",
            "Keith Lam (trust committee)", "Joann Lee (trust committee)"],
   ans=["PARTY", "CAPITAL"],
   note="⚠ THE REACH LADDER'S BEST RUNG ON THIS PARCEL. The deed gives an "
        "entity; the mortgage gives natural persons AND the family trust "
        "structure behind it. Note the document spells one person two ways "
        "on the SAME PAGE - 'Mui Hing Won Lam' as grantor of the John Lam "
        "trust and 'Mui Hing Wong Lam' as committee member of the Winnie Lam "
        "trust. Likely one person; recorded as the document has it"),
 C("c2015-appraisal", "2015091001439003", "p017", "easement",
   text="section J gives the lender 'the right, from time to time, upon "
        "reasonable notice to the Mortgagor, to conduct or cause to be "
        "conducted an appraisal or appraisals of the Premises, the cost of "
        "which shall be paid by the Mortgagor'",
   eff="2015-09-02", ans=["ENCUMBRANCE", "VALUE"],
   note="⚠ APPRAISALS EXIST FOR THIS PARCEL AND ARE BORROWER-FUNDED. They "
        "are never recorded. A recurring shape in this corpus: the record "
        "proves a valuation happened and withholds the number"),
 C("c2015-receiver", "2015091001439003", "p028", "easement",
   text="section G: on default 'the Mortgagee shall be entitled to the "
        "appointment of a receiver of the rents, issues and profits of the "
        "Premises without the necessity of proving either inadequacy of the "
        "security or insolvency of the Mortgagor'",
   eff="2015-09-02", ans=["ENCUMBRANCE", "INCOME"],
   note="section H adds that on a sale of less than all the premises 'this "
        "Mortgage shall continue as a lien on the remaining portion' - which "
        "is the clause the 2018 splitter operates against"),
 C("c2015-casualty-draw", "2015091001439003", "p012", "easement",
   text="casualty proceeds are released on construction-style draw mechanics: "
        "requisitions certified by 'a licensed A.I.A. architect'; 'No payment "
        "made prior to the final completion of work shall exceed ninety "
        "percent (90%) of the value of the work performed'; released 'not "
        "more than once a month' subject to safeguards 'the Mortgagee then "
        "requires in connection with construction loans for similar projects'",
   eff="2015-09-02", ans=["PERMIT", "CAPITAL"],
   note="⚠ THIS GOVERNS INSURANCE PROCEEDS, NOT LOAN ADVANCES. I nearly "
        "recorded it as the draw schedule. The actual draw schedule, the "
        "completion date and any description of the building live in the "
        "UNRECORDED Building Loan Agreement and are not obtainable from these "
        "documents"),
 C("c2015-title-policy", "2015091001439003", "p008", "cross_reference",
   text="Loan Title Insurance Policy No. 2730732-94145650, issued by Federal "
        "Standard Abstract, Inc. as agent for Fidelity National Title "
        "Insurance Company - with a SEPARATE policy (number ending 720) for "
        "the Project Loan Mortgage",
   eff="2015-09-02", ans=["TITLE"],
   note="two policies for two lien positions on the same land, same day"),
 C("c2015-releaseparcel", "2015091001439002", "p005", "easement",
   text="section 1.6, replacing Article 3: the borrower 'shall have the right "
        "to secure the release of the lien of the Mortgage (the "
        "'Prepayment Release') from the parcel commonly known as 113-117 West "
        "24th Street, New York, New York (the 'Release Parcel')'",
   eff="2015-09-02", ans=["CAPITAL", "PARCEL"],
   note="⚠ THE 2019 SUBDIVISION WAS DESIGNED IN 2015. This clause names the "
        "24th Street half as a RELEASE PARCEL four years before it becomes "
        "lot 50. The 2018 splitter moved $22,500,000 onto it; this clause is "
        "why that was possible"),
 C("c2015-crossdefault", "2015091001439002", "p005", "easement",
   text="section 1.5: 'The occurrence of any Default or Event of Default "
        "under the Building Loan Documents or the Project Loan Documents "
        "shall constitute a Default or Event of Default under the Land Loan "
        "Agreement and the Land Loan Documents'",
   eff="2015-09-02", ans=["CAPITAL"],
   note="the three facilities are cross-defaulted, so the $48M land loan and "
        "the $65.71M of construction money stand or fall together. Maturity "
        "moved to 2018-09-02 with one six-month extension option at a 0.25% "
        "fee, conditioned on extending the other facilities too"),
 C("c2015-lien-positions", "2015091001439003", "p008", "unresolved",
   text="the Building Loan Mortgage 'warrants that this Mortgage is and shall "
        "be maintained as a valid SECOND lien on the Premises'; the Project "
        "Loan Mortgage at 2015091001439004 p008 warrants a valid THIRD lien - "
        "both behind the pre-existing $48,000,000 Land Loan Mortgage",
   eff="2015-09-02", ans=["PRIORITY", "CAPITAL"],
   note="⚠ THE ONLY EXPLICIT LIEN-POSITION LADDER IN THE ENTIRE CORPUS. "
        "PRIORITY has been the thinnest function all session because almost "
        "nothing else states its rank on the face of the instrument"),
 C("c2015-recourse-absent", "2015091001439003", "p003", "unresolved",
   text="NO exculpation, non-recourse or limitation-of-liability clause "
        "appears in the Building Loan Mortgage - the agent read p003 through "
        "p035. A COMPLETION GUARANTY 'in favor of the Mortgagee dated of even "
        "date herewith' is referenced at p006 and is NOT recorded",
   eff="2015-09-02", ans=["CAPITAL"],
   note="⚠ ABSENT here is not the same as non-recourse. A completion guaranty "
        "implies separate guarantor exposure that the record cannot size. "
        "Contrast 2003, where non-recourse was granted expressly"),
'''


def main():
    p = pathlib.Path("claims.py")
    t = p.read_text(encoding="utf-8")
    m = re.search(r"^ # ---- 2018.*$", t, re.M) or re.search(
        r"^ # ---- 201[6-9].*$", t, re.M)
    assert m, "no anchor"
    t = t.replace(m.group(0), NEW + m.group(0), 1)
    p.write_text(t, encoding="utf-8")
    print("recorded 13 claims that existed only as prose")


main()
