"""NY Department of State — turning an SPE name into a real party.

WHY THIS IS THE FOURTH DECODER

    ACRIS names "120-22 W 25 STREET LLC". That is a single-purpose entity: no
    address, no human, no phone. DOS holds 4,259,924 entities and 20,832,961
    filings, and for each entity a SERVICE-OF-PROCESS ADDRESS — where the state
    sends a lawsuit. That address is the principal's office or their attorney's,
    which is the rung above the SPE on the contact ladder.

    So the chain becomes:
        parcel -> ACRIS document -> party name -> DOS entity -> address + dates

⚠ THE JOIN IS A NAME, AND NAMES ARE THE WORST JOIN KEY THERE IS

    There is no BBL in DOS and no DOS id in ACRIS. Everything here rests on
    matching a string, so this module is built to REFUSE rather than to guess:

      exact       one entity matches the normalised name           -> usable
      multiple    several match — reported, NEVER silently first   -> look
      none        no match — a real finding (dissolved, foreign,
                  or the name was transcribed wrong)               -> look

    Picking the first of several matches would attach a real company's address
    to the wrong deal, and nothing downstream could detect it.

★ THE SPE NAMING CONVENTION IS A SIGNAL, NOT NOISE

    "120-22 W 25 STREET LLC" is named for the property it holds. So the entity
    name often ENCODES the address, which means:
      * a name can be predicted from an address (find the entity for a parcel)
      * an address can be read from a name (confirm a match is really the deal)
    `address_in_name()` extracts it, and a match whose encoded address disagrees
    with the parcel is a WARNING even when the string matched exactly.

DATASETS (data.ny.gov — NOT the NYC portal; querying the city domain 404s)
    n9v6-gdp6   Active Corporations & entities   4,259,924
    63wc-4exh   Corporation filings              20,832,961
    3gg2-jgnp   Entity status history            20,832,961

⚠⚠ THAT WAS WRONG, AND THE WAY IT WAS WRONG IS THE LESSON — corrected 2026-08-06

    The claim "63wc-4exh carries no entity name or dos_id, only film_num" was
    taken from a TWO-ROW sample. Socrata omits null fields from a row's JSON, so
    a small sample does not show the schema — it shows the fields those
    particular rows happened to populate. Over 5,000 rows:

        63wc-4exh   corp_name    100%   corpid_num  97%   documenttype 100%
                    entitytype   100%   dis_eff_date 1%   juris        64%
        3gg2-jgnp   corpid_num    97%   status      68%

    `corpid_num` IS the dos_id. So the filings ARE joinable, and they are the
    single most valuable table here, because n9v6-gdp6 holds only ACTIVE
    entities while 63wc-4exh holds every filing an entity ever made —
    ARTICLES OF ORGANIZATION (formation) through ARTICLES OF DISSOLUTION,
    SURRENDER OF AUTHORITY and CERTIFICATE OF MERGER (the end).

    A field inventory from a sample under-reports the schema AND reports the
    shortfall as absence — the same shape as every other failure in this
    project: the missing thing looks like a fact about the world.

⚠ NORMALISE FOR COMPARISON, CLASSIFY ON THE RAW STRING

    `normalize()` strips commas and periods. Three separate bugs on 2026-08-06
    came from forgetting that the stripped punctuation is still there on the
    other side of the comparison:

      1. find() sent the NORMALISED name into `upper(current_entity_name)='...'`
         — a normalised needle in a raw haystack. DOS stores "10-12 BOND
         STREET, LLC"; ACRIS says "10-12 BOND STREET LLC". 639 real entities
         reported `none`. Match rate 42.6% -> 79.4% when fixed.
      2. a prefix search built from the normalised name carried the suffix past
         the point where DOS punctuates it ("X, INC.") — zero rows, no error.
      3. a classifier testing `^LAST, FIRST$` ran against a normalised string
         and so matched nothing, reporting "individuals: 0" while a third of
         the names were people.

    None of the three raised. All three returned a plausible smaller number.

★ MEASURED, so it replaces the single-case generalisation above: over 2,423
  (entity, instrument) pairs, formation-to-instrument median is 1,187 days.
  Only 25.9% were formed within a year of the deal and 16.5% within six months.
  Formation date is a REAL but MINORITY marker — it flags about a quarter of
  deals, and the 2009-formed/2010-deal example is one of that quarter, not the
  rule.
"""
import json, re, sys, urllib.parse, urllib.request

DOMAIN = "https://data.ny.gov/resource"
ENTITIES = "n9v6-gdp6"
FILINGS = "63wc-4exh"
STATUS = "3gg2-jgnp"

SUFFIX = re.compile(r"\b(l\.?l\.?c|inc|corp|corporation|company|co|ltd|limited|"
                    r"l\.?p|llp|lllp|plc|pc|assoc(iates)?|holdings?|realty)\b\.?",
                    re.I)


def soql(dataset, **q):
    url = f"{DOMAIN}/{dataset}.json?" + urllib.parse.urlencode(
        {("$" + k if k in ("select", "where", "limit", "offset", "order", "q") else k): v
         for k, v in q.items()})
    with urllib.request.urlopen(url, timeout=180) as f:
        return json.load(f)


def normalize(name):
    """Compare-able form. Deliberately does NOT drop the suffix — 'X LLC' and
    'X INC' are different entities and collapsing them invents matches."""
    if not name:
        return ""
    t = name.upper().strip()
    t = t.replace("&", " AND ")
    t = re.sub(r"[.,'`]", "", t)
    t = re.sub(r"\bL\s*L\s*C\b", "LLC", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip()


def address_in_name(name):
    """The address an SPE encodes in its own name, if any.

    "120-22 W 25 STREET LLC" -> {'numbers': ['120','22'], 'street': '25'}
    Used to CONFIRM a match, never to make one.
    """
    t = normalize(name)
    nums = re.match(r"^(\d+)(?:\s*-\s*(\d+))?\b", t)
    street = re.search(r"\b(\d+)\s*(?:ST|ND|RD|TH)?\s+(?:ST|STREET|AVE|AVENUE|"
                       r"PL|PLACE|RD|ROAD|BLVD)\b", t)
    if not nums and not street:
        return None
    return {"numbers": [g for g in (nums.groups() if nums else []) if g],
            "street": street.group(1) if street else None}


SUFFIX_TAIL = re.compile(r"\s+(LLC|L L C|INC|CORP|CORPORATION|COMPANY|CO|LP|L P|LLP|"
                         r"LLLP|PLLC|PC|LTD|LIMITED|ASSOCIATES|ASSOCIATION|TRUST|"
                         r"HOLDINGS?|REALTY|PARTNERS(HIP)?)$")


def search_prefix(name, floor=6, cap=34):
    """The leading run of a name that DOS cannot have punctuated differently.

    DOS punctuates around the SUFFIX — "X, LLC", "X L.L.C.", "X, L.P." — so a
    prefix search must stop BEFORE it and let the decision be made locally,
    where both sides can be normalised. Returns None when what is left is too
    short to be discriminating, which is a refusal, not a match.
    """
    n = normalize(name)
    p = re.match(r"^[A-Z0-9 &/-]+", n)
    p = (p.group(0) if p else n)[:cap].strip()
    prev = None
    while prev != p:                       # "X HOLDINGS LLC" -> "X"
        prev = p
        p = SUFFIX_TAIL.sub("", p).strip()
    return p if len(p) >= floor else None


def _norm_hits(rows, target, col):
    """Keep only rows whose name normalises to the same string as the target.
    BOTH sides normalised — the whole point."""
    return [r for r in rows if normalize(r.get(col)) == target]


def find(name, limit=25):
    """Look an entity up by name. THREE outcomes, never a silent pick.

    ⚠ Does NOT compare a normalised needle to the raw column (see the module
    docstring). The server narrows by an un-punctuated prefix; equality is
    decided here, normalised on both sides.
    """
    n = normalize(name)
    if not n:
        return {"verdict": "none", "query": name, "matches": []}
    esc = n.replace("'", "''")
    rows = soql(ENTITIES, where=f"upper(current_entity_name)='{esc}'", limit=limit)
    how = "exact"
    if not rows:
        pre = search_prefix(name)
        if pre:
            cand = soql(ENTITIES, limit=200, where=(
                "starts_with(upper(current_entity_name),'"
                + pre.replace("'", "''") + "')"))
            rows = _norm_hits(cand, n, "current_entity_name")
            how = "normalised"
    if not rows:
        # widen ONLY to a prefix; a substring search on 4.26M names returns
        # noise that looks like evidence.
        #
        # ⚠ This exists for a specific, measured reason: the ACRIS party name
        # field CUTS OFF AT 50 CHARACTERS. 69 of 3,987 names on the rights
        # instruments sit exactly at 50 and 50 of them end mid-word
        # ('CHESTNUT COMMONS HOUSING DEVELOPMENT FUND CORPORAT'). Those can
        # never match by equality, on either side, however well normalised —
        # so a prefix is the only instrument that reaches them, and 18 of the
        # 50 resolved to exactly one entity this way.
        pre = search_prefix(name, floor=10, cap=48)
        if pre:
            rows = soql(ENTITIES, limit=limit, where=(
                "starts_with(upper(current_entity_name),'"
                + pre.replace("'", "''") + "')"))
        how = "prefix (ACRIS name may be truncated at 50 chars)"
    if not rows:
        return {"verdict": "none", "query": name, "normalized": n, "matches": []}
    out = [{"dos_id": r.get("dos_id"), "name": r.get("current_entity_name"),
            "type": r.get("entity_type"), "county": r.get("county"),
            "filed": (r.get("initial_dos_filing_date") or "")[:10],
            "jurisdiction": r.get("jurisdiction"),
            "process_name": r.get("dos_process_name"),
            "address": ", ".join(x for x in (r.get("dos_process_address_1"),
                                             r.get("dos_process_city"),
                                             r.get("dos_process_state"),
                                             r.get("dos_process_zip")) if x)}
           for r in rows]
    return {"verdict": "exact" if (how == "exact" and len(out) == 1)
            else ("multiple" if len(out) > 1 else "prefix"),
            "query": name, "normalized": n, "how": how, "matches": out}


def resolve(name, parcel_hint=None):
    """find(), plus a check that the name's own encoded address agrees.

    An exact string match whose encoded street number contradicts the parcel is
    still reported as matched — but FLAGGED, because two different LLCs named
    for two different buildings can normalise to very similar strings.
    """
    r = find(name)
    enc = address_in_name(name)
    r["encoded_address"] = enc
    if enc and parcel_hint:
        hint = normalize(parcel_hint)
        num_ok = any(x and x in hint for x in (enc.get("numbers") or []))
        st_ok = bool(enc.get("street")) and enc["street"] in hint
        if not (num_ok or st_ok):
            r["warning"] = (f"the entity name encodes {enc} which does not appear "
                            f"in the parcel address {parcel_hint!r} — verify")
    return r


def report(names, parcel_hint=None):
    for nm in names:
        r = resolve(nm, parcel_hint)
        print(f"\n  {nm}")
        print(f"    verdict: {r['verdict']}" +
              (f"  (matched by {r.get('how')})" if r.get("how") else ""))
        if r.get("encoded_address"):
            print(f"    name encodes address: {r['encoded_address']}")
        if r.get("warning"):
            print(f"    ⚠ {r['warning']}")
        for m in r["matches"][:4]:
            print(f"      dos_id {m['dos_id']}  {m['name']}")
            print(f"         {m['type']} · {m['county']} · filed {m['filed']}")
            print(f"         service: {m['address']}")
            if m.get("process_name") and normalize(m["process_name"]) != normalize(m["name"]):
                print(f"         ⭐ process to: {m['process_name']}  <- a NAMED "
                      f"party, not the SPE")
        if len(r["matches"]) > 4:
            print(f"      ... and {len(r['matches'])-4} more — NOT auto-selected")


# ── The filings table: the entity's own lifecycle ───────────────────────────
# These are the DOCUMENTS this decoder cites. Not property documents — none of
# them names a parcel — but each is a filed instrument with a microfilm number,
# so a fact taken from one can be walked back exactly like an ACRIS page.

FORMATION = re.compile(r"ARTICLES OF ORGANIZATION|CERTIFICATE OF INCORPORATION|"
                       r"ARTICLES OF INCORPORATION", re.I)
AUTHORITY = re.compile(r"APPLICATION (OF|FOR) AUTHORITY", re.I)
ENDING = re.compile(r"DISSOL|ANNUL|SURRENDER|TERMINAT|CANCEL|MERGER|CONSOLIDAT", re.I)


def filings_for(names, chunk=20, cap=5000):
    """Every filing whose corp_name normalises to one of `names`.

    Narrowed server-side by suffix-free prefixes, decided locally with both
    sides normalised. Reports the chunks that hit `cap`, because a capped chunk
    means some of its names are UNDER-FOUND and that must not be read as
    "this entity filed nothing".
    """
    want = {}
    for n in names:
        want.setdefault(normalize(n), []).append(n)
    pre = {}
    for k in want:
        p = search_prefix(k)
        if p:
            pre.setdefault(p, []).append(k)
    unreachable = [k for k in want if not search_prefix(k)]
    out = {}
    still_capped = []

    def pull(part, depth=0):
        """⚠ A chunk that comes back holding exactly `cap` rows is TRUNCATED,
        and the names in it are under-found — which reads as 'this entity filed
        nothing'. Subdivide until it fits rather than warning about it; a
        warning is a thing to remember, and this project's rule is to enforce.
        A single prefix that still caps is genuinely too broad and is reported.
        """
        clause = " OR ".join("starts_with(upper(corp_name),'"
                             + p.replace("'", "''") + "')" for p in part)
        rows = soql(FILINGS, where=clause, limit=cap)
        if len(rows) >= cap:
            if len(part) == 1 or depth > 6:
                still_capped.append(part[0])
            else:
                mid = len(part) // 2
                pull(part[:mid], depth + 1)
                pull(part[mid:], depth + 1)
                return
        for r in rows:
            k = normalize(r.get("corp_name"))
            if k in want:
                out.setdefault(k, []).append(r)

    keys = sorted(pre)
    for i in range(0, len(keys), chunk):
        pull(keys[i:i + chunk])
    return {"filings": out, "capped_chunks": len(still_capped),
            "capped_prefixes": still_capped, "unreachable": unreachable,
            "asked": len(want), "found": len(out)}


def lifecycle(rows):
    """One entity's filings -> its birth, its authority, and its end.

    An SPE's END is the interesting half: n9v6-gdp6 holds only ACTIVE entities,
    so an SPE that wound up after its deal is INVISIBLE there and reads as
    'no such company'. Here it reads as 'dissolved on a date' — which is not a
    failed lookup, it is the deal closing out.
    """
    rows = sorted(rows, key=lambda r: (r.get("date_filed") or ""))
    born = next((r for r in rows if FORMATION.search(r.get("documenttype") or "")), None)
    auth = next((r for r in rows if AUTHORITY.search(r.get("documenttype") or "")), None)
    ends = [r for r in rows if ENDING.search(r.get("documenttype") or "")]
    return {
        "dos_id": next((r.get("corpid_num") for r in rows if r.get("corpid_num")), None),
        "dos_name": next((r.get("corp_name") for r in rows if r.get("corp_name")), None),
        "entity_type": next((r.get("entitytype") for r in rows if r.get("entitytype")), None),
        "formed": ((born or auth or {}).get("date_filed") or "")[:10] or None,
        "formed_doc": (born or auth or {}).get("documenttype"),
        "formed_film": (born or auth or {}).get("film_num"),
        "formed_is_authority": born is None and auth is not None,
        "ended": ((ends[-1] if ends else {}).get("date_filed") or "")[:10] or None,
        "ended_doc": (ends[-1] if ends else {}).get("documenttype"),
        "ended_film": (ends[-1] if ends else {}).get("film_num"),
        "filings": len(rows)}


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if args:
        report(args)
    else:
        # the real parties from 2010102601040006, decoded 2026-08-06
        report(["120-22 W 25 STREET LLC", "124-26 W 25 STREET LLC",
                "112-118 WEST 25TH LLC"], parcel_hint="120 WEST 25 STREET")
