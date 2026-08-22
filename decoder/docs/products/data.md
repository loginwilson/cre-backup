# ACRIS · APPLICATION — THE DATA

## ⚠ THIS PHASE OWNS NO DATA, AND THAT IS THE DESIGN.

Application **reads** derived values from Supabase. It does not compute them, it
does not store its own, and it never reaches back to raw documents.

Like derivation, this phase has been thought through systematically and not
operationally. Nothing technical is written here yet because nothing has been
measured.

## THE ONE RULE THAT MATTERS

⚠ **If the app is computing, the derivation is missing.** Any calculation that
appears in application code is a derivation that was not built — and the moment
a second screen needs the same number, the two will disagree. The fix is always
to push the value back into derivation, never to share a helper function.

This is the practical test for whether the phase boundary is holding, and it is
checkable by reading application code alone.

## WHAT APPLICATION IS FOR

Delivery: the right user experience over values that are already correct. UI and
UX are its whole job. Login, 2026-08-14: *"the data is pre calc in the database
for the app to just worry on ui/ux."*

The decoder is deliberately **not** built app-first — *"instead of building the
app from the start, my philosophy has become to decode the data systems into
practical derivations for application usage."* One decoder, a product suite on
top.

## WHAT IS NOT DECIDED

Everything operational: which products, what they read, how they authenticate,
how freshness is surfaced to a user.

⚠ **One thing must not be deferred, though: freshness has to be visible.** The
claimed edge over existing tools is current-correct-consistent against
lagged-wrong-varying. A product that shows a derived number without showing how
current it is has thrown away the advantage it was built for.

## RELATIONSHIP TO THE EXISTING APP

The BKREA territory app is a **separate project on separate infrastructure**
(Supabase `ghjkjxfxtpqhxxkxbdrp`, versus the decoder's `trljekigamtnxqfoyorm`).
It is not this phase. It may eventually become a consumer of decoder
derivations, but it currently computes its own values from its own sources, and
treating it as the reference implementation would invert the architecture.
