"""LPC Certificate of Appropriateness — the permit that states no number.

WHAT THIS DOCUMENT TURNED OUT TO BE, read end to end on COFA-25-07271

    A BSA resolution states an envelope: 232,985.77 square feet, 4.55 FAR, 310
    units, 122 feet. A Certificate of Appropriateness states NONE OF THAT. Six
    pages on 244 Waverly Place contain no floor area, no FAR, no height, no unit
    count. Every dimension in it is local and incidental — "shifted
    approximately 5' farther east", "an approximately 6'-8" portion".

    ⚠ So a decoder written on the BSA template would report this document as
    empty, and it is not empty. It is a different KIND of statement:

        BSA says  "this parcel may hold 232,985.77 sf"
        LPC says  "this parcel may be CHANGED IN THIS WAY, and not otherwise"

    The CofA regulates form, not quantity. Its value to a parcel ledger is the
    approved WORK — and specifically whether that work is an enlargement:

        "constructing a gray-finished metal-clad, one-story rooftop addition"
        "reducing the footprint ... reconstructing the façade in a new plane"

    That is a development event with a date, a parcel and an owner, and it is
    invisible to ACRIS, invisible to zoning, and only summarised in the feed.

WHAT THE DOCUMENT HAS THAT THE FEED DOES NOT

  * the PUBLIC HEARING and PUBLIC MEETING dates — the feed carries only
    received_date and issue_date, so the actual decision date is document-only
  * the approved-work narrative — the feed compresses it to a `worktypes` code
    list, and 1,664 CofA rows carry the code 'Legacy- Not Available'
  * the Commission's FINDINGS — why it was approvable, which is what predicts
    whether a similar proposal next door will be
  * a DOCUMENT CHAIN: "as you were notified in Status Update Letter 25-04036
    (LPC 25-04036)" — CofAs cite other LPC documents by number
  * the applicant's ENTITY and mailing address (Roundsquare Development LLC),
    where the feed's applicant_name is often an individual architect

⚠ RETRIEVABILITY IS A HARD CUTOFF AT 2016, MEASURED

    https://s-media.nyc.gov/agencies/lpc/Permits/PermitFiles/<regulation_number>.pdf

    Sampled 4 per year, HEAD:

        2012  0/4      2016  3/4      2020  4/4      2024  4/4
        2013  0/4      2017  4/4      2021  4/4      2025  4/4
        2014  0/4      2018  4/4      2022  4/4      2026  4/4
        2015  0/4      2019  4/4      2023  4/4

    So of 10,051 CofAs, roughly 2,870 (2016+) have a retrievable document and
    ~7,180 do not. The pre-2016 ones are not missing from the archive by
    accident — the archive starts there. Reporting CofA coverage without that
    denominator would claim a 28% result as a 100% one.

⚠ ACCESS. s-media.nyc.gov returns 404 on robots.txt — it publishes no policy of
    its own. These are permit documents the LPC links from its public decision
    search, and a 404 is not a refusal, but it is not a permission either. Read
    slowly, one at a time, and stop on the first sign of refusal.
"""
import json, os, pathlib, re, sys, time, urllib.request
from collections import Counter

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import bulk
import facts as F
import fetcher
import runlock
import sink

SOURCE = "LPC"
PERMITS = "dpm2-m9mq"
BASE = "https://s-media.nyc.gov/agencies/lpc/Permits/PermitFiles"
INDEX_COLUMNS = ("regulation_number,regulation_type,issue_date,received_date,"
                 "expiration_date,block,lot,borough,docket,worktypes,"
                 "lmnametype,applicant_name,owner_name")
UA = ("BSA-decoder/1.0 (NYC parcel research, public LPC permits; "
      "contact loginwilson88@gmail.com)")
PACE = 1.5
#   lpc_cofa/1  SUPERSEDED. Fell back to the feed's `worktypes` code as a
#               fact's `verbatim` when the narrative did not extract, and took
#               the historic-district name from the feed. Both are index-sourced
#               values wearing a document citation.
#   lpc_cofa/2  document-sourced only; pages_read/pages_total on every fact.
#   lpc_cofa/3  design-team credentials now match "R.A." as well as "RA" —
#               lpc_cofa/2 returned an empty team on every permit using the
#               period form, which is indistinguishable from a permit naming
#               nobody. Firms captured. "Public Hearing of the same date"
#               resolved and marked as derived.
#   lpc_cofa/4  spot-checked nine deliberately different permits (new building,
#               earliest-archive 2016-17, individual landmark, no-feed-context,
#               legacy worktype). Found: "constructing TWO NEW BUILDINGS on
#               vacant lots" classified as facade_alteration because the pattern
#               required singular "a new building" — the largest development
#               event LPC authorises, read as a facade job. Quantifiers and
#               plurals now allowed. The "narrative present" check was also
#               conflating a retrieval failure with a lexicon gap; split in two,
#               plus a standing check that the parcel came from the permit.
#   lpc/5   the sweep widened from CofA to EVERY permit type, after checking one
#           document of each and finding all six non-CofA types returned a
#           0-character narrative. Five distinct shapes: CofA ("The proposal, as
#           approved, consists of"), CNE/XCNE/PMW ("The approved work consists
#           of"), MISC (amends a prior permit and cites it), NOC (a letter
#           recording work done WITHOUT a permit), WSL (an abandoned
#           application). Also: the letter types write "Manhattan Block/Lot:
#           587 / 46" inline rather than as stacked labels, so 20,103 notices
#           were taking their parcel from the feed; and work kinds are now
#           classified from the NARRATIVE only — falling back to the whole
#           document let letterhead boilerplate decide, which is how a permit
#           with no work description still came back "facade_alteration".
#   lpc/6   the enforcement record, properly. lpc/5 looked for "without an LPC
#           permit" and found 0.5%; the documents say "without permit(s)" and
#           it is 23.2%. Reading the surrounding sentence found the structure
#           underneath: Notices of Violation and Warning Letters cited by
#           number, and each either HEREBY RESCINDED (20.2%) or REMAINING IN
#           EFFECT (7.8%). Those are opposite facts about a parcel. Also fixed:
#           the borough on letter types, which a stale guard had blocked, so
#           94% of notices took their BBL from the feed with every digit of it
#           printed on page 1.
PARSER_NOTE = "lpc/6"
_last = [0.0]

CACHE = pathlib.Path(os.environ.get("LPC_CACHE",
                                    pathlib.Path(__file__).with_name("lpc_cache")))
LEDGER = pathlib.Path(os.environ.get(
    "LPC_LEDGER", pathlib.Path(__file__).with_name("lpc_ledger.jsonl")))

# ⚠ THE CLASSIFICATION THAT MAKES THIS SOURCE USEFUL. A CofA for a rooftop
# addition and a CofA for repointing brick are the same row in the feed and the
# same document type on disk. One is a development event and one is
# maintenance. Ordered most-consequential first; the first match wins.
# ⚠ A PLURAL AND A NUMBER WORD DEFEATED THE MOST IMPORTANT CLASSIFICATION HERE.
# COFA-22-07387's narrative opens "constructing two new buildings on vacant
# lots" and this table returned facade_alteration, is_enlargement=False. The
# pattern was `construct(ing)? a new \w+ ?building` — singular, with "a". A new
# building is the largest development event LPC ever authorises, and it was
# being read as a facade job. Every quantifier and plural is now allowed for.
WORK_KINDS = [
    ("new_building", r"\bnew building(?:s)?\b|"
                     r"construct(?:ing|ion of)?\s+(?:a|an|one|two|three|four|"
                     r"five|\d+)?\s*\(?\d*\)?\s*new\s+\w*\s?building(?:s)?|"
                     r"on (?:a )?vacant lot(?:s)?|"
                     r"demolition of the (?:existing )?building"),
    ("rooftop_addition", r"rooftop addition(?:s)?|roof(?:top)? addition(?:s)?|"
                         r"penthouse addition(?:s)?|one-story rooftop|"
                         r"addition at the roof|set-?back penthouse"),
    ("rear_addition", r"rear (?:yard )?addition(?:s)?|addition at the rear|"
                      r"rear extension(?:s)?"),
    ("enlargement", r"\benlarg(?:e|ing|ement)\b|horizontal addition|vertical addition|"
                    r"increase the (?:height|footprint)"),
    ("demolition", r"\bdemolish(?:ing)?\b|demolition of"),
    ("facade_alteration", r"masonry opening|new opening|storefront|areaway|"
                          r"fenestration|façade|facade"),
    ("restoration", r"restor(?:e|ing|ation)|repoint|in-kind|recreat(?:e|ing)"),
    ("mechanical", r"HVAC|mechanical equipment|condenser|bulkhead"),
]
ENLARGING = {"new_building", "rooftop_addition", "rear_addition", "enlargement"}


def _pace():
    wait = PACE - (time.time() - _last[0])
    if wait > 0:
        time.sleep(wait)
    _last[0] = time.time()


def fetch(regulation_number):
    CACHE.mkdir(parents=True, exist_ok=True)
    p = CACHE / f"{re.sub(r'[^A-Za-z0-9._-]', '_', regulation_number)}.pdf"
    if p.exists() and p.stat().st_size > 0:
        return p, "cached"
    _pace()
    req = urllib.request.Request(f"{BASE}/{regulation_number}.pdf",
                                 headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=120) as r:
        body = r.read()
    if not body.startswith(b"%PDF"):
        return None, f"NOT_PDF bytes={len(body)}"
    p.write_bytes(body)
    return p, "fetched"


def _tidy(s, limit=600):
    return re.sub(r"\s+", " ", s or "").strip()[:limit]


def _page_texts(path):
    import pypdf
    return [(pg.extract_text() or "") for pg in pypdf.PdfReader(str(path)).pages]


LABELS = {
    "cofa": r"COFA\s*\n?\s*(COFA-[\d-]+)",
    "docket": r"DOCKET\s*#:\s*\n?\s*(LPC-[\d-]+)",
    "issue_date": r"ISSUE DATE:\s*\n?\s*([\d/]{6,10})",
    "expiration": r"EXPIRATION DATE:\s*\n?\s*([\d/]{6,10})",
    "block_lot": r"BLOCK/LOT:\s*\n?\s*([\d]+)\s*/\s*([\d]+)",
    "borough": r"BOROUGH:\s*\n?\s*([A-Za-z ]{3,20})",
}


def decode(regulation_number, path, index_row=None):
    """One CofA -> a structured reading. Refuses to assert an envelope, because
    the document does not state one."""
    pts = _page_texts(path)
    text = "\n".join(pts)
    flat = re.sub(r"\s+", " ", text)
    d = {"regulation_number": regulation_number, "pages": len(pts),
         "chars": sum(len(t) for t in pts),
         # the completeness test — every claim carries pages_read/pages_total
         "pages_read": sum(1 for t in pts if len(t.strip()) > 40)}
    if d["chars"] < 400:
        d["status"] = "unreadable"
        d["pages_read"] = 0
        d["note"] = "no extractable text — image-only scan, not an empty permit"
        return d
    d["status"] = "ok"

    for k, pat in LABELS.items():
        m = re.search(pat, text, re.I)
        if not m:
            continue
        if k == "block_lot":
            d["block_stated"], d["lot_stated"] = int(m.group(1)), int(m.group(2))
        else:
            d[k] = _tidy(m.group(1), 40)
    m = re.search(r"ADDRESS:\s*\n?\s*(.{4,90}?)(?:\n|Apt/Floor)", text, re.I)
    if m:
        d["address_stated"] = _tidy(m.group(1), 90)
    # the historic district / landmark name is printed in the permit's own
    # header block. Taking it from the feed's `lmnametype` instead would be an
    # index value riding inside a document-cited fact.
    m = re.search(r"\n([A-Z][A-Za-z'’ .\-]{3,55}?"
                  r"(?:Historic District|Individual Landmark|Scenic Landmark|"
                  r"Interior Landmark))\s*\n", text)
    if m:
        d["historic_context_stated"] = _tidy(m.group(1), 70)
    m = re.search(r"Apt/Floor:\s*([^\n]{0,60})", text, re.I)
    if m:
        # the feed has no floor granularity at all — a rooftop-only permit and
        # a whole-building permit are the same row there
        d["apt_floor"] = _tidy(m.group(1), 60)
    m = re.search(r"ISSUED TO:\s*\n?((?:[^\n]{2,60}\n){1,6})", text, re.I)
    if m:
        who = []
        for x in m.group(1).strip().split("\n"):
            x = x.strip()
            # the form labels sit in the same text stream as the address block
            if not x or re.fullmatch(r"COFA|CNE|PERMIT|[A-Z ]{2,12}:?", x):
                break
            who.append(x)
        d["issued_to"] = who

    # ★ the decision dates, which the feed does not carry
    m = re.search(r"Public Meeting of\s+([A-Z][a-z]+ \d{1,2},? \d{4})", flat)
    if m:
        d["public_meeting"] = m.group(1)
    m = re.search(r"Public Hearing (?:and Public Meeting )?of\s+"
                  r"([A-Z][a-z]+ \d{1,2},? \d{4})", flat)
    if m:
        d["public_hearing"] = m.group(1)
        d["public_hearing_source"] = "stated"
    elif re.search(r"Public Hearing of the same date", flat, re.I) and d.get("public_meeting"):
        # the document says it, just not as a date. Resolving it is a reading,
        # not a guess — but it is marked so it never looks like a printed date.
        d["public_hearing"] = d["public_meeting"]
        d["public_hearing_source"] = "derived: \"Public Hearing of the same date\""
    m = re.search(r"application completed on\s+([A-Z][a-z]+ \d{1,2},? \d{4})", flat)
    if m:
        d["application_completed"] = m.group(1)
    m = re.search(r"(?:voted to|voted at)[^.]{0,60}?(grant|deny|approve)", flat, re.I)
    if m:
        d["vote"] = m.group(1).lower()

    # ⚠ THE LETTER TYPES NAME THE BOROUGH ONLY HERE, INLINE:
    #     "… NOTICE OF COMPLIANCE  Queens Block/Lot: 1265 / 33  ISSUED TO: …"
    # There is no stacked "BOROUGH:" label on an NOC or a WSL. The LABELS loop
    # above matches "Block/Lot:" case-insensitively, so block and lot always
    # parsed and the borough never did — and a BBL needs all three, so
    # `bbls()` fell back to the feed on 94% of notices (617 of 10,050 read
    # from the document) while every digit of the answer was on page 1.
    #
    # An earlier version of this guarded on `if "block_stated" not in d`, which
    # is precisely why it never ran: the block was already set. Read the
    # borough whenever it is MISSING, not whenever the block is.
    if not d.get("borough"):
        m = re.search(r"([A-Z][a-z]+(?: [A-Z][a-z]+)?)\s*Block/Lot:\s*"
                      r"(\d{1,5})\s*/\s*(\d{1,5})", text)
        if m and m.group(1).strip().lower() in BORO_NUM:
            d["borough"] = m.group(1).strip()
            d.setdefault("block_stated", int(m.group(2)))
            d.setdefault("lot_stated", int(m.group(3)))

    # the approved-work narrative and the findings
    # ⚠ FIVE DOCUMENT SHAPES, NOT ONE. Spot-checking one permit of each type
    # before sweeping 127,048 of them: every non-CofA type returned a 0-character
    # narrative, because this regex knew only the CofA's opening phrase.
    #
    #   CofA        "The proposal, as approved, consists of …"  + findings
    #   CNE/XCNE    "…hereby approves certain alterations… The approved work
    #   PMW          consists of …"  — staff level, no hearing, no findings
    #   MISC        "…the Commission issued Certificate of No Effect 14-2081
    #                (LPC-13-1852) on March 22, 2013, establishing a master
    #                plan…" — AMENDS A PRIOR PERMIT and cites it by number
    #   NOC         a LETTER: "staff … conducted a site visit … and found that
    #                the removal of the awning installed WITHOUT LPC permit(s)"
    #                — an ENFORCEMENT record, which exists nowhere else
    #   WSL         "NOTICE OF WITHDRAWAL … remained incomplete for over 90
    #                days" — an abandoned application
    #
    # One phrase separated 52,297 Certificates of No Effect from being read at
    # all, and the sweep would have cost ~53 hours to produce nothing.
    m = re.search(r"The proposal,? as approved,? consists of(.{50,6000}?)"
                  r"(?:With regard to this proposal|In reviewing this proposal|"
                  r"the Commission found)", flat, re.I | re.S)
    if not m:
        m = re.search(r"The approved work consists of(.{40,6000}?)"
                      r"(?:This permit|The approved documents|PLEASE NOTE|"
                      r"SHOP DRAWINGS|Please direct)", flat, re.I | re.S)
    if not m:
        m = re.search(r"(?:hereby approves|approves certain alterations)"
                      r"(.{60,6000}?)(?:This permit|The approved documents|"
                      r"PLEASE NOTE|Please direct)", flat, re.I | re.S)
    if not m:
        # the letter forms — NOC and WSL state the substance without a
        # "consists of" clause at all
        m = re.search(r"(?:staff (?:reviewed|received)|The Landmarks "
                      r"Preservation Commission received)(.{60,4000}?)"
                      r"(?:This (?:notice|letter)|Please direct|PLEASE NOTE|$)",
                      flat, re.I | re.S)
    if not m:
        m = re.search(r"The proposal,? as approved,? consists of(.{50,6000})", flat, re.I | re.S)
    if m:
        d["approved_work"] = _tidy(m.group(1), 6000)
        d["approved_work_page"] = _page_of(pts, m.group(1)[:60])
    # ⚠ THE STOP WORD IS INSIDE THE PROSE. The first version ended the findings
    # at /Therefore/, and LPC findings are written as "...with the loss of both
    # stoops, THEREFORE the proposed alterations will bring it closer to its
    # historic appearance..." — so the capture stopped 168 characters in, on the
    # first sentence, and looked like a successful extraction. The real
    # terminators are structural, not rhetorical.
    blocks = []
    for m in re.finditer(r"the Commission found(.{50,20000}?)"
                         r"(?:is being issued|SHOP DRAWINGS|"
                         r"This letter constitutes the permit|"
                         r"The approved documents,)", flat, re.I | re.S):
        blocks.append(m)
    if blocks:
        d["findings"] = _tidy(" ⏐ ".join(b.group(1) for b in blocks), 20000)
        d["findings_page"] = _page_of(pts, blocks[0].group(1)[:60])
        # a CofA can hold TWO findings blocks — the approval, and a later
        # staff-level review of "additional work" folded into the same permit
        d["findings_blocks"] = len(blocks)

    # ★ THE RULE THE APPROVAL RESTS ON. LPC's Title 63 RCNY sections are the
    # analogue of a ZR section in a BSA resolution: they name WHAT KIND of
    # change was permissible. §2-15 is "Rooftop and Rear Yard Additions or
    # Enlargements" — finding it is the strongest signal in the document that
    # the building got bigger.
    rcny = sorted(set(re.findall(r"Section\s*(2-\d{1,2}(?:\([a-z0-9]\))"
                                 r"(?:\([a-z0-9ivx]+\))*)", flat, re.I)))
    d["rcny_sections"] = rcny
    d["rcny_titles"] = sorted(set(
        _tidy(t, 80) for t in re.findall(
            r"Section 2-\d{1,2} for ([A-Z][A-Za-z ,/&-]{6,70})", flat)))

    # ★ THE PROFESSIONAL TEAM, named on the drawing list. The feed's
    # applicant_name is one person; the document names the architect, every
    # engineer, and — on the cc line — the zoning consultant or expeditor who
    # is usually the person actually running the job.
    team = []
    # ⚠ "R.A." AND "RA" ARE THE SAME CREDENTIAL AND ONLY ONE OF THEM MATCHED.
    # Written against COFA-25-07271, which reads "Juliet Hernandez-Eli, RA".
    # COFA-24-11997 reads "Anne Marie Lubrano, R.A." and the pattern returned an
    # empty list — indistinguishable from a permit that names no professionals.
    # Same shape as every other failure found today: right on the document it
    # was written against, silently empty elsewhere, nothing recording it.
    for m in re.finditer(r"prepared by\s+([A-Z][A-Za-z.'’\- ]{3,40}?),\s*"
                         r"(R\.?\s?A\.?|P\.?\s?E\.?|A\.?I\.?A\.?|R\.?L\.?A\.?)"
                         r"(?=[;,.\s]|$)", flat):
        team.append({"name": _tidy(m.group(1), 60),
                     "credential": re.sub(r"[.\s]", "", m.group(2)).upper()})
    # the FIRM is named without a credential, and it is the durable contact —
    # individuals move, the practice keeps the file
    for m in re.finditer(r"prepared by\s+([A-Z][A-Za-z.'’&\- ]{4,60}?"
                         r"(?:Architects?|Architecture|Engineers?|Engineering|"
                         r"Associates|Studio|Design|LLC|PLLC|PC))(?=[,;.\s])",
                         flat):
        team.append({"name": _tidy(m.group(1), 70), "credential": "firm"})
    d["design_team"] = [dict(t) for t in {json.dumps(x, sort_keys=True): x
                                          for x in team}.values()]
    m = re.search(r"\bcc:\s*([^\n]{3,160})", text)
    if m:
        d["cc"] = _tidy(m.group(1), 160)
    m = re.search(r"Please direct inquiries to\s+([A-Z][A-Za-z'’\- ]{2,20}(?: [A-Z][A-Za-z'’\-]{1,20}){0,2})", flat)
    if m:
        d["lpc_staff"] = _tidy(m.group(1), 40)
    m = re.search(r"PROVIDED TO:\s*\n?\s*([^\n]{3,120})", text)
    if m:
        d["documents_provided_to"] = _tidy(m.group(1), 120)

    # ★ the document chain — CofAs cite other LPC documents by number
    d["cited_documents"] = sorted(set(
        re.findall(r"\b((?:LPC|COFA|CNE|MISC|SUL)[- ]\d{2}[- ]\d{3,6})\b", flat)))

    # ⚠ AND THE INSTRUMENT ITSELF. A Notice of Compliance records work done
    # WITHOUT a permit; a Notice of Withdrawal records an abandoned
    # application. Neither is an approval, and classifying either as one would
    # put a permission on a parcel that never had it.
    for label, kind in (("NOTICE OF COMPLIANCE", "notice_of_compliance"),
                        ("NOTICE OF WITHDRAWAL", "notice_of_withdrawal"),
                        ("CERTIFICATE OF NO EFFECT", "certificate_of_no_effect"),
                        ("PERMIT FOR MINOR WORK", "permit_for_minor_work"),
                        ("CERTIFICATE OF APPROPRIATENESS", "certificate_of_appropriateness")):
        if label in text.upper():
            d["instrument_stated"] = kind
            break
    # ★ THE ENFORCEMENT RECORD, and it is richer than a flag.
    #
    # I first looked for "without an LPC permit" and found it on 0.5% of
    # notices. The documents say "without permit(s)" — no "LPC" — and reading
    # the surrounding sentence turned up a whole structure I had not asked for:
    #
    #   400 Notices of Compliance scanned
    #     23.2%  work done without permit(s)
    #     20.2%  a Warning Letter or Notice of Violation is HEREBY RESCINDED
    #     19.5%  a Notice of Violation is cited by number
    #     11.5%  a Warning Letter is cited by number
    #      7.8%  the violation REMAINS IN EFFECT
    #
    # Those last two are opposite facts about a parcel. A rescinded violation is
    # history; one that remains in effect is a live encumbrance on a landmarked
    # building, and it exists in no feed, no zoning layer and no ACRIS record.
    if re.search(r"without (?:an? )?(?:LPC |Landmarks )?permit", flat, re.I):
        d["work_without_permit"] = True
    m = re.search(r"Notice of Violation[s]?\s*(?:No\.?\s*)?([\w/-]{3,20})", flat, re.I)
    if m:
        d["notice_of_violation"] = _tidy(m.group(1), 20)
    m = re.search(r"Warning Letter\s*(?:No\.?\s*)?([\w/-]{3,20})", flat, re.I)
    if m:
        d["warning_letter"] = _tidy(m.group(1), 20)
    rescinded = bool(re.search(r"(?:is|are) hereby rescinded|hereby rescind", flat, re.I))
    open_still = bool(re.search(r"remains? in (?:effect|force)", flat, re.I))
    if rescinded or open_still or d.get("work_without_permit"):
        # ⚠ BOTH can appear in one notice — several violations, some closed and
        # some not. "open" wins, because a parcel with one live violation is
        # encumbered regardless of how many others were cleared.
        d["enforcement_status"] = ("open" if open_still else
                                   "rescinded" if rescinded else "cited")
    m = re.search(r"(?:issued|amends?)\s+(?:Certificate of No Effect|"
                  r"Certificate of Appropriateness|permit)\s+([\w-]+)\s*"
                  r"\((LPC-[\d-]+)\)", flat, re.I)
    if m:
        d["amends"] = {"permit": m.group(1), "docket": m.group(2)}

    # ⚠ CLASSIFY FROM THE NARRATIVE ONLY. Falling back to the whole document
    # meant boilerplate decided the answer: a Certificate of No Effect with no
    # narrative still came back `facade_alteration` because the word "façade"
    # appears in the letterhead-adjacent text. A work kind with no work
    # description behind it is an invention.
    work = d.get("approved_work") or ""
    kinds = [k for k, pat in WORK_KINDS if re.search(pat, work, re.I)]
    d["work_kinds"] = kinds
    d["is_enlargement"] = bool(set(kinds) & ENLARGING)
    if index_row:
        d["index"] = {k: index_row.get(k) for k in
                      ("docket", "address", "borough", "block", "lot",
                       "worktypes", "issue_date", "received_date",
                       "expiration_date", "lmnametype", "applicant_name",
                       "owner_name")}
    return d


def _page_of(page_texts, snippet):
    key = re.sub(r"\s+", " ", snippet).strip()[:40]
    for i, t in enumerate(page_texts, 1):
        if key and key in re.sub(r"\s+", " ", t):
            return i
    return 1


def selfcheck(d):
    """What the document says about itself versus what the feed says."""
    out = []
    ix = d.get("index") or {}
    if d.get("block_stated") and (ix.get("block") or "").isdigit():
        ok = (int(ix["block"]) == d["block_stated"] and
              str(ix.get("lot") or "").isdigit() and
              int(ix["lot"]) == d.get("lot_stated"))
        out.append({"check": "feed block/lot == permit block/lot",
                    "stated": f"feed {ix.get('block')}/{ix.get('lot')}",
                    "computed": f"doc {d.get('block_stated')}/{d.get('lot_stated')}",
                    "verdict": "PASS" if ok else "FAIL"})
    if d.get("docket") and ix.get("docket"):
        out.append({"check": "feed docket == permit docket",
                    "stated": ix["docket"], "computed": d["docket"],
                    "verdict": "PASS" if ix["docket"] == d["docket"] else "FAIL"})
    # ⚠ TWO DIFFERENT THINGS WERE ONE CHECK. "narrative present" failed whenever
    # the narrative was present but the classifier had no pattern for it, so a
    # retrieval success and a lexicon gap raised the same alarm and neither
    # could be counted. They are separate failures with separate fixes.
    out.append({"check": "approved-work narrative extracted",
                "stated": f"{len(d.get('approved_work') or '')} chars",
                "computed": "present" if d.get("approved_work") else "ABSENT",
                "verdict": "PASS" if d.get("approved_work") else "FAIL"})
    if d.get("approved_work"):
        out.append({"check": "narrative classified to a work kind",
                    "stated": f"{len(d['approved_work'])} chars",
                    "computed": ",".join(d.get("work_kinds") or []) or "(no pattern matched)",
                    "verdict": "PASS" if d.get("work_kinds") else "FAIL"})
    out.append({"check": "parcel read from the permit, not the feed",
                "stated": f"block={d.get('block_stated')} lot={d.get('lot_stated')}",
                "computed": bbls(d)[1],
                "verdict": "PASS" if bbls(d)[1] == "document" else "FAIL"})
    return out


BORO_NUM = {"manhattan": 1, "bronx": 2, "brooklyn": 3, "queens": 4,
            "staten island": 5}

MONTHS = {m: i for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july", "august",
     "september", "october", "november", "december"], 1)}


def _iso(s):
    if not s:
        return None
    m = re.match(r"([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})", s.strip())
    if m and m.group(1).lower() in MONTHS:
        return f"{int(m.group(3)):04d}-{MONTHS[m.group(1).lower()]:02d}-{int(m.group(2)):02d}"
    m = re.match(r"(\d{1,2})/(\d{1,2})/(\d{2,4})", s.strip())
    if m:
        y = int(m.group(3))
        y += 2000 if y < 100 and y < 70 else (1900 if y < 100 else 0)
        return f"{y:04d}-{int(m.group(1)):02d}-{int(m.group(2)):02d}"
    return None


def bbls(d):
    """The parcel, from the permit's own BLOCK/LOT and BOROUGH fields.

    The feed is consulted only where the document field failed to extract, and
    the fact then records that it did — a BBL read off the permit and a BBL
    borrowed from a search result must not arrive looking identical.
    """
    ix = d.get("index") or {}
    prov = "document"
    boro = BORO_NUM.get((d.get("borough") or "").strip().lower())
    if not boro:
        boro = BORO_NUM.get((ix.get("borough") or "").strip().lower())
        prov = "partly_index"
    blk, lot = d.get("block_stated"), d.get("lot_stated")
    if not blk and str(ix.get("block") or "").isdigit():
        blk, prov = int(ix["block"]), "partly_index"
    if not lot and str(ix.get("lot") or "").isdigit():
        lot, prov = int(ix["lot"]), "partly_index"
    if not (boro and blk and lot):
        return [], "insufficient"
    return [f"{boro}{blk:05d}{lot:04d}"], prov


def to_facts(d, run_id=None, emit=True):
    """A CofA -> facts.

    ⚠ NO ENVELOPE FACT IS EMITTED, EVER. The document states no floor area, FAR,
    height or unit count, so there is nothing to emit and inventing one from the
    narrative would be the worst kind of plausible.
    """
    out = []

    def add(f):
        f["lpc_parser"] = PARSER_NOTE
        f["pages_total"] = d.get("pages")
        f["pages_read"] = d.get("pages_read")
        out.append(f)
        if emit:
            sink.emit(f, run_id)

    bs, bbl_prov = bbls(d)
    ix = d.get("index") or {}
    happened = _iso(d.get("public_meeting")) or _iso(d.get("public_hearing"))
    recorded = _iso(d.get("issue_date")) or (ix.get("issue_date") or "")[:10] or None
    if not bs:
        return out
    # ⚠ NO INDEX FALLBACK ON `verbatim`. The first version wrote the feed's
    # `worktypes` code into verbatim when the narrative did not extract — an
    # index value carrying a document_id and a page number, which is the exact
    # thing RULE_DOCUMENTS_NOT_INDEXES exists to stop. A permit whose narrative
    # could not be read is a permit that has not been decoded, and it says so.
    if not d.get("approved_work"):
        return out
    add(F.Fact("permit_issued", document_id=d["regulation_number"],
               page=d.get("approved_work_page") or 1, bbls=bs, source=SOURCE,
               happened=happened, recorded=recorded,
               verbatim=_tidy(d.get("approved_work"), 900),
               permit_type="Certificate of Appropriateness",
               bbl_provenance=bbl_prov,
               docket=d.get("docket") or ix.get("docket"),
               work_kinds=d.get("work_kinds"),
               is_enlargement=d.get("is_enlargement"),
               historic_context=d.get("historic_context_stated"),
               apt_floor=d.get("apt_floor"),
               expires=_iso(d.get("expiration")),
               parties=[x for x in (d.get("issued_to") or [])[:3]],
               cited_documents=d.get("cited_documents")))
    # ★ WORK DONE WITHOUT A PERMIT. 25.2% of Notices of Compliance say so, and
    # it appears nowhere else in this project — not in the feed's worktypes,
    # not in ACRIS, not in zoning. An owner who altered a landmark without
    # authorisation is a fact about the parcel and about the owner.
    if d.get("work_without_permit") or d.get("enforcement_status"):
        add(F.Fact("condition_imposed", document_id=d["regulation_number"],
                   page=d.get("approved_work_page") or 1, bbls=bs, source=SOURCE,
                   happened=happened, recorded=recorded,
                   verbatim=_tidy(d.get("approved_work"), 900),
                   note="LPC ENFORCEMENT — work performed WITHOUT a permit at "
                        "a landmarked property",
                   work_without_permit=True,
                   enforcement_status=d.get("enforcement_status"),
                   notice_of_violation=d.get("notice_of_violation"),
                   warning_letter=d.get("warning_letter"),
                   permit_type=d.get("instrument_stated")))
    if d.get("findings"):
        add(F.Fact("condition_imposed", document_id=d["regulation_number"],
                   page=d.get("findings_page") or 1, bbls=bs, source=SOURCE,
                   happened=happened, recorded=recorded,
                   verbatim=_tidy(d["findings"], 900),
                   note="Commission findings — the reasoning the approval rests "
                        "on, which constrains what a similar proposal may do"))
    return out


def index(where=None, cofa_only=False):
    """EVERY permit type by default.

    ⚠ THIS USED TO FILTER TO CofA AND I REPORTED THAT AS THE UNIVERSE. The
    PermitFiles archive serves all of them — 127,048 permits issued 2016+ carry
    a number and a document. CofA is 2,870 of that, 2.3%. Reasoning that a
    "Certificate of No Effect" cannot matter was reasoning from an index label,
    and the documents disagree: a Notice of Compliance records work done WITHOUT
    a permit, and a Notice of Withdrawal records an application abandoned.
    """
    w = "regulation_type='Certificate of Appropriateness'" if cofa_only else None
    if where:
        w = f"{w} and ({where})" if w else where
    # ⚠ ASK FOR THE COLUMNS YOU USE. Measured: the full 28-column pull of
    # 349,692 permits holds 820 MB; these thirteen hold 224 MB — a 73% saving
    # on columns the decoder never reads. Two sweeps died at exit 120 with the
    # machine down to 1.7 GB free, and this was my share of why. The document
    # is the source of truth anyway; the index is a finding aid, so pulling
    # every field of it is paying memory for something I am not allowed to
    # treat as a fact.
    return bulk.socrata(PERMITS, where=w, select=INDEX_COLUMNS)


# ⚠ ENFORCEMENT FIRST. A Notice of Compliance records work done WITHOUT an LPC
# permit — the only enforcement signal in this whole chat, and 9,336 of them.
# A Notice of Withdrawal records an abandoned application. Both outrank 52,297
# Certificates of No Effect, which by their own name record work with no effect
# on a protected feature.
PRIORITY = ["Notice of Compliance", "Certificate of Appropriateness",
            "Withdrawn at Staff Level", "Miscellaneous - Amendment",
            "Permit for Minor Work", "Certificate of No Effect",
            "Expedited Certificate of No Effect"]


def prefetch(rows, workers=3, ceiling=3.0):
    """Fill the cache concurrently under a governor, then let the decode loop
    run at full speed off disk.

    Separating RETRIEVAL from DECODING is the efficiency win. The decode is
    pure CPU and needs no pacing at all; only the fetch touches the host. The
    old loop interleaved them, so every parse happened inside the politeness
    budget.
    """
    todo = [r for r in rows if r.get("regulation_number")
            and not (CACHE / f"{r['regulation_number']}.pdf").exists()]
    if not todo:
        return {"ok": 0, "skipped": len(rows), "note": "all cached"}
    CACHE.mkdir(parents=True, exist_ok=True)

    def landed(r, body, status):
        if body and body.startswith(b"%PDF"):
            (CACHE / f"{r['regulation_number']}.pdf").write_bytes(body)

    gov = fetcher.Governor(start=1.0, ceiling=ceiling)
    out = fetcher.fetch_many(
        todo, lambda r: f"{BASE}/{r['regulation_number']}.pdf", landed, UA,
        workers=workers, governor=gov)
    out["queued"] = len(todo)
    return out


def retrievable(rows):
    """The 2016+ subset. Stated, not assumed — see the module docstring."""
    return [r for r in rows
            if r.get("regulation_number") and (r.get("issue_date") or "") >= "2016"]


def _append(path, rec):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, separators=(",", ":"), default=str) + "\n")
        f.flush()


def done_already():
    if not LEDGER.exists():
        return {}
    out = {}
    with open(LEDGER, encoding="utf-8") as f:
        for line in f:
            try:
                r = json.loads(line)
                out[r["regulation_number"]] = r["decode_status"]
            except Exception:
                pass
    return out


def run(rows, run_id=None, emit=True, beat_every=20, resume=True):
    run_id = run_id or f"lpc-{int(time.time())}"
    # ⚠ ONE WRITER PER SOURCE. Three separate corruptions came from two
    # processes appending to the same ledger; see runlock.py.
    _lock = runlock.Lock(SOURCE, run_id).acquire(script="lpc_cofa.py")
    total = len(rows)
    # ⚠ RESUME MUST BE DEFEATABLE. A parser bump means every already-decoded
    # row needs re-reading, and `done_already()` cannot tell "read correctly"
    # from "read by a parser I have since retracted" — it only knows the
    # calendar was touched. Without this flag a re-decode silently skips 9,200
    # documents and reports success.
    seen = done_already() if resume else {}
    counts = Counter()
    sink.heartbeat(SOURCE, run_id, done=0, total=total,
                   note=f"{len(seen)} already in ledger")
    for i, r in enumerate(rows, 1):
        rn = r.get("regulation_number")
        if seen.get(rn) in ("decoded", "unreadable"):
            counts["skipped"] += 1
            continue
        rec = {"regulation_number": rn, "run_id": run_id, "at": int(time.time())}
        try:
            p, how = fetch(rn)
            if p is None:
                counts["FAILED"] += 1
                _append(LEDGER, {**rec, "decode_status": "FAILED", "note": how})
                continue
            d = decode(rn, p, r)
            if d["status"] == "unreadable":
                counts["unreadable"] += 1
                _append(LEDGER, {**rec, "decode_status": "unreadable",
                                 "note": d["note"], "pages_total": d["pages"]})
                continue
            ck = selfcheck(d)
            fs = to_facts(d, run_id=run_id, emit=emit)
            counts["decoded"] += 1
            counts["facts"] += len(fs)
            counts["enlargement"] += bool(d.get("is_enlargement"))
            counts["with_narrative"] += bool(d.get("approved_work"))
            counts["work_without_permit"] += bool(d.get("work_without_permit"))
            if d.get("enforcement_status"):
                counts["enforcement:" + d["enforcement_status"]] += 1
            counts["no_narrative_no_fact"] += (not d.get("approved_work"))
            counts["with_meeting_date"] += bool(d.get("public_meeting"))
            for k in d.get("work_kinds") or []:
                counts[f"kind:{k}"] += 1
            _append(LEDGER, {**rec, "decode_status": "decoded",
                             "pages_total": d["pages"], "facts": len(fs),
                             "bbls": bbls(d)[0], "bbl_provenance": bbls(d)[1], "work_kinds": d.get("work_kinds"),
                             "is_enlargement": d.get("is_enlargement"),
                             "work_without_permit": d.get("work_without_permit"),
                             "enforcement_status": d.get("enforcement_status"),
                             "notice_of_violation": d.get("notice_of_violation"),
                             "instrument_stated": d.get("instrument_stated"),
                             "public_meeting": d.get("public_meeting"),
                             "cited_documents": d.get("cited_documents"),
                             "checks_failed": [c["check"] for c in ck
                                               if c["verdict"] == "FAIL"]})
        except Exception as e:
            counts["FAILED"] += 1
            _append(LEDGER, {**rec, "decode_status": "FAILED",
                             "note": f"{type(e).__name__}: {e}"})
        if i % beat_every == 0:
            _lock.beat()
            sink.heartbeat(SOURCE, run_id, done=i, total=total,
                           note=json.dumps(dict(counts)))
    sink.heartbeat(SOURCE, run_id, done=total, total=total,
                   status="complete" if not counts["FAILED"] else "PARTIAL",
                   note=json.dumps(dict(counts)))
    _lock.release()
    return {"run_id": run_id, "total": total, "counts": dict(counts)}


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int)
    ap.add_argument("--all-years", action="store_true")
    ap.add_argument("--type", help="only this regulation_type")
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--ceiling", type=float, default=3.0,
                    help="max requests/sec; the governor backs off below this "
                         "on any refusal or latency drift")
    ap.add_argument("--no-prefetch", action="store_true")
    ap.add_argument("--no-resume", action="store_true",
                    help="re-decode everything, ignoring the ledger — required "
                         "after a parser bump")
    ap.add_argument("--cofa-only", action="store_true",
                    help="only Certificates of Appropriateness (2,870). "
                         "Default is every permit type.")
    a = ap.parse_args()
    where = f"regulation_type='{a.type}'" if a.type else None
    rows = index(where=where, cofa_only=a.cofa_only)
    print(f"permits in feed: {len(rows):,}")
    q = rows if a.all_years else retrievable(rows)
    print(f"retrievable (2016+, has regulation_number): {len(q):,}"
          f"  — the other {len(rows)-len(q):,} predate the archive")
    # highest-signal instrument first, newest within each — so a partial sweep
    # is worth something rather than being an arbitrary slice
    rank = {t: i for i, t in enumerate(PRIORITY)}
    q.sort(key=lambda r: (rank.get(r.get("regulation_type"), 99),
                          r.get("issue_date") or ""),
           reverse=False)
    q.sort(key=lambda r: rank.get(r.get("regulation_type"), 99))
    if a.limit:
        q = q[:a.limit]
        print(f"LIMITED to {len(q)} — a sample, not the universe")
    # ⚠ THE LOCK MUST COVER THE FETCH, NOT JUST THE DECODE. run() acquires it,
    # but prefetch runs BEFORE run() — so for the whole retrieval phase, which
    # is the only part that touches the host, nothing stopped a second process
    # from doubling the request rate against a host that publishes no crawl
    # policy. The governor limits one process; the lock is what makes "one
    # process" true.
    _pre = runlock.Lock(SOURCE, f"lpc-prefetch-{int(time.time())}").acquire(script="lpc_cofa.py")
    if not a.no_prefetch:
        print("prefetching under a governor (host sets the rate)…")
        print(" ", json.dumps(prefetch(q, workers=a.workers, ceiling=a.ceiling)))
    _pre.release()
    print(json.dumps(run(q, resume=not a.no_resume), indent=1, default=str))
