# Profiling a person — the enrichment layer, and why it is SEPARATE

The goal (Login, 2026-08-05): parcel → document → role → entity → name → real
company → real role → phone, email, mailing → **a profile of who this person is**.

The chain up to "mailing" is *decoded* — every link cites a page. A profile is
*enriched* — it comes from outside the record. Those are different kinds of
claim and they must not share a table.

## The rule

**A decoded fact cites a document. An enriched fact cites a source and a match.**

Enrichment therefore carries two things a decode never needs:

```jsonc
{
  "claim": "Vice-Chairman, First Jamaica Community and Urban Development Corp",
  "source": "NYS DOS entity filing, DOS ID …, filed 2019-03-11",
  "match_keys": ["entity_name", "address", "title", "date_range"],
  "match_confidence": "strong | plausible | weak",
  "matched_to": "party_observation <document_id>#<page>"
}
```

Without `match_confidence` the layer is worse than useless: it attaches a real
person to a deal they may have nothing to do with, and nothing downstream can
tell that claim from a decoded one.

## Matching is where this goes wrong

A name is not a key. "John Smith" on a deed and "John Smith" on a company page
are not the same person, and asserting they are is the **false-merge** error the
entity resolver already refuses to make — except worse, because here it attaches
a living individual's identity to somebody else's transaction.

Require **at least two independent corroborating keys** before `strong`:

- entity name matches an entity the person is filed against
- address matches a notice address, party-index address, or DOS service address
- title matches a signature block or jurat
- the date falls inside the period the person held that role

One key alone is `weak`, and `weak` never propagates into a contact record.

## Source order — authoritative first, self-reported last

1. **NYS DOS corporate filings** — officers and address for service. The rung
   that turns an SPE into people. Authoritative, free.
2. **SEC EDGAR Form D** — real-estate syndications file these constantly and the
   form NAMES executive officers and promoters with addresses. Structured, free,
   and almost nobody in brokerage reads it.
3. **Licence registers** (DOB, DOS, NYS Education Dept for architects/engineers)
   — a licence number is a verified individual, and certifications already give
   us those (e.g. architect 037995-1).
4. **NYC Campaign Finance Board · City Clerk lobbyist registry** — principals,
   their firms, and who they retain on entitlements.
5. **NY e-courts** — litigation involving the entity.
6. **Company sites, press releases, award and subsidy announcements** — public,
   fetchable, self-reported.

## What this project will not do

- **No LinkedIn scraping.** Its terms prohibit it and it enforces actively. A
  source that fights the collector breaks silently, and a silent break cannot be
  told apart from a real absence — the precise failure this decoder is built to
  prevent. The same standing rule already applies to ACRIS images ("do not build
  a bulk image scraper and do not work around bot detection") and to Crexi.
- **No profiling beyond business capacity.** Who acted, in what role, on which
  deal, for which entity. That is what the public record holds, it is what a
  title company or broker assembles by hand today, and it is the part where every
  claim can cite its source. Personal life is neither needed nor defensible.

## Ordering

Enrichment is worth building when the contact chain beneath it is reliable — i.e.
when `notices[]`, `acknowledgments[]`, `certifications[]` and `signature_blocks[]`
are populated across types and `resolve_signatories()` is returning `resolved`
rather than `no printed instance yet`. Built earlier, it enriches names that are
still uncertain, and a profile hung on a misread signature is worse than no
profile at all.
