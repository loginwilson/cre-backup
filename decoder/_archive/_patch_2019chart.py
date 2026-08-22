"""⚠ THE LAST THREE CLAIMS FROM THE FAILED PATCH — found by the new guard.

_patch_zlda.py died on a heredoc error and lost EIGHT claims. I recovered
five when a supersession edge pointed at one of them. The other three sat
lost until patchlib.audit() compared every patch script's stated output
against the ledger — which took one run and no judgment.

⚠ THAT IS THE DIFFERENCE BETWEEN CATCHING A BUG AND CLOSING ITS CLASS. The
edge check found one instance by luck. The audit finds all of them, always,
and would have flagged this before it was ever reported as done.
"""
import patchlib

NEW = '''
 C("c2019-chart", "2019071700601003", "p044", "envelope_balance",
   num=390_160, unit="sf",
   text="the 2019 Development Rights Chart, Exhibit D row 6 'Allocation of "
        "Development Rights After Transfer (sf)': Lot 49 Land 141,929 · Lot "
        "50 Land 127,035 · TOTAL across all nine combined-lot parcels 390,160",
   eff="2019-05-20", ans=["ENVELOPE"],
   note="⚠ THE NINE-LOT TOTAL IS 390,160 sf, NOT 268,964. My chain closed "
        "141,929 + 127,035 = 268,964 and that is the LOT 49 + LOT 50 SHARE; "
        "the other seven lots retain 121,196 sf between them. A separate row "
        "5 gives 'Lot 49/50 Excess Development Rights' of 56,659 (lot 49) and "
        "55,915 (lot 50) — excess-only, a different scope, not a conflict"),
 C("c2019-upzoning", "2019071700601003", "p015", "easement",
   text="upzoning and downzoning reallocate by formula: on an Upzoning 'Lot "
        "50 Owner shall be entitled to 45.48% of the Development Rights "
        "resulting from such Upzoning ... and Lot 49 Owner shall be entitled "
        "to 54.52%'. The trigger is 'a validly enacted amendment of the "
        "Zoning Resolution', or a casualty following a Downzoning",
   eff="2019-05-20", ans=["ENVELOPE"],
   note="⚠ A VARIABLE ENVELOPE. Any future rezoning of this block splits "
        "45.48/54.52 automatically. Section III otherwise bars cross-draw: "
        "each owner 'shall retain all rights in and to' its own rights, so "
        "neither lot may borrow from the other in normal operation"),
 C("c2019-nonarms", "2019071700601003", "p001", "defect",
   text="the 2019 subdivision paid ZERO transfer tax — NYC RPTT $0.00 and NYS "
        "RETT $0.00 — because grantor LAM GEN 25 LLC and grantee LG CHELSEA "
        "LLC are both 'c/o Lam Generation LLC' and Jeffrey Lam signed for "
        "BOTH as Authorized Signatory",
   eff="2019-05-20", ans=["VALUE", "TITLE"],
   note="⚠ COMMONLY-CONTROLLED ALLOCATION, NOT A SALE. So no price can be "
        "derived here — the stamp arithmetic that works on every arm's-length "
        "transfer in this corpus returns nothing, and that is the correct "
        "answer rather than a failure. ⚠ Only ONE of the two acknowledgment "
        "blocks on p025 was notarised"),
'''

patchlib.apply(NEW)
