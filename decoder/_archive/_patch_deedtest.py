"""THE DEED AGENT'S FIRST RUN — two documents, one new fact, one retraction.

⚠ AND THE RETRACTION IS THE BIG ONE. I told the user, in the scope file and
in conversation, that NO DEED into Chelsea 25 Hotel LLC exists and that the
fee moved by an "Owner Agreement dated October 16, 2023". THE DEED EXISTS.
It is 2023110100486001, eight pages, indexed at $0, sitting in the same
batch three agents read around and none opened.

⚠ HOW IT SURVIVED: the batch agents were handed a hand-built list of
document ids. 486001 was not on it. Every one correctly reported on what it
was given. THE WORK LIST WAS THE DEFECT, AGAIN — the same failure as the
five "missing" instruments, one layer along.
"""
import patchlib

NEW = '''
 C("c2013-lam-purchase", "2013080901116003", "p001", "consideration",
   num=67_500_000, unit="USD",
   text="LAM GEN 25 LLC BOUGHT THE PARCEL FOR $67,500,000 on 2013-08-07. "
        "Cover tax block: 'NYC Real Property Transfer Tax: $1,771,875.00' "
        "and 'NYS Real Estate Transfer Tax: $270,000.00'. $1,771,875 / "
        "2.625% = $67,500,000 and $270,000 / 0.400% = $67,500,000",
   eff="2013-08-07", stated="2013-08-27", ev="derived",
   parties=["112-118 WEST 25TH LLC (grantor)", "LAM GEN 25 LLC (grantee)"],
   ans=["VALUE", "TITLE"],
   note="⚠ THE ACQUISITION PRICE I NEVER HAD. I recorded the 2007 purchase "
        "at $42,700,000 and the 2023 recapitalisation at $120,000,000 and "
        "never knew what Lam paid. TWO WITNESSES AGREE EXACTLY and the ACRIS "
        "index carries the same figure. ⚠ THE DOCUMENT WAS NEVER READ BY ANY "
        "AGENT — it was not on the hand-built work list. $67.5M in 2013 "
        "against $42.7M in 2007 is the assemblage premium: six years and "
        "seven air-rights purchases later"),
 C("c2023-chelsea-DEED", "2023110100486001", "p001", "conveyance",
   text="⚠ THE DEED INTO CHELSEA 25 HOTEL LLC EXISTS. Cover page: "
        "'GRANTOR/SELLER: LAM GEN 25 LLC' and 'GRANTEE/BUYER: CHELSEA 25 "
        "HOTEL LLC', MANHATTAN 800 49 Entire Lot, recorded 11-06-2023 10:10, "
        "CRFN 2023000287573",
   eff="2023-10-16", stated="2023-11-06",
   parties=["LAM GEN 25 LLC (grantor)", "CHELSEA 25 HOTEL LLC (grantee)"],
   ans=["TITLE"],
   note="⚠ RETRACTS MY CONCLUSION THAT NO DEED EXISTS. I told the user the "
        "fee moved by an 'Owner Agreement dated October 16, 2023' because a "
        "franchise memorandum recited that phrase and no deed had been "
        "found. The deed was in the index the whole time, eight pages, in "
        "the same batch three agents read around. ⚠ NONE OF THEM WAS GIVEN "
        "486001 — the hand-built work list was the defect, exactly as it was "
        "for the five 'missing' instruments. The Owner Agreement is real and "
        "is a SEPARATE instrument; it did not replace the deed"),
 C("c2023-chelsea-zero", "2023110100486001", "p001", "tax_paid",
   num=0.0, unit="USD",
   text="the deed into Chelsea 25 Hotel LLC paid ZERO transfer tax — 'NYC "
        "Real Property Transfer Tax: $0.00' and 'NYS Real Estate Transfer "
        "Tax: $0.00' — with only a $250.00 filing fee and $52.00 recording "
        "fee",
   eff="2023-11-06", ans=["VALUE", "TITLE"],
   note="⚠ A $0/$0 STAMP PAIR IS A POSITIVE FINDING, NOT A MISSING PRICE. It "
        "identifies a commonly-controlled transfer — LG 25 Hotel DE LLC is "
        "the managing member of BOTH Lam Gen 25 and Chelsea 25 Hotel, and "
        "Jeffrey Lam signs for both. So the propco/opco split was an "
        "internal reorganisation ahead of the MetLife financing, not a sale, "
        "and NO PRICE EXISTS TO FIND. Saying so is the answer"),
'''

patchlib.apply(NEW)
