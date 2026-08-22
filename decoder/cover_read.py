"""THE COVER PAGE READER — every field the City Register prints, bound to a value.

    python cover_read.py                     # read + self-grade the DEVR set
    python cover_read.py --dir devr_pages --limit 25
    from cover_read import read_cover

⚠ WHY THIS IS SEPARATE FROM cover_fields.py. That file proved the METHOD — bind
label to value by POSITION, because the cover is a two-column table and reading
order interleaves the columns. It read two fields. The completeness pass on
2026-08-14 showed the same page also prints both BBLs, the property types, both
parties with their mailing addresses, the presenter, the return-to, three
distinct dates and the page count — at 25/25 — and that NOTHING in the system
read any of them. This file reads the page; that one was the proof it could be.

⚠ TWO READING MODES, AND MIXING THEM IS THE ORIGINAL DEFECT.
    SPATIAL  the FEES AND TAXES block. Two columns interleave in reading order,
             so flat text puts "County (Basic)" next to the RETT figure. Bind by
             x/y or bind wrong.
    FLAT     everything above it. PROPERTY DATA and PARTIES are full-width rows
             that survive linearisation, and reading them spatially would add a
             geometry dependency for no gain.
Choosing per-field is deliberate. A single mode would be wrong for half the page.

⚠ THE THREE DEFECTS THIS FIXES, ALL MEASURED, NONE GUESSED:

  1. "Real Property Transfer Tax" MATCHES INSIDE "Real Property Transfer Tax
     Filing Fee". cover_fields.py reported rptt=$25.00 on document
     2003013001838001 — the FILING FEE, with the tax itself exempt. $25 read as
     the tax implies a $952 sale. It is not a small error and it does not look
     like one: 33 of 150 documents "bound a stamp" and the value was the fee.

  2. MONEY REQUIRED A DECIMAL POINT OCR HAD EATEN. `^[\\d,]+\\.\\d\\d$` rejects
     "6,26200", which is how $6,262.00 prints when the point is lost. THREE of
     the EIGHT non-zero stamps in the DEVR sample are in that state — a price
     reader that ignores it silently loses 37% of the money.

  3. THE PROPERTY TABLE CAN CONTINUE ON PAGE 2. "Additional Properties on
     Continuation Page" is printed when it does. Counting lots from page 1 alone
     reports a floor as if it were the total, and for a rights transfer the lot
     count IS the sender/receiver structure.

⚠ THE REPAIR IS STRUCTURAL AND IT IS RECORDED. "6,26200" is resolved by the
COMMA, not by what would make a check pass: a comma group is three digits, five
follow it, so the last two are cents. That decision is made before any
cross-check runs and `money_repaired` is carried on the row. Never repair a
number to make a check agree — repair it because the notation says so, then let
the check disagree if it wants to.

⚠ AND IT STILL GRADES ITSELF ON EVIDENCE IT DID NOT PRODUCE:
    the printed Document ID must equal the directory name on disk
    RPTT / 2.625% must equal RETT / 0.400%, computed independently
    Document Page Count + cover pages must equal the pages actually on disk
No labelling, at any scale.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import pathlib
import re
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).parent

from cover_fields import words, RPTT_RATE, RETT_RATE

# ── money, including the form OCR mangles ───────────────────────────────────
# ⚠ THE SECOND ALTERNATIVE IS THE WHOLE POINT. "6,26200" is a real printed
# amount whose decimal point did not survive scanning; requiring the point is
# how it became invisible.
MONEY_CLEAN = re.compile(r"^\$?\s*([\d,]+\.\d{2})$")
MONEY_MANGLED = re.compile(r"^\$?\s*(\d{1,3}(?:,\d{3})+)(\d{2})$")


def money(tok):
    """(value, repaired) or (None, False). Never guesses — the comma decides."""
    t = tok.strip().strip("|!sSiI$ ")
    m = MONEY_CLEAN.match(t)
    if m:
        try:
            return float(m.group(1).replace(",", "")), False
        except ValueError:
            return None, False
    m = MONEY_MANGLED.match(t)
    if m:
        # "6,262" + "00" -> 6262.00. The comma group fixes where the point went.
        try:
            return float(m.group(1).replace(",", "") + "." + m.group(2)), True
        except ValueError:
            return None, False
    return None, False


def find_phrase(ws, phrase, not_followed_by=()):
    """Locate a label; return the box of its LAST word.

    ⚠ `not_followed_by` IS LOAD-BEARING, NOT DEFENSIVE. Without it
    "Real Property Transfer Tax" matches the prefix of "Real Property Transfer
    Tax Filing Fee" and binds the $25 fee as the tax.
    """
    parts = phrase.upper().split()
    bad = {b.upper() for b in not_followed_by}

    # ⚠ STRIP EVERY NON-ALPHANUMERIC, NOT A CHOSEN SET. Tesseract emits the
    # cover's label as "‘RETURN" — a scan artifact read as an opening quote.
    # A strip list of ":|$.," leaves it, the phrase never matches, and
    # PRESENTER/RETURN TO drop from 25/25 on the page to 9/25 in the output.
    # The list of characters a scanner can hallucinate is not enumerable.
    def norm(s):
        return re.sub(r"[^A-Z0-9]", "", s.upper())

    parts = [norm(p) for p in parts]
    bad = {norm(b) for b in bad}
    for i in range(len(ws) - len(parts) + 1):
        if not all(norm(ws[i + k]["t"]) == parts[k] for k in range(len(parts))):
            continue
        tail = [norm(ws[j]["t"])
                for j in range(i + len(parts), min(i + len(parts) + 2, len(ws)))]
        if bad & set(tail):
            continue
        return ws[i + len(parts) - 1]
    return None


def value_near(ws, label, maxdy=2.2):
    """⚠ AT OR BELOW THE LABEL, NEVER ABOVE — the fix for a 250x error.

    MEASURED on this layout, three documents, y in pixels:

        NYS/NYC Real Property Transfer Tax Filing Fee:   label y=2392
                                            $ 25.00     value y=2454   (+62)
        NYS Real Estate Transfer Tax:                    label y=2490
                                            $ 6,262.00   value y=2526   (+36)

    Every value sits BELOW its own label. The first version allowed dy >= -h,
    so the RETT label reached UP 36px and bound the FILING FEE — producing
    rett=$25.00 on three documents, a $6,250 "price" for a $1.5M transfer. It
    looked like a successful bind, which is why it survived a coverage count.

    The x >= label.x test stays: it is what keeps the reader out of the left
    column, where the mortgage-tax zeros sit.
    """
    if not label:
        return None
    best = None
    for w in ws:
        v, rep = money(w["t"])
        if v is None:
            continue
        dy = w["y"] - label["y"]
        # a quarter line of jitter for baseline wobble, and not one pixel more
        if dy < -0.25 * label["h"] or dy > maxdy * label["h"] or w["x"] < label["x"]:
            continue
        d = (abs(dy), w["x"] - label["x"])
        if best is None or d < best[0]:
            best = (d, w, v, rep)
    return best[1:] if best else None


# ── column blocks: PRESENTER | RETURN TO, PARTY ONE | PARTY TWO ─────────────
def column_split(ws, y0, y1):
    """The x where the page's two columns divide, MEASURED per band.

    ⚠ NOT THE PAGE MIDPOINT, AND NOT THE MIDPOINT OF THE TWO LABELS. Measured on
    2003013001838001: PRESENTER sits at x=237 and RETURN TO at x=1321, so their
    midpoint is 779 — but the left column's own text runs out to x=864
    ("FIRST AMERICAN NEW YORK OFFICE"), which that split would hand to the right
    column and attribute the presenter's address to the return-to. The real
    divider is the widest vertical gutter, and it is empty by construction.
    """
    xs = sorted(w["x"] for w in ws if y0 <= w["y"] <= y1)
    if len(xs) < 4:
        return None
    span = max(xs) - min(xs)
    lo, hi = min(xs) + 0.25 * span, min(xs) + 0.8 * span
    gap = (0, None)
    for a, b in zip(xs, xs[1:]):
        if lo <= a <= hi and b - a > gap[0]:
            gap = (b - a, (a + b) / 2)
    return gap[1]


def block(ws, label, y1, side, split):
    """Words under `label`, on its side of the gutter, in reading order."""
    if not label or split is None:
        return None
    sel = [w for w in ws
           if label["y"] - 0.5 * label["h"] <= w["y"] < y1
           and ((w["x"] < split) if side == "left" else (w["x"] >= split))
           and w["c"] > 30 and w is not label]
    sel.sort(key=lambda w: (round(w["y"] / max(label["h"], 1)), w["x"]))
    txt = " ".join(w["t"] for w in sel)
    # ⚠ find_phrase RETURNS ONLY THE LAST WORD OF A LABEL, so "PARTY" is still
    # loose in the block when the anchor was "ONE"/"TWO" — every party name came
    # back prefixed "PARTY 691 EIGHTH AVENUE CORPORATION". Strip the label words
    # themselves, repeatedly, along with the scan noise that precedes them.
    for _ in range(4):
        n = re.sub(r"^[^A-Za-z0-9]*(?:PRESENTER|RETURN|TO|PARTY|ONE|TWO)\b[:\s]*",
                   "", txt, flags=re.I)
        if n == txt:
            break
        txt = n
    return _clean(txt) or None


# ── flat-text fields (full-width rows — linearisation-safe) ─────────────────
BORO = r"MANHATTAN|BRONX|BROOKLYN|QUEENS|STATEN\s*ISLAND"
# ⚠ THE LOT IS OPTIONAL AND THAT IS NOT SLOPPINESS. On 2003021400219004 OCR ate
# the second lot number ("MANHATTAN 1277 Entire Lot"). Requiring both numbers
# drops that row silently; making it optional records a lot we KNOW is missing,
# which is a fact the resolver can act on.
PROP = re.compile(rf"\b({BORO})\b[^\dA-Za-z]{{0,4}}(\d{{1,5}})(?:\s+(\d{{1,5}}))?", re.I)
# ⚠ EVERY FIELD ON THIS PAGE NEEDS AN EXPLICIT TERMINATOR. The cover has no
# blank lines once linearised, so a greedy class runs straight into the next
# section: "OFFICE BUILDING" came back as "OFFICE BUILDING CROSSREFERENCEDATA
# CRFN ." and the document type as "DEC OF DEVELOPMENT RIGHTS D" — the D being
# the start of "Document Page Count". A trailing fragment does not look like a
# failure, it looks like a slightly odd value, which is how it survives review.
SECTION = (r"(?=CROSS|PARTIES|PARTY\s*ONE|Borough|Additional\s*Propert|"
           r"FEES\s*AND|Document|Property\s*Type|$)")
PTYPE = re.compile(r"Property\s*Type\s*:?\s*([A-Z0-9][A-Z0-9 /\-,&\.]{2,44}?)\s*"
                   + SECTION)
CONT = re.compile(r"Additional\s*Propert(?:y|ies)\s*on\s*Continuation", re.I)
DOCTYPE = re.compile(r"Document\s*Type\s*:?\s*([A-Z][A-Z /&\-]{4,44}?)\s*"
                     r"(?=Document|PRESENTER|RETURN|PROPERTY|$)")
PAGECOUNT = re.compile(r"Document\s*Page\s*Count\s*:?\s*(\d{1,4})", re.I)
PAGEOF = re.compile(r"PAGE\s*(\d+)\s*[O0]F\s*(\d+)", re.I)
DOCID = re.compile(r"Document\s*ID\s*:?\s*(\d{16})", re.I)
D_DOC = re.compile(r"Document\s*Date\s*:?\s*(\d{2}-\d{2}-\d{4})", re.I)
D_PREP = re.compile(r"Preparation\s*Date\s*:?\s*(\d{2}-\d{2}-\d{4})", re.I)
D_REC = re.compile(r"Recorded/?\s*Filed\s*(\d{2}-\d{2}-\d{4})", re.I)
CRFN = re.compile(r"(?:CRFN\)?\s*:?|File\s*No\.?\s*\(CRFN\)\s*:?)\s*(\d{13})", re.I)
# ⚠ PRESENTER / RETURN TO / PARTY ONE / PARTY TWO HAVE NO FLAT-TEXT PATTERN HERE
# ON PURPOSE — they are read spatially by block(), below. They are COLUMN HEADS,
# so linearisation emits "PARTIES PARTY ONE: PARTYTWO: 691EIGHTHAVENUE..." with
# both labels ahead of either name. The obvious regex — PARTY ONE:(.*?)PARTY TWO
# — therefore captures the empty string on a page where both names are printed
# in full. Measured: 1 of 25 flat, 25 of 25 spatial.
#
# ⚠ AND PARTY ONE / PARTY TWO ARE THE ONLY INDEPENDENT WITNESS TO THE party_type
# CONVENTION. The index encodes the side as 1/2 and never says which is which;
# role inversion is the one defect transcription scoring cannot see. Checked
# 2026-08-14 against the ACRIS PARTIES index (636b-3b5g): 13 documents testable,
# 13 agree that cover PARTY ONE == party_type 1, ZERO inverted. The other 12 are
# the 2003070100714xxx batch, where the index lists several names under each
# type so a token test cannot discriminate — ambiguous, not disagreeing.


def _clean(s):
    return " ".join((s or "").split())[:200]


def read_cover(doc_dir, flat_text=""):
    """Every cover-page field this document supports. Never raises on a bad page."""
    doc_dir = pathlib.Path(doc_dir)
    p1 = doc_dir / "p001.tif"
    t = flat_text or ""
    r = {"doc": doc_dir.name}

    # ── flat-text fields ────────────────────────────────────────────────────
    # ⚠ EVERY FLAT FIELD CARRIES ITS SPAN, BECAUSE THE CLAIM LAYER WILL DEMAND
    # ONE. claim_read.py's rule is absolute — "a claim carries a span and the
    # text at those offsets is re-read and compared byte-for-byte" — and a field
    # that arrives without offsets cannot be promoted without weakening that
    # rule for everything else. Recording them here costs nothing; retrofitting
    # them later means re-deriving the value and hoping it lands the same way.
    r["_span"] = {}
    lots, seen = [], set()
    for m in PROP.finditer(t):
        key = (m.group(1).upper().replace(" ", ""), m.group(2), m.group(3))
        if key in seen:
            continue
        seen.add(key)
        lots.append({"borough": key[0], "block": key[1], "lot": key[2],
                     "lot_missing": key[2] is None,
                     "span": [m.start(), m.end()], "quote": m.group(0)})
    r["lots"] = lots
    r["lot_count"] = len(lots)
    r["lots_continue"] = bool(CONT.search(t))
    r["property_types"] = [_clean(x.group(1)) for x in PTYPE.finditer(t)][:8]
    for k, rx in (("doc_type", DOCTYPE), ("page_count", PAGECOUNT),
                  ("read_id", DOCID), ("document_date", D_DOC),
                  ("preparation_date", D_PREP), ("recorded_date", D_REC),
                  ("crfn", CRFN)):
        m = rx.search(t)
        r[k] = _clean(m.group(1)) if m else None
        if m:
            r["_span"][k] = [m.start(1), m.end(1)]
    m = PAGEOF.search(t)
    r["page_of"] = [int(m.group(1)), int(m.group(2))] if m else None

    # ── spatial fields ──────────────────────────────────────────────────────
    r["rptt"] = r["rett"] = None
    r["money_repaired"] = False
    r["established_by"] = None
    r["presenter"] = r["return_to"] = r["party_one"] = r["party_two"] = None
    r["spatial"] = p1.exists()
    if p1.exists():
        ws = words(p1)
        # ⚠ THE DOCUMENT ID COMES FROM THE WORD BOXES, NOT THE FLAT TEXT.
        # Measured: reading it from PaddleOCR's linearised page matched the
        # directory name 18/25; the same field off Tesseract's tokens is 145/150.
        # The cover page is clean modern print and the engines are not equal on it.
        sid = next((w["t"] for w in ws if re.fullmatch(r"\d{16}", w["t"])), None)
        if sid:
            r["read_id"] = sid
        # ⚠ THE PAGE'S OWN CRFN IS ORPHANED BY LINEARISATION. It prints as
        # "City Register File No.(CRFN):" in the right column with the number
        # below it, and the left column's "TOTAL: $0.00" lands between them —
        # which is why a flat-text regex found it on 0 of 25.
        cr = next((w for w in ws
                   if re.fullmatch(r"20\d{11}", w["t"]) and w["c"] > 50), None)
        if cr:
            r["crfn"] = cr["t"]
            # ⚠ BOX, NOT SPAN — and without it the field is read but unclaimable.
            # First wiring emitted CRFN only when the FLAT regex had found it,
            # which is never (0/25), so all 19 spatial reads were silently
            # dropped at the claim layer while the reader reported them bound.
            r["crfn_box"] = [cr["x"], cr["y"], cr["w"], cr["h"]]

        # ⚠ "Filing"/"Fee" EXCLUDED — that line is the $25 filing fee, not the tax.
        rp = value_near(ws, find_phrase(ws, "Real Property Transfer Tax",
                                        not_followed_by=("FILING", "FEE")))
        rt = value_near(ws, find_phrase(ws, "Real Estate Transfer Tax"))
        # ⚠ THE BOX IS THE SPATIAL ANALOGUE OF A SPAN, AND IT IS WHAT MAKES A
        # SPATIALLY-BOUND VALUE CHECKABLE. There is no character offset to quote
        # — the value was chosen by POSITION — so provenance is (page, box,
        # token) and verification re-runs the word boxes and asks whether that
        # token is still at that box. A cover claim without one would be the
        # only value in the system asserting itself on trust.
        if rp:
            r["rptt"], r["rptt_conf"] = rp[1], rp[0]["c"]
            r["rptt_box"] = [rp[0]["x"], rp[0]["y"], rp[0]["w"], rp[0]["h"]]
            r["rptt_quote"] = rp[0]["t"]
            r["money_repaired"] |= rp[2]
        if rt:
            r["rett"], r["rett_conf"] = rt[1], rt[0]["c"]
            r["rett_box"] = [rt[0]["x"], rt[0]["y"], rt[0]["w"], rt[0]["h"]]
            r["rett_quote"] = rt[0]["t"]
            r["money_repaired"] |= rt[2]
            r["established_by"] = "tesseract_spatial"

        # ── the two-column blocks ───────────────────────────────────────────
        pres = find_phrase(ws, "PRESENTER")
        ret = find_phrase(ws, "RETURN TO")
        pdata = find_phrase(ws, "PROPERTY DATA") or find_phrase(ws, "PROPERTYDATA")
        if pres and ret:
            y1 = pdata["y"] if pdata and pdata["y"] > pres["y"] else pres["y"] + 500
            s = column_split(ws, pres["y"], y1)
            r["presenter"] = block(ws, pres, y1, "left", s)
            r["return_to"] = block(ws, ret, y1, "right", s)
        # ⚠ PARTY ONE / PARTY TWO CANNOT BE READ FLAT AND THIS IS WHY. The
        # linearised page reads "PARTIES PARTY ONE: PARTYTWO: 691EIGHTH..." —
        # both LABELS arrive before either NAME, because they are column heads.
        # Any regex of the form "PARTY ONE:(.*?)PARTY TWO" captures the empty
        # string, which is exactly what happened: 1 of 25.
        p1l = find_phrase(ws, "PARTY ONE")
        p2l = find_phrase(ws, "PARTY TWO")
        fees = find_phrase(ws, "FEES AND TAXES") or find_phrase(ws, "FEESANDTAXES")
        if p1l and p2l:
            y1 = fees["y"] if fees and fees["y"] > p1l["y"] else p1l["y"] + 400
            s = column_split(ws, p1l["y"], y1)
            r["party_one"] = block(ws, p1l, y1, "left", s)
            r["party_two"] = block(ws, p2l, y1, "right", s)

    # ⚠ SECOND CHANNEL, CONSULTED ONLY WHEN THE FIRST PRODUCED NO PARSEABLE
    # TOKEN — never to override it. Tesseract read "626200" (comma lost, so the
    # decimal point is UNRECOVERABLE — 6262.00 and 626200.00 are equally
    # consistent, and guessing here would be inventing a price). PaddleOCR read
    # the same figure as "6,26200", where the comma group fixes where the point
    # belongs. Neither engine is better; they fail on different characters, which
    # is the same argument that put two channels on the body text.
    if r["rett"] is None:
        m = re.search(r"NYS\s*Real\s*Estate\s*Transfer\s*Tax(.{0,180})", t,
                      re.I | re.S)
        if m:
            cands = []
            for x in re.finditer(r"\d{1,3}(?:,\d{3})+(?:\d{2}|\.\d{2})?", m.group(1)):
                v, rep = money(x.group(0))
                if v:
                    cands.append((v, rep))
            if len(cands) == 1:
                r["rett"], rep = cands[0]
                r["money_repaired"] |= rep
                r["established_by"] = "paddle_flat"

    # ⚠ CONSIDERATION IS DERIVED FROM A TAX, AND IS LABELLED AS SUCH. It is not
    # a figure anyone printed. RETT rounds UP to the next $500, so this is a
    # bound, not a reading, and calling it "price" would hide that.
    r["consideration_from"] = None
    if r["rett"]:
        r["consideration"] = round(r["rett"] / RETT_RATE, 2)
        r["consideration_from"] = "rett"
    elif r["rptt"]:
        r["consideration"] = round(r["rptt"] / RPTT_RATE, 2)
        r["consideration_from"] = "rptt"
    else:
        # ⚠ THREE STATES, NEVER TWO — matches event_quantity.presence. A stamp
        # printed as 0.00 means no taxable consideration; an unread page means
        # nothing at all. Collapsing them makes every sum built on it wrong.
        r["consideration"] = None
        r["presence"] = "absent_by_nature" if r["spatial"] else "unread"
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="devr_pages")
    ap.add_argument("--text", default="devr_text")
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()

    flat = {}
    for f in (HERE / a.text).glob("*.json"):
        rec = json.loads(f.read_text(encoding="utf-8"))
        for pg in rec.get("pages") or []:
            if str(pg.get("page")).lstrip("p0") == "1":
                flat[rec.get("doc_id", f.stem)] = pg.get("accepted_text") or ""

    docs = sorted(d for d in (HERE / a.dir).iterdir()
                  if d.is_dir() and (d / "p001.tif").exists() and d.name in flat)
    if a.limit:
        docs = docs[:a.limit]
    t0 = time.time()
    with cf.ThreadPoolExecutor(12) as ex:
        rows = list(ex.map(lambda d: read_cover(d, flat.get(d.name, "")), docs))
    el = time.time() - t0

    n = len(rows)
    print(f"COVER READER — {n} documents in {el:.0f}s "
          f"({n/max(el,1e-9)*3600:,.0f} pg/hr)\n")

    def pct(k, f):
        c = sum(1 for r in rows if f(r))
        print(f"    {k:<34}{c:>4}/{n}")

    print("  FIELDS BOUND")
    pct("both BBLs (sender + receiver)", lambda r: r["lot_count"] >= 2)
    pct("any BBL", lambda r: r["lot_count"] >= 1)
    pct("⚠ lots continue on page 2", lambda r: r["lots_continue"])
    pct("property type", lambda r: bool(r["property_types"]))
    pct("document type", lambda r: bool(r["doc_type"]))
    pct("document date (executed)", lambda r: bool(r["document_date"]))
    pct("recorded date", lambda r: bool(r["recorded_date"]))
    pct("own CRFN", lambda r: bool(r["crfn"]))
    pct("presenter", lambda r: bool(r["presenter"]))
    pct("return to", lambda r: bool(r["return_to"]))
    pct("party one + party two", lambda r: r["party_one"] and r["party_two"])
    pct("a transfer-tax stamp", lambda r: r["rptt"] or r["rett"])
    pct("  of which decimal was repaired", lambda r: r["money_repaired"])

    # ── grade 1: the page grades itself against the filesystem ──────────────
    ok = sum(1 for r in rows if r["read_id"] == r["doc"])
    print(f"\n  GRADE 1  printed Document ID == directory name   {ok}/{n}")

    # ── grade 2: two stamps, computed independently ────────────────────────
    both = [r for r in rows if r["rptt"] and r["rett"]]
    agree = sum(1 for r in both
                if abs(r["rptt"]/RPTT_RATE - r["rett"]/RETT_RATE)
                / max(r["rptt"]/RPTT_RATE, r["rett"]/RETT_RATE) < 0.01)
    print(f"  GRADE 2  RPTT/2.625% == RETT/0.400%              "
          f"{agree}/{len(both)} of {len(both)} with both")

    # ── grade 3: printed page count vs pages on disk ───────────────────────
    g3 = g3n = 0
    for r in rows:
        d = HERE / a.dir / r["doc"]
        disk = len(list(d.glob("p*.tif")))
        if not r["page_count"] or not r["page_of"]:
            continue
        g3n += 1
        # cover pages = total printed - document pages
        if int(r["page_count"]) + (r["page_of"][1] - int(r["page_count"])) == disk:
            g3 += 1
    print(f"  GRADE 3  page count + cover == pages on disk      {g3}/{g3n}")

    print(f"\n  CONSIDERATION RECOVERED (derived from the stamp, not printed)")
    got = [r for r in rows if r.get("consideration")]
    for r in sorted(got, key=lambda r: -r["consideration"]):
        flag = " ⚠repaired" if r["money_repaired"] else ""
        print(f"    {r['doc']}  {r['consideration_from']}={r['rett'] or r['rptt']:>10,.2f}"
              f"  ->  ${r['consideration']:>14,.2f}{flag}")
    print(f"    {len(got)}/{n} with a price · "
          f"{sum(1 for r in rows if r.get('presence')=='absent_by_nature')}/{n} "
          f"stamped zero (absent_by_nature)")

    out = HERE / "_cover_read.json"
    out.write_text(json.dumps(rows, indent=1), encoding="utf-8")
    print(f"\n  -> {out.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
