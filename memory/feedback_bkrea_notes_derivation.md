---
name: feedback_bkrea_notes_derivation
description: "Card rule — no standalone Contacts/Notes section; a contact's derivation folds under that contact, a note sits at the foot of the section it comments on"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: b81cdba8-aef2-4c37-a0d9-9daa59a3b947
  modified: 2026-08-03T02:56:06.292Z
---

Settled 2026-08-02. The card has **no Contacts & Notes section** and must not grow one back.
Broker knowledge renders **beside the fact it qualifies**:

- **How a contact was derived** → a `Derivation` fold-out ON that contact (architect, filing rep,
  developer, contractor, buyer, seller, lender; owner later). With no explanation to give it
  collapses to the plain citation line — most contacts need nothing.
- **What the record gets wrong about the trade** → `SectionNotes` at the foot of the sale event in
  Comparables, under the parties (`data.notes`).
- **Anything else** → `SectionNotes` at the foot of its own section (`data.sectionNotes[key]`).

The contact EDITOR (add-a-person, registry picker) is withdrawn, not deleted — "later on we will
have a database for this, but not yet." Until then the broker layer is written by populate scripts
against the reach ladder, never typed lot by lot.

**Why:** a single per-lot prose box made the reader join two blocks by eye, and provenance belongs
to the party it explains, not to the parcel.

**How to apply:** any new card section gets a notes footer; any new contact block gets a
`Derivation` with its exact document. Green (`bkrea-lime`) accents, never purple — purple is the
comparables widget palette. See [[project_bkrea_reach_ladder_roles]] and
[[feedback_bkrea_dev_card_grammar]].
