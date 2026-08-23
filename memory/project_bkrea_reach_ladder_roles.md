---
name: project_bkrea_reach_ladder_roles
description: "The reach ladder is per-ROLE — each role signs a different instrument; the seller's rung 2 is their OWN prior mortgage, and the lender has none"
metadata: 
  node_type: memory
  type: project
  originSessionId: b81cdba8-aef2-4c37-a0d9-9daa59a3b947
  modified: 2026-08-03T02:56:19.661Z
---

Settled 2026-08-02, `lib/reachLadder.ts` + `scripts/reachWalk.ts`. Getting from an ACRIS ENTITY to a
person generalizes past the buyer, **but each role signs a different piece of paper**:

- **buyer** — rung 2 is the acquisition mortgage recorded WITH the deed.
- **seller** — rung 2 is **their own prior acquisition mortgage**: walk the lot back to the deed
  where they were grantee. ⚠ The seller does NOT sign the mortgage recorded with the sale; the buyer
  does. Aiming rung 2 at `deed.mtgDoc` for a seller returns the buyer's signatory wearing the
  seller's label.
- **lender** — **no rung 2 exists.** A mortgage is executed by the borrower alone; a lender officer
  signs only a satisfaction or assignment. Rung 1 is the notice address, already structured in ACRIS.

Two guards before any fetch: **MERS is a nominee, not a lender** (916 loans / 232 spellings / 15.7%
of lender slots — the card flags it in amber), and **a natural person needs no rung** (ACRIS writes
people as `SURNAME, FIRSTNAME`; 31.7% of buyers, 49.2% of sellers).

Reach: ~58% of buyer and ~61% of seller slots resolve to a named human inside ACRIS, vs **0.3%** for
name-matching deed parties to PW1 parties.

**Why:** every measured rule change here deleted a person who does not exist. The extractor is
versioned (`REV`) and old reads are RE-READ, never inherited — REV 2 killed "MIN WU LIN", REV 3 four
more, REV 4 two more. All were name-shaped, so they pass every downstream check and earn a
deterministic partyId.

**How to apply:** never point a role at another role's instrument; bump `REV` on any gate change;
state coverage as a measured number, not an impression. See [[feedback_bkrea_notes_derivation]] and
[[project_bkrea_debt_throughline]].
