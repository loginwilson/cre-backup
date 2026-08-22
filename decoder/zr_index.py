"""A full index of the Zoning Resolution — every section, so nothing modifies an
envelope without us knowing the section exists.

WHY
    Three times now a FAR has been wrong because a MODIFIER was not consulted,
    and each time it was found only because something forced a look:
      * street width  — ZR 23-22 footnote 1, "within 100 feet of a wide street";
        R6 is 2.20 or 3.00 depending on it
      * special district — ZR 115-21, Downtown Jamaica lifts C6-3 commercial FAR
        from 6.0 to 8.0; the citywide answer was understated 14% with no error
      * uniform-FAR districts — ZR 43-132, "all permitted uses" in an A-suffix M1
    Finding modifiers by tripping over them is not a method. The Resolution is
    finite: index it once, then ASK it which sections bear on a question.

WHAT THIS BUILDS
    zr_index.json — every section number, title, article, chapter and URL, with a
    flag for whether the title implies it touches floor area or bulk. That is an
    index of WHERE TO LOOK, not a store of rules: the rules still come from
    reading the section (zr_feed), so nothing here can silently go stale into a
    wrong number. A stale index costs a missed section, and the coverage report
    says how many there are.

USAGE
    python zr_index.py --build          crawl and cache (~1 request/second)
    python zr_index.py floor area       search titles
    python zr_index.py --modifiers      every section that can change an envelope
"""
import html, json, pathlib, re, sys, time, urllib.request

BASE = "https://zr.planning.nyc.gov"
CACHE = pathlib.Path(__file__).with_name("zr_index.json")
ARTICLES = ["i", "ii", "iii", "iv", "v", "vi", "vii", "viii",
            "ix", "x", "xi", "xii", "xiii", "xiv"]

# Title patterns that mean "this section can change how much may be built, or
# where". Deliberately broad — a false positive costs one read, a false negative
# costs a wrong number that looks right.
MODIFIER_PATTERNS = [
    (r"floor area", "floor_area"),
    (r"\bFAR\b", "floor_area"),
    (r"lot coverage|open space|yard|court\b", "bulk"),
    (r"height|setback|sky exposure|sliver", "bulk"),
    (r"density|dwelling unit|room count", "density"),
    (r"inclusionary|affordable|MIH|UAP|senior housing", "affordability"),
    (r"transfer|development rights|air space|landmark", "transfer"),
    (r"bonus|additional floor area|plaza|transit", "bonus"),
    (r"non-conforming|non-complying|vested|lapse", "grandfathering"),
    (r"quality housing|contextual", "program"),
    (r"street|block|frontage|waterfront|corner", "geometry"),
    (r"special .*district|applicab", "supersession"),
]


def _get(url, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "acris-decoder/1.0"})
            return urllib.request.urlopen(req, timeout=90).read().decode("utf-8", "ignore")
        except Exception:
            if i == tries - 1:
                return ""
            time.sleep(1.5 * (i + 1))
    return ""


def _clean(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def chapters_of(article):
    page = _get(f"{BASE}/article-{article}")
    return sorted({m for m in re.findall(rf"/article-{article}/chapter-(\d+)", page)},
                  key=int)


def sections_of(article, chapter):
    """Section number -> title, from the chapter's own listing."""
    page = _get(f"{BASE}/article-{article}/chapter-{chapter}")
    out = {}
    # links to sections carry the number in the href and the title beside them
    for m in re.finditer(rf'href="(/article-{article}/chapter-{chapter}/'
                         rf'([\d]{{2,3}}-[\d]{{2,3}}))"[^>]*>(.*?)</a>', page, re.S):
        num, title = m.group(2), _clean(m.group(3))
        if title and not re.fullmatch(r"[\d\-]+", title):
            out[num] = title
    # fall back to the flat "115-21 Floor Area Ratio" listing style
    if not out:
        flat = _clean(page)
        for num, title in re.findall(r"\b(\d{2,3}-\d{2,3})\s+([A-Z][A-Za-z' ,\-]{3,70})", flat):
            out.setdefault(num, title.strip())
    return out


def classify(title):
    tags = set()
    for pat, tag in MODIFIER_PATTERNS:
        if re.search(pat, title, re.I):
            tags.add(tag)
    return sorted(tags)


def build():
    index, n_ch = {}, 0
    for art in ARTICLES:
        chs = chapters_of(art)
        print(f"  article {art:<5} {len(chs):>3} chapters", flush=True)
        for ch in chs:
            n_ch += 1
            for num, title in sections_of(art, ch).items():
                index[num] = {
                    "section": num, "title": title, "article": art, "chapter": ch,
                    "url": f"{BASE}/article-{art}/chapter-{ch}/{num}",
                    "tags": classify(title)}
            time.sleep(0.3)
    CACHE.write_text(json.dumps(index, indent=1), encoding="utf-8")
    tagged = [s for s in index.values() if s["tags"]]
    print(f"\n{len(index)} sections across {n_ch} chapters -> {CACHE.name}")
    print(f"{len(tagged)} carry an envelope-relevant tag")
    counts = {}
    for s in tagged:
        for t in s["tags"]:
            counts[t] = counts.get(t, 0) + 1
    for t, c in sorted(counts.items(), key=lambda kv: -kv[1]):
        print(f"   {t:<16} {c}")
    return index


def load():
    if not CACHE.exists():
        raise SystemExit("no index yet — run: python zr_index.py --build")
    return json.loads(CACHE.read_text(encoding="utf-8"))


def search(term, index=None):
    index = index or load()
    t = term.lower()
    return [s for s in index.values() if t in s["title"].lower() or t in s["section"]]


if __name__ == "__main__":
    if "--build" in sys.argv:
        build()
    elif "--modifiers" in sys.argv:
        idx = load()
        want = sys.argv[sys.argv.index("--modifiers") + 1:] or None
        rows = [s for s in idx.values()
                if s["tags"] and (not want or set(want) & set(s["tags"]))]
        for s in sorted(rows, key=lambda s: (s["article"], int(s["chapter"]), s["section"])):
            print(f"  {s['section']:<9} {s['title'][:62]:<64} {','.join(s['tags'])}")
        print(f"\n{len(rows)} sections")
    else:
        for s in search(" ".join(sys.argv[1:]) or "floor area"):
            print(f"  {s['section']:<9} {s['title'][:66]:<68} {','.join(s['tags'])}")
