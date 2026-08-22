"""Live feed from the Zoning Resolution itself — zr.planning.nyc.gov.

WHY
    Every FAR the decoder uses had been reaching it through a hand-transcribed
    chart. Transcription cannot carry a footnote, and in the Zoning Resolution
    the footnote IS the regulation: ZR 23-22 lists R6 at 2.20 in its own row and
    again as "R6¹" in the 3.00 row, where footnote 1 reads "For zoning lots, or
    portions thereof, located within 100 feet of a wide street". Flattened to a
    number, R6 becomes either 2.20 or 3.00 and one of them is wrong on every lot.

    So FAR is not a number per district. It is a number per (district,
    condition), and the Resolution is the only source that publishes both.

WHAT THIS DOES
    - resolves a section number to its URL (the ZR numbering is self-describing:
      "23-22" is Article II, Chapter 3; "77-22" is Article VII, Chapter 7)
    - fetches the section, keeps LAST AMENDED, and parses its tables with the
      superscript footnote markers intact
    - caches the PARSED FACTS, never the page. Same discipline as the document
      images: the source stays where it lives, only what it said is kept.
    - re-running detects an amendment, because LAST AMENDED is part of the fact.

USAGE
    python zr_feed.py 23-22              # fetch + show a section's FAR table
    python zr_feed.py --verify           # check the app's table against the ZR
"""
import html, json, pathlib, re, sys, urllib.request
from datetime import date

BASE = "https://zr.planning.nyc.gov"
CACHE = pathlib.Path(__file__).with_name("zr_cache")
ROMAN = {1: "i", 2: "ii", 3: "iii", 4: "iv", 5: "v", 6: "vi", 7: "vii", 8: "viii",
         9: "ix", 10: "x", 11: "xi", 12: "xii", 13: "xiii", 14: "xiv"}

# The sections the decoder actually depends on. Each one is a citation we can
# put on a posting, not just a lookup.
FAR_SECTIONS = {
    "23-22": "residential FAR, R6-R12",
    "23-21": "residential FAR, R1-R5",
    "24-11": "community facility FAR",
    "33-12": "commercial FAR",
    "43-12": "manufacturing FAR",
    "77-22": "FAR on a zoning lot divided by a district boundary",
}


def section_url(sec):
    """'23-22' -> /article-ii/chapter-3/23-22.

    The numbering IS the address, but it is not simply "first digit, second
    digit": the prefix can be two digits or three, and the split moves.

        23-22   -> Article  2, Chapter 3
        95-00   -> Article  9, Chapter 5
        115-21  -> Article 11, Chapter 5     <- three-digit prefix
        121-00  -> Article 12, Chapter 1

    Reading the first two characters as (article, chapter) sends 115-21 to
    Article I Chapter 1, which 404s — every special purpose district lives in
    Articles VIII-XIV and so has a three-digit prefix. That is most of the
    supersession surface, and it was unreachable until this was fixed.
    """
    m = re.match(r"^(\d{2,3})-", sec)
    if not m:
        raise ValueError(f"not a section number: {sec!r}")
    prefix = m.group(1)
    art, chap = (int(prefix[0]), int(prefix[1])) if len(prefix) == 2 \
        else (int(prefix[:2]), int(prefix[2]))
    if art not in ROMAN:
        raise ValueError(f"article out of range in {sec!r}")
    return f"{BASE}/article-{ROMAN[art]}/chapter-{chap}/{sec}"


def _fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "acris-decoder/1.0"})
    with urllib.request.urlopen(req, timeout=90) as f:
        return f.read().decode("utf-8", "ignore")


# A superscript is rarely a bare <sup>1</sup> — the site wraps it in colour
# spans, and the footnote definitions put the padding INSIDE the <sup> too. Both
# must survive as ^N, because a dropped marker silently merges two different
# regulations into one number.
SUP_RE = re.compile(r"<sup\b[^>]*>(.*?)</sup>", re.S | re.I)


def _mark_sups(s):
    def repl(m):
        digits = re.sub(r"<[^>]+>", "", m.group(1))
        digits = re.sub(r"[^\d]", "", html.unescape(digits))
        return f"^{digits}" if digits else " "
    return SUP_RE.sub(repl, s)


def _flat(s):
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"[ \t]+", " ", html.unescape(s).replace("\xa0", " ")).strip()


def _cell_text(cell_html):
    """Cell text with footnote markers preserved as ^N — the whole point."""
    return _flat(_mark_sups(cell_html))


def parse_tables(page):
    out = []
    for t in re.findall(r"<table.*?</table>", page, re.S):
        rows = []
        for r in re.findall(r"<tr.*?</tr>", t, re.S):
            cells = [_cell_text(c) for c in re.findall(r"<t[dh].*?</t[dh]>", r, re.S)]
            if any(cells):
                rows.append(cells)
        if rows:
            out.append(rows)
    return out


def parse_footnotes(page):
    """Footnote definitions: the superscripted paragraphs that follow a table.
    Only paragraphs AFTER the last table are considered, so a marker inside the
    table body is never mistaken for its own definition."""
    notes = {}
    tail = page.rsplit("</table>", 1)[-1] if "</table>" in page else page
    tail = tail.split("Footer Links")[0]
    for m in re.finditer(r"<p\b[^>]*>(.*?)</p>", tail, re.S | re.I):
        txt = _flat(_mark_sups(m.group(1)))
        d = re.match(r"^\^(\d+)\s*(.+)$", txt)
        if d and len(d.group(2)) > 15:
            notes.setdefault(d.group(1), d.group(2).strip(" ."))
    return notes


def fetch_section(sec, refresh=False):
    CACHE.mkdir(exist_ok=True)
    cached = CACHE / f"{sec}.json"
    if cached.exists() and not refresh:
        return json.loads(cached.read_text(encoding="utf-8"))
    url = section_url(sec)
    page = _fetch(url)
    title = re.search(r"<title>(.*?)</title>", page, re.S)
    amended = re.search(r"LAST AMENDED\s*</?[^>]*>?\s*([\d/]{6,10})", page, re.I)
    if not amended:  # the label and the date sit in adjacent block elements
        flat = re.sub(r"<[^>]+>", " ", page)
        amended = re.search(r"LAST AMENDED\s+([\d/]{6,10})", flat, re.I)
    rec = {
        "section": sec, "url": url,
        "title": html.unescape(title.group(1)).strip() if title else None,
        "last_amended": amended.group(1) if amended else None,
        "fetched": date.today().isoformat(),
        "footnotes": parse_footnotes(page),
        "tables": parse_tables(page),
    }
    cached.write_text(json.dumps(rec, indent=1), encoding="utf-8")
    return rec


DIST_RE = re.compile(r"^[RCM]\d+[A-Z]?(?:-\d+[A-Z]?)?(?:/[RCM]\d+[A-Z]?)?$")


def far_rows(rec, table_index=0):
    """A FAR table -> [{district, footnotes, values{column: number}}].

    One row can name several districts, and a superscript on ONE of them binds
    only to that district — which is how R6 carries both 2.20 and 3.00.
    """
    tables = rec.get("tables") or []
    if not tables:
        return []
    rows = tables[table_index]
    # The header is not always row 0: 24-11 opens with a merged spanning row
    # ("Lot coverage") above the real one. Find the row that names the district
    # column instead of assuming a position.
    hi = 0
    for i, r in enumerate(rows[:4]):
        if r and re.match(r"^districts?$", r[0].strip(), re.I):
            hi = i
            break
    header = [c for c in rows[hi]]
    out = []
    for cells in rows[hi + 1:]:
        if len(cells) < 2:
            continue
        names, vals = cells[0], cells[1:]
        nums = []
        for v in vals:
            m = re.match(r"^([\d.]+)(?:\s*\^(\d+))?", v.strip())
            nums.append((float(m.group(1)), m.group(2)) if m else (None, None))
        for tok in re.split(r"[\s,]+", names):
            # markers come as <sup>N</sup> (already ^N) or as bare asterisks
            fn = re.findall(r"\^(\d+)", tok) + (["*"] * tok.count("*"))
            name = re.sub(r"\^\d+|\*+", "", tok).strip()
            if not DIST_RE.match(name):
                continue
            out.append({
                "district": name,
                "footnotes": sorted(set(fn)),
                "values": {header[i + 1] if i + 1 < len(header) else f"col{i+1}": nums[i][0]
                           for i in range(len(nums)) if nums[i][0] is not None},
                "value_footnotes": {header[i + 1] if i + 1 < len(header) else f"col{i+1}": nums[i][1]
                                    for i in range(len(nums)) if nums[i][1]},
            })
    return out


# Which section answers which question. Each is a citation we can put on a
# posting, not just a lookup — and each was read off the live page, not assumed.
FAR_SOURCE = {
    # (use, district family) -> section
    "residential_R": "23-22",       # R6-R12 residential FAR
    "facility_R": "24-11",          # community facility FAR in residence districts
    "commercial_C": "33-122",       # commercial FAR in C1-C8
    "facility_C": "33-123",         # community facility FAR in commercial districts
    "commercial_overlay": "33-121", # commercial FAR under a C1/C2 OVERLAY, keyed by
                                    # the UNDERLYING residence district
    "manufacturing_M": "43-12",     # manufacturing FAR in M districts
    # A-suffix M1 districts (City of Yes). Verbatim: "In M1 Districts with an A
    # suffix, the maximum floor area ratio for ALL PERMITTED USES shall be as set
    # forth in the following table" — so one figure serves manufacturing,
    # commercial and community facility alike. That sentence is why this key can
    # answer three questions from one table; without it, it could answer none.
    "uniform_MA": "43-132",
}


def conditional_far(sec="23-22", refresh=False, all_tables=False):
    """district -> [{far, column, condition}] — every figure the ZR states,
    each carrying the condition under which it applies. Nothing is collapsed."""
    rec = fetch_section(sec, refresh)
    notes = rec.get("footnotes") or {}
    out = {}
    rows = []
    n_tables = len(rec.get("tables") or [])
    for ti in range(n_tables if all_tables else min(1, n_tables)):
        rows.extend(far_rows(rec, ti))
    for row in rows:
        for col, v in list(row["values"].items()):
            fns = set(row["footnotes"]) | ({row["value_footnotes"][col]}
                                           if col in row.get("value_footnotes", {}) else set())
            cond = " AND ".join(notes.get(f, f"footnote {f} (text not parsed)")
                                for f in sorted(fns)) or "unconditional"
            out.setdefault(row["district"], []).append(
                {"far": v, "column": col, "condition": cond,
                 "cite": f"ZR {rec['section']} (last amended {rec['last_amended']})"})
    return out, rec


def zr_far(key, refresh=False):
    """district -> {far, column, condition, cite} for one (use, family) pair,
    straight from the section that governs it.

    Where a section states several figures for a district, the FIRST unconditional
    one is taken and every alternative is carried alongside — the caller decides,
    and can see what it decided against.
    """
    sec = FAR_SOURCE[key]
    table, rec = conditional_far(sec, refresh, all_tables=True)
    out = {}
    for d, entries in table.items():
        uncond = [e for e in entries if e["condition"] == "unconditional"]
        pick = (uncond or entries)[0]
        out[d] = dict(pick, alternatives=[e for e in entries if e is not pick],
                      section=sec, section_title=rec.get("title"),
                      last_amended=rec.get("last_amended"))
    return out, rec


def applies_at(sec, when, refresh=False):
    """Is today's text of a section safe to use for a document dated `when`?

    Verifying floor area on a 2004 instrument against the 2026 Resolution is not
    verification — it measures how much the rules changed. The site's own archive
    of full-ZR versions only reaches back to March 2024, so it cannot answer
    "what did this say in 2004". LAST AMENDED can answer the question that
    matters just as much:

        last amended <= document date   -> today's text IS the text that applied
        last amended >  document date    -> it is NOT, and today's number must
                                             not be used for that date

    The second case is a stated gap, not a silent substitution. Returns
    (safe: bool, detail: str).
    """
    rec = fetch_section(sec, refresh)
    amended = rec.get("last_amended")
    if not amended:
        return False, f"ZR {sec}: no LAST AMENDED date parsed — cannot date the text"
    try:
        m, d, y = [int(x) for x in amended.split("/")]
        amended_iso = f"{y:04d}-{m:02d}-{d:02d}"
    except Exception:
        return False, f"ZR {sec}: unparseable LAST AMENDED {amended!r}"
    when = str(when)[:10]
    if amended_iso <= when:
        return True, (f"ZR {sec} last amended {amended_iso}, on or before {when} — "
                      f"today's text applied at that date")
    return False, (f"ZR {sec} was amended {amended_iso}, AFTER {when} — today's text "
                   f"did NOT apply then; the figure for that date is not established "
                   f"(site archive only reaches 2024-03)")


ARCHIVE = f"{BASE}/zr-downloads"


def archive_vintages():
    """Dated full-ZR versions the site publishes. Only ~2024 onward — the honest
    floor on how far back a text lookup can reach from this source."""
    page = _fetch(ARCHIVE)
    out = []
    for href in sorted(set(re.findall(r'href="(/sites/default/files/[^"]+\.pdf)"', page))):
        m = re.search(r"ZR[_ ](\d{1,2})([A-Za-z]+)(\d{4})", urllib.parse.unquote(href))
        if m:
            out.append({"url": BASE + href, "day": int(m.group(1)),
                        "month": m.group(2), "year": int(m.group(3))})
    return out


def far_columns(sec):
    """The full column headings of a section's tables — a FAR figure means
    nothing without knowing which column it came from (33-121 has three, keyed
    to what the zoning lot contains)."""
    rec = fetch_section(sec)
    return [t[0] if t else [] for t in (rec.get("tables") or [])]


def verify(ref_path=None):
    """Cross-check the transcribed table against the Resolution. Reports three
    kinds of disagreement and repairs nothing."""
    ref_path = pathlib.Path(ref_path or pathlib.Path(__file__).with_name("zoning_reference.json"))
    ref = json.loads(ref_path.read_text(encoding="utf-8"))["districts"]
    zr, rec = conditional_far("23-22")
    print(f"ZR {rec['section']} — {rec['title']}\n  {rec['url']}\n"
          f"  last amended {rec['last_amended']}, fetched {rec['fetched']}\n")
    std = "Standard residences"
    agree = differ = missing = 0
    for d, entries in sorted(zr.items()):
        vals = [e for e in entries if e["column"].startswith(std[:8])]
        if not vals:
            continue
        uncond = [e["far"] for e in vals if e["condition"] == "unconditional"]
        cond = [(e["far"], e["condition"]) for e in vals if e["condition"] != "unconditional"]
        r = ref.get(d)
        if not r:
            print(f"  {d:<8} ZR has it; the reference does not")
            missing += 1
            continue
        rn, rw = r.get("residential_narrow"), r.get("residential_wide")
        zr_narrow = uncond[0] if uncond else (cond[0][0] if cond else None)
        zr_wide = max([v for v, _ in cond] + uncond) if (cond or uncond) else None
        if rn == zr_narrow and rw == zr_wide:
            agree += 1
        else:
            differ += 1
            print(f"  {d:<8} ZR narrow {zr_narrow} / wide {zr_wide}"
                  f"   reference {rn} / {rw}")
            for v, c in cond:
                print(f"           ZR {v} applies: {c[:110]}")
    print(f"\n{agree} agree | {differ} differ | {missing} absent from the reference")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--verify" in sys.argv:
        verify()
    else:
        sec = args[0] if args else "23-22"
        table, rec = conditional_far(sec, refresh="--refresh" in sys.argv)
        print(f"{rec['title']}  ({rec['url']})\n  last amended {rec['last_amended']}\n")
        for d, entries in sorted(table.items()):
            for e in entries:
                print(f"  {d:<8} {e['far']:<7} {e['column'][:34]:<36} {e['condition'][:80]}")
