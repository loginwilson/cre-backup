"""FILL THE REAL TABLES — claim -> event -> account. Not page regions.

    python extract.py --doc FT_1680008647768

⚠ THE FIRST VERSION OF THIS FILE BUILT THE WRONG TABLES AND THE OUTPUT PROVED IT.
It emitted `recording_stamp`, `parties`, `notary` — those are places ink sits on
paper, not `subject × function × mode`. Nineteen of its forty-four rows were the
reel and page number repeated once per page: document metadata, restated, carrying
no event. Login, 2026-08-16: "this tells me nothing of the function or event or
subject." Correct. A page is not a row; an EVENT is a row, and the page is only
where its evidence was found.

    claim    one value read off one page   document · page · box · value
    event    one thing that happened       subject × function × mode · date ·
                                           participants · quantities · terms
    account  one function's state          function · subject · posting

⚠ THE ANCHOR IS COMPUTED, NEVER CLAIMED — THIS IS THE SECOND TIME THAT RULE HAS
PAID. Asking the VLM to name the line its value came from produced correct values
on fabricated anchors: p008 returned block/borough/county/lot/street ALL = "586"
on line 1, and p009 returned every acknowledgment field = "769" on line 1. When it
does not know the line it answers `1`. So it is no longer asked. It returns values
only; the line and box are found by searching the OCR lines here, in code, where
the answer is verifiable. (Routing survived precisely because a line NUMBER was its
whole answer — nothing else to get wrong.)

⚠ AND A VALUE THAT MATCHES NO LINE IS KEPT, FLAGGED, NOT DROPPED. On film the VLM
reads better than OCR — 98.0% vs 94.5% on this document — so "not in the OCR text"
is often the VLM being RIGHT. Three states, never a boolean:
    verbatim    found in an OCR line. Two channels agree, box is exact.
    corrected   near-matches a line. The VLM cleaned up the OCR; box is that line.
    unanchored  matches no line. KEPT with no box, and it cannot be re-verified,
                so it is the weakest thing this file emits and says so.

⚠ THE PRINTED NAME IS ITS OWN FIELD. The old run captured `signer1 = 387 P.A.S.
ENTERPRISES` (the entity) and `signer2 = Attorney-in-Fact` (a role) and never the
HUMAN who signed. The vocabulary ledger already carries `signature → person` as
`unread` — "sits at the END; every head read stops first". An SPE signature is the
join that binds a person to an entity, so `signer_name` is asked for explicitly and
separately from the entity it signs for.
"""
from __future__ import annotations

import argparse, collections, difflib, json, pathlib, re, sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).parent
DEC = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(DEC))

import route as RT
import run_cli as R
import lexicon as L

# ── FIELDS TYPED BY WHAT THEY BECOME, not by where they sit ──────────────────
# kind -> field -> (prompt hint, the region(s) worth asking on)
SUBJECT_F = {"borough": "borough or county", "block": "the tax BLOCK number, labelled Block — never a reel or page number",
             "lot": "the tax LOT number, labelled Lot — never a reel or page number",
             # ⚠ A MANHATTAN BACKER PRINTS SECTION / BLOCK / LOT / COUNTY as one
             # stack. Section was in the OCR from the first run and never asked for.
             "section": "the SECTION number printed above Block on the backer",
             # ⚠ NO LITERAL EXAMPLE. Any sample parcel key I write here is a
             # string a real backer could print, and the echo guard would then
             # reject the true reading. Describe the shape only.
             "parcel_key": ("the tax block and lot printed together on the "
                            "backer, exactly as shown including both labels — "
                            "read the number printed beside each label"), "street_address": "street address of the premises"}
PARTY_F = {"mortgagor": "the mortgagor/borrower entity name",
           "mortgagor_form": "its organisational form, e.g. a New York limited partnership",
           "mortgagee": "the mortgagee/lender name",
           "signer_name": "the PRINTED HUMAN NAME under a signature (not the entity)",
           "signer_title": "that person's title, e.g. President, Attorney-in-Fact",
           "signer_for": "the entity that person signed on behalf of",
           "notary_name": "the notary's printed name",
           "notary_no": "the notary commission number"}
QTY_F = {"principal_amount": "the principal sum secured, in figures",
         "principal_words": "the principal sum written in words",
         "tax_paid": "mortgage recording tax paid",
         # ⚠ FACE AMOUNT IS NOT NEW MONEY. On a CEMA the principal restates a debt that
         # already existed and only the NEW portion is taxed; without this field the two
         # are indistinguishable and every consolidation reads as fresh lending. Schema
         # note 11. It is also the cross-check partner for tax_paid: new money x 1.5%
         # should equal the stamp, which is how $60,000 was confirmed on this document.
         "taxable_amount": "the amount NEW tax was computed on — on a consolidation or "
                           "CEMA this is the new money only, not the restated total",
         "interest_rate": "the interest rate",
         "term_months": "the term length"}
TERM_F = {"maturity_date": "the maturity or due date",
          "rate_type": "fixed, floating or hybrid",
          "prepayment": "any prepayment penalty, lockout or open right",
          "lien_position": "first, second or subordinate lien",
          "cross_collateral": "other property also securing this obligation",
          # ⚠ THE ONE FIELD WE ALREADY READ AND THEN THREW AWAY. This mortgage is signed
          # by an attorney-in-fact for a general partner of the borrower, and the VLM
          # transcribed `Attorney-in-Fact` and `General Partner` correctly and repeatedly
          # from PRINTED text beside the signature. It was captured as `signer_title` —
          # a name with no schema slot — and dropped at compose(). The schema defines
          # `authority` as a term attaching to a PARTICIPANT: scope and expiry of a power
          # to act, and it is the payload a POA exists to create (schema note 2).
          # ⚠ Authority is PRINTED, unlike the signature it sits beside. That is why it
          # is recoverable when `signature -> person` is not.
          "authority": "the capacity the signer acts in and for whom — e.g. "
                       "Attorney-in-Fact, General Partner, President — as PRINTED "
                       "beside the signature, never guessed from handwriting"}
EVENT_F = {"instrument_type": "the instrument's own title, e.g. MORTGAGE",
           "execution_date": "the date the parties executed it",
           "recording_date": "the date it was recorded",
           "reel": "recording reel number", "reel_page": "recording page number"}

# ⚠ A FIELD MAY ONLY BE SOURCED FROM A REGION THAT COULD HONESTLY CARRY IT.
# The first run built BBL 1005860768 from `block=586 lot=768` — which was the
# RECORDING STAMP (reel 586, page 768), not the legal description. The real lot
# is block 883. compose() had picked the best-anchored claim and ignored where it
# came from, then stamped resolved=True on a tax lot made of a reel number.
# Routing already knew that line was a stamp; this is what stops that being lost.
SOURCE_GATE = {
    "parcel_key": {"recording_stamp", "legal_description"},
    "section": {"recording_stamp"},
    "block": {"legal_description", "recording_stamp"},
    "lot": {"legal_description", "recording_stamp"},
    "borough": {"legal_description", "recording_stamp"},
    "street_address": {"legal_description"},
    "reel": {"recording_stamp"}, "reel_page": {"recording_stamp"},
    # ⚠ p010's `notary` region carries 59 lines, so an unrelated "12973" in the
    # acknowledgment outranked p001's correct 60,000 purely on region weight.
    # Region weight is a tie-breaker, never a substitute for belonging.
    "tax_paid": {"recording_stamp", "granting_clause", "amount"},
    "principal_amount": {"granting_clause", "amount"},
    "principal_words": {"granting_clause", "amount"},
    # ⚠ taxable_amount rides the SAME regions as tax_paid because that is where the
    # arithmetic lives — a CEMA states the new money next to the stamp it produced.
    "taxable_amount": {"recording_stamp", "granting_clause", "amount"},
    "signer_name": {"signature", "notary"}, "signer_title": {"signature", "notary"},
    # ⚠ authority is PRINTED text in the execution block, so it is gated to the same
    # regions as the signature it qualifies — and unlike signer_name it is allowed to
    # resolve, because the printed capacity survives where the pen does not.
    "authority": {"signature", "notary"},
    "notary_name": {"notary"}, "notary_no": {"notary"},
}

# ⚠ A SENTINEL IS NOT A READING. The model answers the prompt rather than the page
# when it does not know, so these are absences and are counted as such.
SENTINEL = {"notspecified", "none", "na", "n/a", "unknown", "notpresent",
            "notstated", "nil", "null", "notapplicable", "notavailable", "0"}

# ⚠ BARE "0" IS THIS MODEL'S "NOT ON THIS PAGE" AND IT IS NOT ZERO. p001 returned
# interest_rate/maturity_date/prepayment/recording_date/term_months all as "0"
# while returning real values for everything actually present. Treating those as
# readings would post a 0% rate and a zero-month term into the tables. But a zero
# CAN be meaningful for money, so "0" is an absence only for fields where zero is
# not a legal reading — never blanket.
ZERO_IS_ABSENT = {"interest_rate", "maturity_date", "prepayment", "rate_type",
                  "recording_date", "term_months", "execution_date",
                  "lien_position", "cross_collateral"}

KIND = {}
for d, k in ((SUBJECT_F, "subject"), (PARTY_F, "participant"),
             (QTY_F, "quantity"), (TERM_F, "term"), (EVENT_F, "event")):
    for f in d:
        KIND[f] = k
ALL_F = {**SUBJECT_F, **PARTY_F, **QTY_F, **TERM_F, **EVENT_F}

# which page-regions are worth asking which fields on — routing's only job now
ASK_ON = {
    # ⚠ THE BACKER IS WHERE THE PARCEL KEY LIVES. The hand key describes p010 as
    # "ACKNOWLEDGEMENT + BACKER - the parcel key and every recording stamp", and
    # `BLOCK 883` sits there — but routing calls that region recording_stamp, so
    # never asking for block/lot there meant the document's ONLY true block was
    # never requested on any page. The stamps and the parcel key are neighbours;
    # they are separated by their LABELS, not by their region.
    "recording_stamp": ["reel", "reel_page", "recording_date", "tax_paid",
                        "taxable_amount",
                        "instrument_type", "block", "lot", "borough", "parcel_key",
                        "section"],
    "parties": ["mortgagor", "mortgagor_form", "mortgagee", "instrument_type",
                "execution_date"],
    "granting_clause": ["principal_amount", "principal_words", "mortgagee",
                        "interest_rate", "maturity_date"],
    "amount": ["principal_amount", "principal_words", "tax_paid",
               "taxable_amount"],
    "legal_description": ["borough", "block", "lot", "street_address"],
    "covenants": ["maturity_date", "rate_type", "prepayment", "lien_position",
                  "cross_collateral", "interest_rate", "term_months"],
    "signature": ["signer_name", "signer_title", "signer_for", "mortgagor",
                  "authority"],
    "notary": ["notary_name", "notary_no", "signer_name", "signer_for", "authority"],
}

PROMPT_HEAD = (
    "This is a scanned page from a New York property document. Below are the OCR "
    "lines from THIS page, grouped by region. The OCR is often garbled — read the "
    "IMAGE and trust it over the OCR.\n\n"
    "Return ONLY compact JSON on one line mapping field to value:\n"
    "{\"<field>\":\"<value>\"}\n\n"
    # ⚠ NO LINE NUMBERS ASKED FOR. The previous version demanded them and got
    # correct values on invented anchors (everything defaulted to line 1).
    "Do NOT include line numbers. Give the value exactly as printed.\n"
    "OMIT any field not on this page — most pages carry only a few, and inventing "
    "one is worse than missing it. Never guess.\n\nFIELDS:\n")


def norm(s):
    return re.sub(r"[^a-z0-9]+", "", str(s or "").lower())


# ⚠ THE LINE THAT CARRIES A NUMBER SAYS WHAT THE NUMBER IS. Every wrong block/lot
# this document produced came off a line that announces itself: `586  761`,
# `REEL 586c: 763`, `RiEt 586:Aa 764` are recording stamps, and `Northerly side of
# 27th Street with the Easterly side of Fourth Avenue` is a street ordinal that
# yielded lot=27. None of them are parcel keys, and all of them are refusable by
# reading the line rather than the value.
NOT_A_PARCEL_KEY = re.compile(
    r"\breel\b|\bre[a-z]{0,2}[lt]\b|\bstreet\b|\bavenue\b"
    r"|\bside\s+of\b|\bcorner\b|\bnortherly\b|\bsoutherly\b"
    r"|\beasterly\b|\bwesterly\b",
    re.I)


ROLE_MARKER = re.compile(
    r"\bby\s*:|\battorney[- ]in[- ]fact\b|\bgeneral\s+partner\b|\bpresident\b"
    r"\b|\bvice\s+president\b|\bsecretary\b|\bmember\b|\bmanager\b|\btrustee\b",
    re.I)


def printed_name_ok(field, line_text, page_text):
    """Is this a PRINTED name, or a guess at a handwritten mark?

    ⚠ A handwritten signature reaches OCR as an isolated nonsense token on a line
    of its own — `Katbhals`, `Mirort`, `easonu` on FT p009. A printed name sits
    beside a role marker or repeats elsewhere on the page. Requiring one of those
    two corroborations keeps handwriting out of the participant table, and the
    honest consequence is that `signer_name` comes back EMPTY on this document,
    which is what the vocabulary ledger already says: signature -> person, UNREAD.
    """
    if field != "signer_name":
        return True
    line = line_text or ""
    if ROLE_MARKER.search(line):
        return True
    # repeated elsewhere on the page = it is printed text, not one stray mark
    n = norm(line)
    return bool(n) and norm(page_text).count(n) > 1


def parcel_key_ok(field, line_text):
    if field not in ("block", "lot"):
        return True
    return not NOT_A_PARCEL_KEY.search(line_text or "")


def present_in(value, page_text):
    """Do this value's distinctive tokens actually occur on the page?

    ⚠ THE HALLUCINATED DATE IS THE CASE THIS EXISTS FOR. recording_date came back
    as `1970-07-01` and `1980-01-01` — well-formed, plausible, and nowhere on the
    page. They were UNANCHORED, but so was the CORRECT `OCT 2 1981`, so anchor
    state alone could not separate them and the wrong one won a tie on page order.
    A value whose every distinctive token is absent from the page was not read.
    """
    t = norm(page_text)
    toks = [x for x in re.findall(r"[A-Za-z]{3,}|\d{2,}", str(value))]
    if not toks:
        return True
    return any(norm(x) in t for x in toks)


def anchor(value, lines):
    """FIND the line the value sits on. Returns (line_index, state).

    ⚠ THE WHOLE POINT: this is a search, not a question. A model that is asked for
    an anchor will supply one whether or not it knows.
    """
    v = norm(value)
    if not v:
        return None, "empty"
    if len(v) < 3:
        # ⚠ SHORT VALUES ANCHOR ON AN EXACT TOKEN, NEVER A SUBSTRING. `1` occurs
        # inside 1981, 1,500 and half the page; as a standalone token it occurs
        # exactly where the parcel key prints it. Refusing them outright — which
        # is what this function used to do — silently deleted every single-digit
        # lot, section and unit number in the corpus.
        raw = str(value).strip()
        for i, t in sorted(lines.items()):
            if raw in re.findall(r"[A-Za-z0-9]+", str(t)):
                return i, "verbatim"
        return None, "unanchored"
    for i, t in sorted(lines.items()):
        if v in norm(t):
            return i, "verbatim"
    best, bi = 0.0, None
    for i, t in sorted(lines.items()):
        n = norm(t)
        if not n:
            continue
        r = difflib.SequenceMatcher(None, v, n).ratio()
        # a long line dwarfs a short value, so also try the best window in it
        if len(n) > len(v):
            for j in range(0, len(n) - len(v) + 1, max(1, len(v) // 3)):
                r = max(r, difflib.SequenceMatcher(None, v, n[j:j + len(v)]).ratio())
        if r > best:
            best, bi = r, i
    if best >= 0.70:
        return bi, "corrected"
    return None, "unanchored"


def ask(img, prompt, url, ntok, timeout):
    import base64, urllib.request
    b64 = base64.b64encode(pathlib.Path(img).read_bytes()).decode()
    body = {"model": "qwen", "messages": [{"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url",
                 "image_url": {"url": f"data:image/png;base64,{b64}"}}]}],
            "max_tokens": ntok, "temperature": 0, "cache_prompt": False,
            "chat_template_kwargs": {"enable_thinking": False},
            "reasoning_effort": "none"}
    req = urllib.request.Request(url.rstrip("/") + "/v1/chat/completions",
                                 data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        j = json.load(r)
    ch = j["choices"][0]
    txt = (ch["message"].get("content") or "").strip()
    if txt:
        return txt
    raise RuntimeError(f"empty (finish_reason={ch.get('finish_reason')})")


def compose(doc, claims):
    """claims -> ONE event -> account postings.

    ⚠ A DOCUMENT IS NOT AN EVENT AND THE DIFFERENCE IS THE WHOLE MODEL. Ten pages
    of one mortgage are ten pages of evidence for ONE CAPITAL event on ONE parcel.
    The old output emitted the reel number ten times and called it ten rows.

    ⚠ FUNCTION IS NOT ASSUMED FROM THE REGISTER'S CODE. The register is a PRIOR,
    never a filter — CERT's expected function fires on 2% while three unexpected
    ones fire 27-45%. So function is taken from what the CLAUSES say, via
    lexicon.fire(), and the instrument title is recorded beside it as the prior.
    """
    # ⚠ RANKED ON THREE THINGS, IN ORDER, BECAUSE ONE WAS NOT ENOUGH.
    # in_region first: a value sitting in a region that could honestly carry it
    # beats a better-anchored value that could not. Then anchor quality. Then
    # REGION WEIGHT — the page where that region dominates. p002 carries 13
    # legal_description lines and p008 carries 2, and p008's two are a misrouted
    # recording stamp; weighting by dominance is what separates them, because a
    # gate alone could not (the ROUTER had mislabelled the line, so the gate
    # passed it legitimately).
    best = {}
    for c in claims:
        f = c["field"]
        # ⚠ COMPLETENESS FIRST FOR DATES. `OCT 2 1981` and `1981` are both true;
        # only one is useful, and the shorter one wins on anchor quality because
        # the register stamp never reaches OCR. Count the date parts present.
        dparts = 0
        if c["field"] in ("recording_date", "execution_date"):
            t = str(c["value"])
            dparts = (bool(re.search(r"[A-Za-z]{3,}|\b\d{1,2}[/-]", t))
                      + bool(re.search(r"\b\d{1,2}\b", t))
                      + bool(re.search(r"\b(?:19|20)\d{2}\b", t)))
        rank = (dparts,
                1 if c.get("in_region") else 0,
                {"verbatim": 4, "corrected": 3, "label_anchored": 2,
                 "unanchored": 1}[c["anchor_state"]],
                c.get("region_weight", 0))
        if f not in best or rank > best[f]["_r"]:
            best[f] = {**c, "_r": rank}
    val = {f: c["value"] for f, c in best.items()}

    # ⚠ A TAX LOT THAT EQUALS THIS DOCUMENT'S OWN REEL/PAGE IS NOT A TAX LOT.
    # `BBL=1005860768` was built from block=586 lot=768 — reel 586, page 768.
    # The coincidence is the evidence, and it is checkable without any model.
    # ⚠ EVERY REEL/PAGE VALUE, NOT THE BEST ONE. reel_page is PER PAGE — this
    # document carries 762, 766, 767, 768, 769, 770 — so comparing against a
    # single document-level "best" let `lot=768` through while catching
    # `block=586`. The whole observed set is the discriminator.
    # ⚠ THE PAIR WINS. A parcel key read as one printed unit carries its own
    # evidence that both numbers belong together; two independently-guessed
    # numbers do not, and every wrong lot this document produced was a reel page
    # that looked plausible in isolation.
    pk = next((c["value"] for c in claims if c["field"] == "parcel_key"), None)
    pk_resolved = False
    if pk:
        t = str(pk)
        mb = re.search(r"block\s*[:.#]?\s*(\d{1,5})", t, re.I)
        ml = re.search(r"lots?\s*[:.#]?\s*(\d{1,5})", t, re.I)
        if not (mb and ml):
            # ⚠ BARE PAIR. The model often returns only the numerals it read
            # beside each label, e.g. `883 1`. Block is printed above lot on a
            # backer, so order carries the meaning — but ONLY for exactly two
            # numbers. Three or more is not a parcel key and is refused rather
            # than sliced.
            nums = re.findall(r"\d{1,5}", t)
            if len(nums) == 2:
                val["block"], val["lot"] = nums
                pk_resolved = True
        else:
            val["block"], val["lot"] = mb.group(1), ml.group(1)
            pk_resolved = True
        val["_parcel_key_raw"] = t
        val["_parcel_key_resolved"] = pk_resolved

    stamp = {re.sub(r"\D", "", str(c["value"] or ""))
             for c in claims if c["field"] in ("reel", "reel_page")}
    stamp.discard("")
    for k in ("block", "lot"):
        if pk_resolved:
            break
        d = re.sub(r"\D", "", str(val.get(k) or ""))
        if d and d in stamp:
            val.pop(k, None)
            best.pop(k, None)

    bbl = None
    b = norm(val.get("borough", ""))
    boro = {"manhattan": 1, "newyork": 1, "bronx": 2, "brooklyn": 3, "kings": 3,
            "queens": 4, "statenisland": 5, "richmond": 5}.get(b)
    blk = re.sub(r"\D", "", val.get("block", "") or "")
    lot = re.sub(r"\D", "", val.get("lot", "") or "")
    if boro and blk and lot:
        bbl = f"{boro}{int(blk):05d}{int(lot):04d}"

    ev = {
        "subject": {"type": "parcel", "bbl": bbl,
                    # ⚠ NAMED WHEN INCOMPLETE. A null BBL is a real finding: the
                    # document did not yield one, which is different from absent.
                    "resolved": bool(bbl),
                    # ⚠ AN UNRESOLVED SUBJECT NAMES WHAT IS MISSING. "resolved:
                    # false" alone reads as a shrug; the caller needs to know
                    # whether the borough, the block or the lot never arrived.
                    "missing": [k for k in ("borough", "block", "lot")
                                if not val.get(k)] or None,
                    "borough": val.get("borough"), "block": val.get("block"),
                    "lot": val.get("lot"), "section": val.get("section"),
                    "address": val.get("street_address")},
        "function": None, "function_prior": val.get("instrument_type"),
        "mode": None,
        "date": val.get("execution_date"), "recorded": val.get("recording_date"),
        "participants": [], "quantities": [], "terms": [],
    }
    if not val.get("signer_name"):
        # ⚠ NAMED AS UNREAD. The page was signed; the mark is handwritten and no
        # channel read it. Silence here would read as "unsigned".
        ev["participants"].append(
            {"role": "signatory", "name": None, "type": "person",
             "state": "unread_handwritten",
             "title": val.get("signer_title"),
             "acts_for": val.get("signer_for") or val.get("mortgagor")})
    for f, role in (("mortgagor", "borrower"), ("mortgagee", "lender"),
                    ("signer_name", "signatory"), ("notary_name", "notary")):
        if val.get(f):
            p = {"role": role, "name": val[f], "type": "entity"}
            if f == "signer_name":
                p.update({"type": "person", "title": val.get("signer_title"),
                          "acts_for": val.get("signer_for") or val.get("mortgagor")})
            if f == "mortgagor":
                p["form"] = val.get("mortgagor_form")
            ev["participants"].append(p)
    for f, dim, unit in (("principal_amount", "money", "USD"),
                         ("tax_paid", "money", "USD"),
                         ("taxable_amount", "money", "USD"),
                         ("interest_rate", "rate", "% p.a."),
                         ("term_months", "duration", "months")):
        if val.get(f):
            ev["quantities"].append({"dim": dim, "kind": f, "unit": unit,
                                     "value": val[f],
                                     # ⚠ BOUND TRAVELS. A price from an RETT stamp
                                     # is an UPPER bound, not a reading.
                                     "bound": "exact"})
    # ⚠ ATTACHES_TO IS PART OF THE TERM, NOT DECORATION. The schema fixes it per
    # term: lien_position / cross_collateral / authority do NOT attach to the event.
    # A term on the event applies to everyone; on a participant, to one side only;
    # on the subject, it survives a change of owner. Writing "event" for all of them
    # silently applies one party's obligation to every party.
    ATTACH = {"authority": "participant", "lien_position": "participant",
              "cross_collateral": "subject"}
    for f in TERM_F:
        if val.get(f):
            ev["terms"].append({"term": f, "value": val[f],
                                "attaches_to": ATTACH.get(f, "event")})
    # ⚠ AND AUTHORITY IS ALSO STAMPED ON THE SIGNATORY ITSELF, because that is the
    # participant it qualifies and the tables are read participant-first. The
    # signatory may still be `unread_handwritten` — the PERSON is unread, the
    # CAPACITY is printed and read, and those are two different facts.
    if val.get("authority"):
        for p in ev["participants"]:
            if p.get("role") == "signatory":
                p["authority"] = val["authority"]
    return ev, best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--doc", required=True)
    ap.add_argument("--url", default="http://127.0.0.1:8000")
    ap.add_argument("--model", default="4B-Qwen3-VL-4B-Instruct-Q4_K_M.gguf")
    ap.add_argument("--mmproj", default="4B-mmproj-F16.gguf")
    ap.add_argument("--width", type=int, default=900)   # 1400 hangs the encoder
    ap.add_argument("--ntok", type=int, default=768)
    ap.add_argument("--timeout", type=int, default=170)
    ap.add_argument("--retries", type=int, default=2)
    ap.add_argument("--ngl", type=int, default=99)
    ap.add_argument("--ctx", type=int, default=8192)
    a = ap.parse_args()

    rdir = HERE / "out" / "_route" / a.doc
    routed = sorted(p for p in rdir.glob("p*.json") if ".BEFORE" not in p.name)
    if not routed:
        print(f"  no routed pages under {rdir}")
        return 1
    pgdir = HERE / "pages" / a.doc
    claims, stats = [], collections.Counter()
    fn_hits = collections.Counter()
    mode_hits = collections.Counter()

    print(f"  EXTRACT {a.doc} · {len(routed)} pages -> claim / event / account")
    print(f"  the VLM returns VALUES ONLY; the anchor is searched for here\n")

    for rf in routed:
        r = json.loads(rf.read_text(encoding="utf-8"))
        pg = r["page"]
        lines = {l["i"]: l["text"] for l in r["lines"]}
        boxes = {l["i"]: l.get("box") for l in r["lines"]}

        # ⚠ FUNCTION AND MODE COME FROM THE CLAUSES, not from the filing code.
        page_text = " ".join(lines.values())
        for cl, _off in L.clauses(page_text):
            for f in L.fire(cl, "function"):
                fn_hits[f] += 1
        # ⚠ MODE COMES FROM THE OPERATIVE CLAUSE, NOT A DOCUMENT-WIDE VOTE.
        # Counting every clause let `signals` win a MORTGAGE 5-2. A covenants
        # section is dense with future-conditional language (shall / will /
        # upon) that reads as intent but is the TERMS OF A TRANSACTION that has
        # already happened. Worse, the signals cues were calibrated on BSA
        # APPLICATIONS (97%, 1050/27) — proven on that corpus, never on ACRIS,
        # where the ledger records under 10 hits in 23,282 clauses. A reader
        # proven on one corpus is not proven on another, so its votes are only
        # counted where the page is actually operative.
        for rg in ("granting_clause", "parties"):
            for i in r["placed"].get(rg, []):
                for cl, _off in L.clauses(lines.get(i, "")):
                    for m in L.mode(cl):
                        mode_hits[m] += 1

        want = sorted({f for reg in r["placed"] for f in ASK_ON.get(reg, [])})
        if not want:
            print(f"  {pg}  no field-bearing region — skipped")
            continue
        prompt = (PROMPT_HEAD
                  + "\n".join(f"  {f}: {ALL_F[f]}" for f in want)
                  + "\n\nLINES BY REGION:\n"
                  + "\n".join(f"[{reg}]\n" + "\n".join(
                      f"{i}. {lines.get(i,'')}" for i in sorted(ls))
                      for reg, ls in sorted(r["placed"].items())
                      if reg in ASK_ON))
        img = R.prep(pgdir / f"{pg}.png", a.width)

        raw = None
        for attempt in range(a.retries + 1):
            try:
                raw = ask(img, prompt, a.url, a.ntok, a.timeout)
                break
            except Exception as e:
                if attempt < a.retries:
                    print(f"  {pg}  hang — restarting server", flush=True)
                    if not RT.restart_server(a.model, a.mmproj, a.url, a.ngl, a.ctx):
                        break
                    continue
        if raw is None:
            print(f"  {pg}  ⚠ UNREAD")
            stats["page_unread"] += 1
            continue
        m = re.search(r"\{.*\}", raw, re.S)
        if not m:
            stats["page_no_json"] += 1
            print(f"  {pg}  ⚠ no JSON")
            continue
        try:
            j = json.loads(m.group(0))
        except Exception:
            stats["page_bad_json"] += 1
            print(f"  {pg}  ⚠ bad JSON")
            continue

        got = collections.Counter()
        for field, value in j.items():
            if field not in ALL_F:
                stats["unknown_field"] += 1
                continue
            if not isinstance(value, (str, int, float)) or not str(value).strip():
                stats["empty"] += 1
                continue
            v = str(value).strip()
            nv = norm(v)
            # ⚠ THE MODEL ECHOING MY OWN PROMPT IS NOT EVIDENCE.
            is_zero = bool(re.fullmatch(r"[$]?0*(?:[.,]0*)?", str(v).strip()))
            if (nv in SENTINEL or is_zero) and \
               (not (nv == "0" or is_zero) or field in ZERO_IS_ABSENT):
                stats["sentinel"] += 1
                continue
            if nv == norm(field):
                stats["echoed_field_name"] += 1      # mortgagor: "Mortgagor"
                continue
            # ⚠ STRIP THE EXAMPLE BEFORE COMPARING. A hint that illustrates
            # with a concrete value will otherwise veto that value when it is
            # genuinely on the page — which is exactly how `BLOCK 883 LOT 1`
            # was thrown away.
            hint = re.split(r"\be\.g\.|\bfor example\b|,\s*such as\b",
                            ALL_F[field], 1)[0]
            if nv == norm(hint) or (len(nv) > 3 and nv in norm(hint)):
                stats["echoed_prompt_hint"] += 1
                continue
            ln, st = anchor(value, lines)
            if st == "empty":
                stats["empty"] += 1
                continue
            # ⚠ THE REGION IS RECORDED, AND RANKED ON — IT NO LONGER DELETES.
            # Round 3 gated on the anchored line and dropped `principal_amount`
            # outright because it anchored outside granting_clause/amount. That
            # bought precision with silent recall loss, which is the failure this
            # project keeps re-finding. A guard that discards evidence hides its
            # own cost; a guard that RANKS evidence does not. compose() prefers
            # in-region claims and falls back rather than emitting nothing.
            if not parcel_key_ok(field, lines.get(ln) if ln is not None else ""):
                stats["not_a_parcel_key"] += 1
                continue
            if not printed_name_ok(field, lines.get(ln) if ln is not None else "",
                                   page_text):
                # ⚠ UNREAD, NOT ABSENT. A handwritten signature IS there; we
                # cannot read it, and that is a different fact from "nobody
                # signed". compose() reports it as an unread participant.
                stats["handwritten_unread"] += 1
                continue
            if field == "parcel_key":
                # ⚠ ANCHORED ON ITS LABEL. The value cannot be required to appear
                # in the OCR text because the lot digit is not detected at all —
                # `LOT` is read, the `1` beside it never is. Requiring the page to
                # carry the LABELS keeps this from becoming a free pass: a page
                # with no BLOCK/LOT printed on it cannot yield a parcel key.
                if not re.search(r"\bblock\b", page_text, re.I) or \
                   not re.search(r"\blot\b", page_text, re.I):
                    stats["parcel_key_no_label"] += 1
                    continue
                st = st if st != "unanchored" else "label_anchored"
            elif field == "recording_date" and "recording_stamp" in r["placed"]:
                # ⚠ THE STAMP IS UNREADABLE TO OCR BUT VISIBLE IN THE IMAGE. Only
                # on a page that actually carries a recording stamp, and only if
                # the year is corroborated on the page, so this cannot become a
                # licence to invent a date.
                if not re.search(r"\b(?:19|20)\d{2}\b", page_text):
                    stats["stamp_year_uncorroborated"] += 1
                    continue
                st = st if st != "unanchored" else "label_anchored"
            elif st == "unanchored" and not present_in(v, page_text):
                # ⚠ NOT READ. Kept out of the tables entirely, and counted.
                stats["invented"] += 1
                continue
            reg = next((rg for rg, ls in r["placed"].items()
                        if ln is not None and ln in ls), None)
            gate = SOURCE_GATE.get(field)
            in_region = (gate is None) or (reg in gate)
            if not in_region:
                stats["off_region_kept"] += 1
            stats[st] += 1
            got[st] += 1
            claims.append({"document": a.doc, "page": pg, "field": field,
                           "kind": KIND[field], "value": v,
                           "line": ln, "box": boxes.get(ln) if ln is not None else None,
                           "ocr_line": lines.get(ln) if ln is not None else None,
                           "region": reg, "in_region": in_region,
                           # how strongly this page evidences that region at all
                           "region_weight": len(r["placed"].get(reg, [])) if reg else 0,
                           "anchor_state": st})
        print(f"  {pg}  asked {len(want):>2} · " +
              ("  ".join(f"{k}:{v}" for k, v in got.most_common()) or "nothing"))

    ev, best = compose(a.doc, claims)
    # function/mode from the document's own language
    if fn_hits:
        top = fn_hits.most_common(1)[0][0]
        ev["function"] = L.canon(top) or top.upper()
    # ⚠ ARGMAX OVER RAW HITS LET `signals` WIN ON A MORTGAGE (signals 5 /
    # observes 2 / transacts 2). The ledger records signals as UNREAD — under 10
    # hits in 23,282 clauses, i.e. no corpus — so its count is noise and must not
    # outrank a reader that is proven. Status gates the vote; it does not adjust it.
    ranked = [(n, c) for n, c in mode_hits.most_common()
              if L.MODES.get(n, {}).get("status") != "unread"]
    if ranked:
        ev["mode"] = ranked[0][0]
    ev["mode_rejected_unread"] = {n: c for n, c in mode_hits.items()
                                  if L.MODES.get(n, {}).get("status") == "unread"}
    ev["function_evidence"] = dict(fn_hits.most_common())
    ev["mode_evidence"] = dict(mode_hits.most_common())

    out = HERE / "out" / "_tables"
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{a.doc}.json").write_text(json.dumps(
        {"document": a.doc, "claims": claims, "event": ev,
         "account_posting": {"function": ev["function"],
                             "subject": ev["subject"]["bbl"],
                             "posts": [q for q in ev["quantities"]
                                       if q["kind"] == "principal_amount"]},
         "stats": dict(stats)}, indent=1), encoding="utf-8")
    print(f"\n  {len(claims)} claims · " +
          "  ".join(f"{k}={v}" for k, v in stats.most_common()))
    print(f"  -> {out / (a.doc + '.json')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
