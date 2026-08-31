# RC_1598772 — event table (Extractor E) — schema v2

Deed with a developer's restrictive covenant scheme. Richmond County, 2 pages.
Class spec read first: `specs/DEED-RESTRICTIVE-COVENANT.md`. Reading carried over from
my sealed v3 table; re-emitted into the v2 schema. Rects measured against the page
images and verified by re-cropping.

instrument: 1911-04-14
acknowledged: 1911-04-18
recorded: 1911-04-25
expires: 1915-01-01

**rd** (`registration.json`) supplies the BBLs: `5004030016`, `5004030017`. I did not
compose them. rd's `parties[]` is empty and `amount` is `$0.00`.

**Prior finding carried forward, still load-bearing:** the marks on "Sixteen" and
"Seventeen" are lead-in flourishes, not cancellations — two separate strokes each dying
inside its own capital `S`, neither crossing a word gap; the identical stroke sits on
"eleven", "her" ×3 and "Heberton Avenue" ×2, which cannot be cancelled; and this
document's three real cancellations are continuous ruled lines spanning whole phrases.
Rect on E3 so the claim is falsifiable.

## Event table

| # | citation | date | basis | until | function | mode | bbls | parties | quantity | terms | summary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| E1 | p1 · [0.150,0.1180,0.920,0.1470] · plain · "WOOD HARMON RICHMOND REALTY COMPANY, a corporation duly organized and existing under and by virtue of the Laws of the State of New York" | 1911-04-14 | instrument | | IDENTITY | ASSERT | INSTRUMENT | asserted by: Wood Harmon Richmond Realty Company  about: itself | 1 entity | rd `parties[]` is empty, so this recital is the only evidence of the grantor anywhere in the package. Distinct on the page from *Wood Harmon & Co.*, the firm the plat was surveyed for and the return-to party at R2 | The grantor states it is a New York corporation |
| E2 | p1 · [0.190,0.2250,0.920,0.2450] · plain · "in consideration of the sum of One Dollar, lawful money of the United States and other valuable considerations" | 1911-04-14 | instrument | | VALUE | ASSERT | 5004030016, 5004030017 | Minnie A. Sweeney → Wood Harmon Richmond Realty Company | $1.00 USD recited + UNKNOWN(the deed states "other valuable considerations" with no amount) | rd `amount` reads `$0.00`; the deed reads one dollar. Both stand, neither corrected | One dollar and unstated other value were paid |
| E3 | p1 · [0.170,0.2830,0.920,0.2970] · flourish · "known and designated as lot s No. Sixteen and Seventeen (16, 17)" — the two strokes are lead-in entries into each capital S, not cancellations; also p1 · [0.150,0.2450,0.920,0.2690] · plain · "does hereby grant and release unto the said party of the second part, her heirs and assigns forever, all its right, title and interest" | 1911-04-14 | instrument | | TITLE | TRANSFER | 5004030016, 5004030017 | Wood Harmon Richmond Realty Company → Minnie A. Sweeney | 2 lots | Document's own designation: **lots 16 and 17 in Block 403**, Borough and County of Richmond — rd's BBLs agree. Grantee recited as "MINNIE A. SWEENEY, residing at No. 409 Third Street, Borough of Brooklyn, City and State of New York". Bargain-and-sale form ("all **its** right, title and interest"), not a warranty; fee to "heirs and assigns forever". Appurtenances pass with it, p1 [0.150,0.5950,0.920,0.6100] "Together with the appurtenances and all the estate and rights of the party of the first part". Courses at p1 [0.150,0.3700,0.920,0.5200] give 40 ft × 100 ft, tied 214.28 ft north of Caswell Avenue, "be said measurements and area more or less"; the parcel lies between lot 15 and lot 18, which corroborates the flourish reading independently of the ink. Habendum unqualified because E5 is struck | The company conveys whatever interest it has in lots 16 and 17 to Minnie A. Sweeney and her heirs forever |
| E4 | p1 · [0.150,0.3050,0.920,0.3500] · plain · "on a certain plan of lots called South New York, Addition Number Four, surveyed for Wood Harmon & Co., 1906, by Lewis T. Haney, Civil Engineer and City Surveyor, and filed or intended to be filed in the Clerk's Office of Richmond County aforesaid, July, 5, 1907, as map no. 995 B" | 1911-04-14 | instrument | | IDENTITY | ASSERT | 5004030016, 5004030017 | asserted by: Wood Harmon Richmond Realty Company  about: the parcel | map no. 995 B; survey 1906; map date 1907-07-05 | **The map date is a fourth kind of date and `basis` has no term for it** — I dated the row to the deed's own assertion, not to the map. The deed says "filed **or intended to be filed**", so it never confirms the filing happened. Not in rd. Without this map "lot 16, block 403" is not a location | The lots are identified by reference to a 1906 Haney survey on map 995 B, dated 5 July 1907 |
| E5 | p1 · [0.150,0.6280,0.920,0.6560] · struck · "subject, however, to all assessments that have become a lien since the ___ day of ___ 19___" | 1911-04-14 | instrument | | ENCUMBRANCE | STRUCK | 5004030016, 5004030017 | Wood Harmon Richmond Realty Company → Minnie A. Sweeney | 0 assessment qualifications | One continuous ruled line spanning the phrase and crossing word gaps, running on to the "day", "of" and "19" blanks — the same morphology as the two setback cancellations, and unlike the flourishes on E3. The habendum therefore passes unqualified as to assessments. **Not** an assertion that no assessments exist. Card 3 defines STRUCK as removal *before execution*; card 1 says stroke order is unrecoverable — I can support the removal, not its timing | The printed "subject to assessments" qualification was ruled out of the habendum |
| E6 | p1 · [0.150,0.6880,0.920,0.7150] · plain · "the said part y of the second part, for herself, her heirs, executors, administrators and assigns, do th hereby covenant and agree to and with the said party of the first part, its successors and assigns" | 1911-04-14 | instrument | 1915-01-01 | ENCUMBRANCE | CREATE | 5004030016, 5004030017 | Minnie A. Sweeney → Wood Harmon Richmond Realty Company | 1 covenant scheme | The clause that makes the burden run to successors on both sides; E7–E14 are its content. Expiry for this row and every covenant row below is p2 [0.150,0.4380,0.950,0.4650] "All restrictions and covenants in this instrument contained shall continue in force until the first day of January, 1915, and no longer." "party" and "doth" are handwritten completions of printed blanks | The grantee binds herself and her successors to a covenant scheme in favour of the company |
| E7 | p1 · [0.150,0.7280,0.920,0.7530] · plain · "any building except a detached or semi-detached dwelling house"; also p1 · [0.150,0.7980,0.920,0.8180] · plain · "such building shall not be less than two stories in height, shall have a cellar, shall not have what is commonly known as a flat roof" | 1911-04-14 | instrument | 1915-01-01 | ENVELOPE | CREATE | 5004030016, 5004030017 | Minnie A. Sweeney → Wood Harmon Richmond Realty Company | min 2 storeys; 1 cellar; 0 flat roofs | One duty — what kind of building may stand here — carried by two adjacent clauses of the same covenant. The word "dwelling" also bears on OCCUPANCY; the use limb is E8 | The house must be detached or semi-detached, at least two storeys, cellared, and not flat-roofed |
| E8 | p1 · [0.150,0.7460,0.920,0.7570] · plain · "no such dwelling house shall be built for use and occupancy of more than two families except as hereinafter provided" | 1911-04-14 | instrument | 1915-01-01 | OCCUPANCY | CREATE | 5004030016, 5004030017 | Minnie A. Sweeney → Wood Harmon Richmond Realty Company | max 2 families | "except as hereinafter provided" points forward to the grantor's reserved right at E15 | No more than two families may occupy the house |
| E9 | p1 · [0.150,0.7530,0.920,0.7960] · plain · "shall cost not less than Two Thousand ($2000.) dollars if built for use and occupancy of one family only; or if built as a double house, for use and occupancy of two families, or as a double tenement, it shall cost not less than Three Thousand ($3,000.) dollars" | 1911-04-14 | instrument | 1915-01-01 | COST | CREATE | 5004030016, 5004030017 | Minnie A. Sweeney → Wood Harmon Richmond Realty Company | $2,000.00 USD min (one family); $3,000.00 USD min (two families) | One duty to spend, varying by occupancy — one row per card 2. Alternatives, never additive. Both amounts handwritten in words and figures, agreeing. Filed under COST per the framework's own COST-vs-VALUE boundary, which names this exact clause; the worked row in `framework.md` files the same clause under ENVELOPE | A house here must cost at least $2,000, or $3,000 if built for two families |
| E10 | p1 · [0.150,0.8180,0.920,0.8560] · struck · "within fifteen (15) feet of the line of Heberton Avenue , nor within (___) feet of the line of ___"; also p2 · [0.150,0.0450,0.950,0.0800] · struck · "must stand at least sixty feet from Heberton Avenue and at least (___) feet from" | 1911-04-14 | instrument | 1915-01-01 | ENVELOPE | CREATE | 5004030016, 5004030017 | Minnie A. Sweeney → Wood Harmon Richmond Realty Company | 15 ft house setback; 60 ft accessory setback | One duty — how far back a structure must stand — varying by structure type, so one row. Steps, piazzas, bay and oriel windows and other usual projections are excepted from the 15 ft line. Only a barn, stable or garage appurtenant to a private residence may stand at all. In **both** clauses the second street blank is ruled out and was never filled, so only Heberton Avenue is regulated; "Heberton Avenue" itself is a flourished fill-in, not a cancellation | Nothing may stand within 15 feet of Heberton Avenue, and no barn or garage within 60 feet |
| E11 | p2 · [0.150,0.0750,0.950,0.1100] · plain · "nor shall more than one such dwelling house and one such stable or garage be erected or permitted on each parcel of land Twenty feet in width by One Hundred feet in depth" | 1911-04-14 | instrument | 1915-01-01 | ENVELOPE | CREATE | 5004030016, 5004030017 | Minnie A. Sweeney → Wood Harmon Richmond Realty Company | 1 dwelling + 1 stable/garage per 20 ft × 100 ft | Density cap expressed per plat lot unit; "Twenty" and "One Hundred" are handwritten. The conveyed premises are two such units, so on its face this permits two dwellings across lots 16 and 17 | At most one house and one stable or garage per 20-by-100-foot lot |
| E12 | p2 · [0.150,0.1300,0.950,0.1650] · plain · "nor shall any fence be built, constructed or maintained on any part of said premises unless the nature, kind, shape and material be first made known and shown to one of the officers of the said WOOD HARMON RICHMOND REALTY COMPANY, and have received his sanction and approval in writing" | 1911-04-14 | instrument | 1915-01-01 | ENVELOPE | CREATE | 5004030016, 5004030017 | Minnie A. Sweeney → Wood Harmon Richmond Realty Company | 0 fences without written approval | **A private discretionary approval right, which has no home in the eleven.** PERMIT is government-only; ENVELOPE holds the constraint and loses the veto holder — an officer of the grantor, with no successor mechanism stated and no standard for withholding. Filing it here loses *who decides* | No fence without the company's written approval of its nature, kind, shape and material |
| E13 | p2 · [0.150,0.1600,0.950,0.2520] · plain · "nor shall there be erected or maintained upon said premises or any part thereof any milkman's stable, livery stable, carpenter shop, piggery, slaughter house ... nor any hospital, and that s he will not use or permit to be used the said premises or any part thereof for the use or carrying on of any trade or business" | 1911-04-14 | instrument | 1915-01-01 | OCCUPANCY | CREATE | 5004030016, 5004030017 | Minnie A. Sweeney → Wood Harmon Richmond Realty Company | ~24 enumerated uses + 1 general ban | One prohibition, listed then generalised in the same sentence — one row per card 2. The list also names smith shop, forge, furnace, steam engine, brass foundry, tin/nail/iron factory, manufactories for gunpowder, glue, varnish, vitriol, ink or turpentine, bone boiling, dressing/tanning/preparing skins hides or leather, brewery, distillery, oil or lampblack factory, "any noxious or dangerous trade or business", and fire-engine, truck or hose-carriage storage. The "s" of "she" is a handwritten insertion in a printed blank | No noxious trade, factory or hospital, and no trade or business of any kind, on the premises |
| E14 | p2 · [0.150,0.2900,0.950,0.3200] · plain · "will sell or suffer or allow to be sold on the premises hereby conveyed, or any part thereof, any strong or spirituous liquors, or ale, beer or wine, or intoxicating liquors of any kind" | 1911-04-14 | instrument | 1915-01-01 | OCCUPANCY | CREATE | 5004030016, 5004030017 | Minnie A. Sweeney, her heirs, executors, administrators and assigns → Wood Harmon Richmond Realty Company | 0 liquor sales | Kept separate from E13 because it is a separately introduced covenant — "do th hereby **further** covenant" — with its own recital of bound parties, and it reaches sale rather than use | No liquor of any kind may be sold on the premises |
| E15 | p2 · [0.150,0.3150,0.950,0.4050] · plain · "The party of the first part, however, shall have the right to erect or maintain or to permit to be erected or maintained on any part of South New York, Addition Number Four, buildings in blocks for the use and occupancy of one or more families, or detached or semi-detached buildings for the use and occupancy of more than two families" | 1911-04-14 | instrument | | ENTITLEMENT | CREATE | SET: all lots in plat 995 B (South New York, Addition Number Four) | Minnie A. Sweeney → Wood Harmon Richmond Realty Company | UNKNOWN(the deed does not state how many lots Addition No. 4 contains) | The grantor exempts its own retained land from the scheme it is imposing, subject only to its own approval of materials and of plans and specifications — a second private approval right (see E12). This is the "except as hereinafter provided" of E8. `until` left blank: the expiry sentence sweeps "restrictions and covenants", and a reserved right is neither. As written the set includes lots 16 and 17, which sits oddly beside E7–E8; the page does not resolve it | The company reserves the right to build multi-family and row buildings anywhere in the plat |
| E16 | p2 · [0.150,0.4000,0.950,0.4350] · plain · "the party of the first part shall also have the right to use and to grant the right to use for all purposes other than those business purposes specifically mentioned above, all of the lots on Richmond Turnpike, Merrill Avenue and Watchogue Road and the lots on Wyona Avenue between Willow Brook and Hawthorne Avenue" | 1911-04-14 | instrument | | ENTITLEMENT | CREATE | SET: lots fronting Richmond Turnpike, Merrill Avenue or Watchogue Road, plus lots on Wyona Avenue between Willow Brook and Hawthorne Avenue | Minnie A. Sweeney → Wood Harmon Richmond Realty Company | 4 named frontages; lot count UNKNOWN(none enumerated) | A commercial carve-out. **The deed never says these streets lie in plat 995 B**, so I could not narrow the criterion to that plat without guessing; as written it is evaluable only against a map showing those streets, which is not in this package | Lots on four named streets are released for uses other than the listed businesses |
| E17 | p2 · [0.150,0.4670,0.950,0.5100] · plain · "the party of the first part has not done or suffered anything whereby the said premises have been encumbered in any way whatever excepting as to said restrictions and limitations" | 1911-04-14 | instrument | 1915-01-01 | ENCUMBRANCE | ASSERT | 5004030016, 5004030017 | asserted by: Wood Harmon Richmond Realty Company  about: the premises | 0 encumbrances of the grantor's own making | A covenant against grantor's acts — a genuine asserted absence, and narrow: it speaks only to what **this** grantor did, not to earlier owners, taxes or assessments. `until` is the literal reading of "All restrictions and **covenants** in this instrument contained", which reaches this covenant too; whether the sweep was meant to end a covenant of title is not settled by the page | The company warrants it has itself encumbered the premises with nothing but these restrictions |
| E18 | p2 · [0.150,0.5150,0.950,0.6550] · plain · "has caused its corporate name to be hereunto subscribed by its Vice-President and by its Secretary and its corporate seal to be hereunto affixed, attested by its Secretary, the day and year first above written" — signed "By Leonidas Keever, Vice-President" and "Attest: John H. Storer, Secretary" | 1911-04-14 | execution | | IDENTITY | ASSERT | INSTRUMENT | Leonidas Keever and John H. Storer → Wood Harmon Richmond Realty Company | 2 signatories | Capacity in which each signs. Dated by the instrument's own words, "the day and year first above written" — this is why `execution` and `instrument` are the same date here and I did not have to choose. At the seal position the image shows only the handwritten words "(Corp. Seal)"; whether an embossed seal is physically present cannot be told from a bitonal scan, though E19 swears one was affixed | The company signs by Vice-President Leonidas Keever, attested by Secretary John H. Storer |
| E19 | p2 · [0.150,0.6700,0.950,0.8150] · uncertain · "On the 18th day of April ... and eleven before me personally came Leonidas Keever to me known and being by me duly sworn did depose and say, that he resides in the City of New York, Borough of Brooklyn and that he is the Vice-President of WOOD HARMON RICHMOND REALTY COMPANY" | 1911-04-18 | acknowledgment | | IDENTITY | ASSERT | INSTRUMENT | Leonidas Keever → Elizabeth Roth, Commissioner of Deeds | 1 deponent, 1 officer | Mark is `uncertain` because the day figure is overwritten by descenders from the venue lines above. Rendered at matched scale, this writer's "5" (p1 "July, 5, 1907") is a single open bowl under a straight top bar; this glyph is two closed loops joined at a waist, so 18. Only 15 is a candidate I would accept; calendar range 14–25. He further swears he knew the corporate seal, that the seal affixed was that seal, that it was affixed by order of the Board of Directors, and that he signed by like order. Venue is three handwritten lines, none struck: "State of New York, City of New York, County of New York". Three counties are in play — acknowledged in New York, deponent resident in Kings, land in Richmond | Keever swears before Commissioner of Deeds Elizabeth Roth that he is the company's Vice-President and signed by order of the Board |

## Registry lane

Not one of the eleven — these ask about the **instrument**, not a parcel. Numbered `R`
so they are not scored as event rows.

| # | citation | date | basis | until | function | mode | bbls | parties | quantity | terms | summary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R1 | p2 · [0.140,0.8250,0.420,0.8750] · plain · "Recorded April, 25, 1911 at 9 a.m." | 1911-04-25 | recording — **not in the `basis` vocabulary, by design** | | — registry act | ASSERT | INSTRUMENT | Richmond County Register → the record | 1 instrument, recorded 09:00 | The **time** fixes priority against anything else recorded that day. rd `recorded` reads `4/25/1911` and carries no time; the endorsement does | The deed was accepted for record at 9 a.m. on 25 April 1911 |
| R2 | p2 · [0.140,0.8700,0.420,0.9100] · plain · "C. Livingston Bostwick, for Wood, Harmon & Co., Broadway, N.Y. City." | 1911-04-25 | recording | | — return-to | ASSERT | INSTRUMENT | Richmond County Register → C. Livingston Bostwick, for Wood, Harmon & Co. | 1 return-to party | The only appearance of the grantor's agent and address anywhere in the package, and rd has no field for it. Note *Wood, Harmon & Co.* is not the grantor named at E1 | The recorded deed returns to C. Livingston Bostwick for Wood, Harmon & Co. |
| R3 | p2 · [0.450,0.8200,0.950,0.8900] · plain · "Elizabeth Roth, Commissioner of Deeds, In and for New York City" | 1911-04-18 | acknowledgment | | — officer | ASSERT | INSTRUMENT | Elizabeth Roth → the instrument | 1 officer | No commission number and no expiry stated. Book 396, page 1 per rd, matching the hand-numbered leaves and the digitisation overlay | The acknowledging officer is a New York City Commissioner of Deeds |

**Fees and stamps: none found.** No recording fee, tax stamp or revenue stamp appears on
either page, both margins checked at 900 dpi. That is "I found nothing", not "the
document says there is nothing".

## Brief

A New York corporation, Wood Harmon Richmond Realty Company, sold two adjoining building
lots on Staten Island to a Brooklyn woman and, in the same instrument, told her what she
could put on them. Signed 14 April 1911, sworn on the 18th, recorded on the 25th at nine
in the morning.

What moved was lots 16 and 17 in Block 403, Borough of Richmond — rd's BBLs 5004030016
and 5004030017 — a 40-by-100-foot rectangle on the west side of Heberton Avenue, taken
from a 1906 survey the deed points at but never confirms was filed. The grant is a
bargain and sale of "all its right, title and interest", and the only warranty given is
that the company itself has encumbered nothing.

The rest is a suburban design code: detached or semi-detached, two storeys, a cellar, no
flat roof, fifteen feet back from the avenue, sixty feet for a barn or garage, one house
per twenty-foot lot, and a cost floor of $2,000 rising to $3,000 for two families. Two
dozen trades are named and banned, then banned again in general, no liquor may be sold,
and no fence may go up without the company's written approval.

The company exempted itself, keeping the right to build multi-family houses anywhere in
the plat and to release four named streets from the trade restrictions. And the whole
scheme was written to die: every restriction expires 1 January 1915 and no longer.

## What the schema could not express

**S1 — `basis` has no term for a recording, and none for a filed-map date.** R1's date is
a real, cited, load-bearing date (9 a.m. fixes same-day priority) and the vocabulary
excludes `recorded` on purpose. I had to put the registry lane outside the event table
to avoid writing an illegal basis. Separately, E4's map date 1907-07-05 — "filed or
intended to be filed ... July, 5, 1907" — is neither effective, instrument, execution nor
acknowledgment, and it is not `UNSUPPORTED` either, because the document supports it. I
dated E4 to the deed's assertion and put the map date in `terms`, where nothing can sort
on it. The class spec predicts this ("a fourth kind of date"); the schema still has no
slot.

**S2 — numbering the registry lane `R` puts it outside every gate.** `tablecheck` scores
only rows whose id matches `E\d+`, so R1–R3 are skipped by CITE, MARK and FEED entirely.
The lane holds exactly what the spec says hides there — the fee, the time, the return-to
party — and nothing checks it. If I had numbered them `E`, FEED would have counted three
rows as unconsumable for having no function among the eleven, which is true but reads as
a defect in the reading rather than in the schema.

**S3 — the private discretionary approval right still has no home (E12, and again in
E15).** "unless the nature, kind, shape and material be first made known and shown to one
of the officers of the said WOOD HARMON RICHMOND REALTY COMPANY, and have received his
sanction and approval in writing". PERMIT is government-only; ENVELOPE captures *what is
constrained* and drops *who holds the veto*, on what standard, and whether it passes to
successors. The spec already flags this as a candidate function; this document contains
two instances, not one.

**S4 — `bbls` has no value meaning "about a party".** E1 asserts the grantor's corporate
existence. It is not about a parcel, and `UNPLACED` means "the document does not place
it", which reads as a defect that is not there. I used `INSTRUMENT`, whose gloss in
`framework.md` says "registry lane rows" — so I am using it outside its stated scope for
E1, E18 and E19. If that is wrong the alternative flags three sound rows as failures.

**S5 — `until` forces a binary where the page supports two readings (E17).** "All
restrictions and **covenants** in this instrument contained shall continue in force until
the first day of January, 1915, and no longer." Literally that sweeps the grantor's
covenant against its own acts. Purposively it targets the restriction scheme. I wrote
1915-01-01 because that is what I can point at, but `until` cannot say "stated sweep,
contested scope", and Resolve will silently drop a title covenant in 1915 on my say-so.
The same sentence is why E15 and E16 have a blank `until` — a reserved right is neither a
restriction nor a covenant, so nothing states when it ends.

**S6 — one `until`, one citation, many rows.** Eight rows carry `until: 1915-01-01` and
the sentence proving it appears once, on page 2. I put its rect in E6's `terms` and
cross-referenced. Every other machine field on a row is proved by that row's own
citation; `until` is the one that is not.

**S7 — cards 1 and 3 contradict each other on E5.** Card 3 defines `STRUCK` as "the
instrument considered this and removed it **before execution**". Card 1 says stroke order
is unrecoverable, so struck-before-execution is permanently uncertain. Using the mode
therefore asserts something the framework elsewhere says can never be supported. I used
it, because the alternatives misstate the world worse, and said so in `terms`.

**S8 — the framework's own worked row disagrees with its function table, on this
document's clause.** The table lists *"shall cost not less than $2,000"* under **COST**;
the worked row in `framework.md` files the same clause under **ENVELOPE**, on page 2 (it
is on page 1), quoting text that is not on the page, with `bbls: SET: all lots in plat
995 B` (the cost floor binds only the herein-described premises) and parties running
company → grantees (the covenant runs grantee → company). I followed the function table
and put E9 under COST. Card 11 says the page wins; recording it so the discrepancy is not
mistaken for my error.

**S9 — two names in the spec are not on the page.** `specs/DEED-RESTRICTIVE-COVENANT.md`
§1 calls the grantor *"The Wood, Harmon Company"*. The page names three distinct things:
**WOOD HARMON RICHMOND REALTY COMPANY** (the grantor, E1), **Wood Harmon & Co.** (whom
the plat was surveyed for, and the return-to party, R2), and no "The Wood, Harmon
Company" anywhere. §5 also says "The covenants bind *any part of South New York, Addition
Number Four*" — on the page it is the **grantor's reserved right** that reaches the plat
(E15); the covenants bind "any part of the **herein-described premises**" only. Those two
clauses point in opposite directions and the spec has merged them.

**S10 — where `bbls` needed judgment, not a guess.** E16 is the only row I could not
place cleanly. The framework names this exact set — "lots on four named streets" — as a
row that failed. I named the streets instead of paraphrasing them, which makes the
criterion evaluable in principle; but the deed never says those streets lie in plat
995 B, so I could not narrow it to the plat without inventing the link. No BBL on this
table was composed; every one came from rd.

**Row-count change from my sealed v3 table: 27 → 19 events**, entirely granularity under
card 2, plus one deletion on the merits. Merged: appurtenances into the grant; grantee
identification into the grant's `parties`/`terms`; the two cost floors into one duty; the
15 ft and 60 ft building lines into one duty; the building-form clauses into one duty.
**Dropped: the standalone `AS_BUILT` row for the parcel's 40 × 100 ft geometry.** Under
v3 the isolated-citation rule forced it, because the granting clause does not prove the
courses. Under v2 `bbls` carries placement and `terms` carries context with its own rect,
so the courses sit in E3 where they belong — and the spec's prediction that `AS_BUILT`
does not fire on a vacant platted lot holds. **Dropped: the standalone `TERMINATE` row
for the 1915 expiry** — `until` is the mechanism, and a TERMINATE row would have invented
an act on a date when nothing happened. Those two are the schema working.
