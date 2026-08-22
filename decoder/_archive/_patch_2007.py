"""THE $2,300,000 IS ANSWERED. And $28.0M of the 2007 borrowing is invisible."""
import pathlib
import re

NEW = '''
 C("c2007-2p3m-answer", "2007062101109002", "p001", "sale_price",
   num=2_300_000, unit="USD",
   text="the $2,300,000 is the price of a SECOND, SEPARATE conveyance closing "
        "the same day - the assignment of the SUBLEASE from LGM Realty, "
        "L.L.C. to 112-118 West 25th LLC. It is NOT a component of the "
        "$42,700,000 fee purchase and must never be added to it",
   eff="2007-06-20", stated="2007-06-29", ev="derived",
   parties=["LMG REALTY, LLC (grantor, as indexed; spelled LGM Realty, "
            "L.L.C. in the mortgage exhibit)", "112-118 WEST 25TH LLC"],
   ans=["VALUE", "TENANCY"],
   note="THREE INDEPENDENT PROOFS. (1) the grantor is not the seller of the "
        "fee - doc ...002 p001 names LMG REALTY LLC; the deed ...001 p001 "
        "names EDELMAN FAMILY LIMITED PARTNERSHIP. (2) both stamps "
        "reconstruct $2,300,000 from two different taxing authorities at two "
        "different rates: NYC RPTT $60,375.00 / 2.625% and NYS RETT "
        "$9,200.00 / 0.4%. (3) the instrument is NAMED at doc ...004 p015 "
        "Exhibit A-2 item 4: 'Assignment and Assumption of Sublease dated as "
        "of June 20, 2007 by and between LGM Realty, L.L.C., as assignor, "
        "and 112-118 West 25th LLC, as assignee'"),
 C("c2007-pagecount0", "2007062101109002", "p001", "defect",
   text="'Document Page Count: 0' - this is a TAX-RETURN-ONLY filing with no "
        "recordable instrument attached, which is exactly how a leasehold or "
        "economic-interest transfer is reported when the transfer instrument "
        "itself is never recorded",
   eff="2007-06-29", ans=["IDENTIFY", "VALUE"],
   note="THIS IS WHY THE INDEX LOOKED BROKEN - a $2.3M figure floating with "
        "no document behind it. The tax stamps are the entire evidentiary "
        "content. A decoder that requires a document body drops it silently"),
 C("c2007-merger", "2007062101109004", "p015", "unresolved",
   text="Exhibit A-2 shows the buyer collapsing THREE ESTATES on 2007-06-20 - "
        "the fee (deed, $42.7M), the prime lease (item 3, Edelman assignor), "
        "and the sublease (item 4, LGM, $2.3M) - ending at item 5, a 'Second "
        "Amendment to Lease ... by and between 112-118 West 25th LLC, as "
        "landlord, and 112-118 West 25th LLC, as tenant': a merger of "
        "estates in one owner",
   eff="2007-06-20", ans=["TITLE", "TENANCY"],
   note="the landlord and the tenant are the same LLC. This is why the site "
        "could later be developed - a split fee/leasehold cannot be"),
 C("c2007-facility", "2007062101109006", "p003", "unresolved",
   num=67_258_543, unit="USD",
   text="the LOAN is $67,258,543 but the RECORDED LIEN on lot 49 is capped at "
        "$39,229,334 - doc ...006 p003 prints both in adjacent recitals, the "
        "single reconciliation point for the whole batch",
   eff="2007-06-20", ans=["CAPITAL"],
   note="~$28.0M OF THE BORROWING IS SECURED ELSEWHERE AND IS INVISIBLE IN "
        "THIS PROPERTY'S RECORD. Anyone sizing outstanding debt from recorded "
        "face amounts understates this borrower's exposure. The CEMA's own "
        "p007 recital calls $67,258,543 'the outstanding aggregate principal "
        "amount of the Original Notes', which sits badly against Schedule B "
        "(notes of $1,000,000 + $226,378.12) and against the sworn 255 "
        "affidavit at p038 ($39,229,334) - read it as the new facility"),
 C("c2007-deed-bare", "2007062101109001", "p002", "unresolved",
   text="the $42,700,000 deed has NO 'subject to' clause, NO Schedule B of "
        "permitted exceptions, and NO reference to tenancies, liens or the "
        "mortgage. It is a bare Bargain and Sale Deed with Covenant Against "
        "Grantor's Acts carrying exactly two covenants: the grantor's-acts "
        "covenant and the Lien Law 13 trust-fund covenant",
   eff="2007-06-20", ans=["TITLE"],
   note="AND IT SAYS NOTHING ABOUT DEVELOPMENT RIGHTS, AIR RIGHTS, FAR OR "
        "ZONING LOTS - unusual for a through-block Chelsea assemblage parcel, "
        "and worth knowing before anyone represents that the record discloses "
        "encumbrances. The only 'together with' language is the standard "
        "streets-to-centerline clause"),
 C("c2007-throughblock", "2007062101109001", "p002", "unresolved",
   text="the deed's own legal description says the parcel is 'known as and by "
        "the street numbers 112-118 West 25th Street AND 113-117 West 24th "
        "Street' - a through-block parcel, though ACRIS indexes it only under "
        "the 25th Street address",
   eff="2007-06-20", ans=["PARCEL", "ENVELOPE"],
   note="the 24th Street half is what becomes lot 50 in the 2019 subdivision. "
        "An address-keyed search on 113-117 West 24th Street never finds this "
        "deed - one more reason the BBL, not the address, is the spine"),
 C("c2007-anglo-balance", "2007062101109003", "p004", "outstanding_balance",
   num=918_046.14, unit="USD",
   text="Anglo Irish Bank paid $918,046.14 for the assignment of the two "
        "consolidated 1990s mortgages, and the instrument states that is "
        "exactly 'the principal amount now due and owing'",
   eff="2007-06-20", ans=["CAPITAL"],
   note="consideration EQUALS outstanding balance - the purest form of the "
        "acquire-the-paper move. $1,000,000 (1990 Apple Bank) + $226,378.12 "
        "(1998 Queens County) had amortised to this"),
 C("c2007-gaptax", "2007062101109004", "p001", "mortgage_tax",
   num=1_072_716.41, unit="USD",
   text="$1,072,716.41 of mortgage recording tax paid on the $38,311,287.86 "
        "gap - fully taxable, no exemption claimed",
   eff="2007-06-29", ans=["CAPITAL"],
   note="1-CENT DISCREPANCY, both on-face: the cover page reads "
        "$1,072,716.41; the CEMA's own Schedule C at doc ...005 p036 reports "
        "the same payment as $1,072,716.40"),
 C("c2007-loanagt-governs", "2007062101109005", "p026", "unresolved",
   text="section 5.23: 'In the event of any inconsistency between the terms "
        "of the Mortgage and the terms of the Loan Agreement, the terms of "
        "the Loan Agreement shall govern' - and the Loan Agreement is "
        "UNRECORDED",
   eff="2007-06-20", ans=["CAPITAL"],
   note="THE RECORDED INSTRUMENTS ARE DELIBERATELY HOLLOW. The interest rate "
        "is not in the record (5.17 says only that it is variable, 'as more "
        "particularly set forth in the Loan Agreement'). 'Event of Default' "
        "is used throughout all four recorded loan documents and DEFINED IN "
        "NONE of them. Acceleration triggers, alteration and demolition "
        "consent, and lease-modification bars are all ABSENT from the record. "
        "This is the 2007 ancestor of the same off-register structure "
        "MetLife uses in 2023 and Deutsche Bank in 2025"),
 C("c2007-groundlease-lock", "2007062101109005", "p026", "unresolved",
   text="the borrower 'will not subordinate or consent to the subordination "
        "of the Ground Lease' - an absolute bar - and must exercise every "
        "renewal option on the lender's demand, with the lender appointed "
        "irrevocable attorney-in-fact to do it if the borrower will not",
   eff="2007-06-20", ans=["ENCUMBRANCE", "TENANCY"],
   note="a power of attorney 'coupled with an interest' over the leasehold "
        "estate. The lender may also enter the Leasehold Parcel to cure "
        "ground-lease defaults, repayable in 5 days at the Default Rate"),
 C("c2007-exhibit-mislabel", "2007062101109004", "p007", "defect",
   text="section 1.1 defines 'Ground Lease' as 'those certain documents "
        "listed in Schedule A-3 attached hereto', but the document actually "
        "annexed is captioned 'EXHIBIT A-2 / Ground Lease' at p015. There is "
        "no Schedule A-3",
   eff="2007-06-20", ans=["IDENTIFY"],
   note="the exhibit that resolves the $2,300,000 question is the one the "
        "definition points at by the wrong name"),
'''


def main():
    p = pathlib.Path("claims.py")
    t = p.read_text(encoding="utf-8")
    m = re.search(r"^ # ---- 201\d.*$", t, re.M)
    assert m, "no 201x section header found"
    anchor = m.group(0)
    t = t.replace(anchor, NEW + anchor, 1)
    p.write_text(t, encoding="utf-8")
    print("recorded 11 claims from the 2007 batch; anchored above:", anchor.strip())


main()
