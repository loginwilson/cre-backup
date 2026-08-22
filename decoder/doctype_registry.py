"""THE FULL ACRIS DOC-TYPE REGISTRY — one specialist per type, every type routed.

⚠ THE POINT: NO DOCUMENT MAY EVER FALL THROUGH TO A GENERALIST.

A generalist reads front to back because it does not know what the instrument
contains. That is what cost ~2.7M tokens and 862 page-reads on one parcel, at
~10,200 tokens per claim. A specialist opens six pages and checks a list.

Every ACRIS type resolves to exactly one specialist here. Types that share a
grammar share a specialist — a satisfaction and a termination are the same
shape of instrument (something is being released; find WHAT, and what
SURVIVES) even though ACRIS names them differently.

⚠ EACH SPECIALIST HAS A TIER, AND THE TIER IS A BUDGET.

  SIGNAL   read properly. These carry money, floor area, or burdens that
           run with the land. ~8-14 pages.
  CHAIN    read the cover and the schedule. These move something that
           already exists. ~3-5 pages. ⚠ Four assignments on lot 49 ran
           29 pages and produced ZERO facts — that is a MEASURED result,
           and it is why this tier exists.
  STAMP    the cover page IS the document. 1-2 pages. A tax-return-only
           filing on lot 49 had "Document Page Count: 0" and its two tax
           stamps still yielded a $2,300,000 conveyance nothing else recorded.
  RARE     no measured priors yet. Read it properly ONCE, then it graduates
           into a specialist with real priors. ⚠ NEVER SKIP ON THE LABEL —
           'SAGE' and 'SUNDRY MISCELLANEOUS' on this parcel hid a Marriott
           franchise ROFR and an environmental cleanup covenant that no
           mortgage in 35 years mentions.
"""

SIGNAL, CHAIN, STAMP, RARE = "SIGNAL", "CHAIN", "STAMP", "RARE"

# ---------------------------------------------------------------------------
# ACRIS type code -> (specialist, tier, what it actually is)
# Grouped by ACRIS's own document classes.
# ---------------------------------------------------------------------------
REGISTRY = {

# ---- DEEDS AND OTHER CONVEYANCES ----------------------------------------
"DEED":      ("DEED",   SIGNAL, "deed"),
"DEEDO":     ("DEED",   SIGNAL, "deed, other"),
"CORRD":     ("DEED",   SIGNAL, "correction deed — ⚠ says what was WRONG"),
"RDEED":     ("DEED",   SIGNAL, "referee's deed — a foreclosure completed"),
"DEEDP":     ("DEED",   SIGNAL, "deed, partial"),
"CONDEED":   ("DEED",   SIGNAL, "condemnation deed — a taking"),
"EXCHDEED":  ("DEED",   SIGNAL, "1031 exchange deed"),
"MASTERDEED":("DECL",   SIGNAL, "condominium declaration / master deed"),
"CONFDEED":  ("DEED",   SIGNAL, "confirmatory deed — ⚠ cures a defect"),

# ---- LEASEHOLDS -----------------------------------------------------------
"LEAS":      ("LEASE",  SIGNAL, "memorandum of lease"),
"MLEA":      ("LEASE",  SIGNAL, "memorandum of lease"),
"ASSTM":     ("LEASE",  SIGNAL, "assignment of lease"),
"SUBLEAS":   ("LEASE",  SIGNAL, "sublease"),
"TERML":     ("RELEASE", CHAIN, "termination of lease"),
"LEASMOD":   ("LEASE",  SIGNAL, "lease modification"),

# ---- MORTGAGES ------------------------------------------------------------
"MTGE":      ("MTGE",   SIGNAL, "mortgage"),
"MMTG":      ("MTGE",   SIGNAL, "master / multiple-parcel mortgage"),
"BLDG":      ("MTGE",   SIGNAL, "building loan mortgage — a real build"),
"PROJ":      ("MTGE",   SIGNAL, "project loan mortgage"),
"AGMT":      ("CEMA",   SIGNAL, "⚠ 'AGREEMENT' — usually a full CEMA"),
"CEMA":      ("CEMA",   SIGNAL, "consolidation, extension, modification"),
"SPRD":      ("CEMA",   SIGNAL, "spreader — ⚠ verify it truly spreads"),
"MODA":      ("CEMA",   SIGNAL, "modification agreement"),
"SUBM":      ("SUBORD", SIGNAL, "subordination of mortgage"),
"WSUB":      ("SUBORD", SIGNAL, "waiver and subordination"),

# ---- MORTGAGE MOVEMENT (chain) -------------------------------------------
"ASST":      ("ASST",   CHAIN,  "assignment of mortgage"),
"ASPM":      ("ASST",   CHAIN,  "assignment, partial"),
"ASGN":      ("ASST",   CHAIN,  "assignment"),
"SAT":       ("RELEASE", CHAIN, "satisfaction of mortgage"),
"PSAT":      ("RELEASE", CHAIN, "partial satisfaction"),
"RELEASE":   ("RELEASE", CHAIN, "release of mortgage / of parcel"),
"DISC":      ("RELEASE", CHAIN, "discharge"),

# ---- RENTS AND INCOME -----------------------------------------------------
"AL&R":      ("ALR",    SIGNAL, "assignment of leases and rents"),
"ALR":       ("ALR",    SIGNAL, "assignment of leases and rents"),
"ASGN L&R":  ("ALR",    SIGNAL, "assignment of leases and rents"),
"TL&R":      ("RELEASE", CHAIN, "termination of assignment of leases/rents"),
"AALR":      ("ASST",   CHAIN,  "assignment OF an assignment of L&R"),

# ---- DEVELOPMENT RIGHTS AND ZONING ---------------------------------------
"DEVR":      ("ZLDA",   SIGNAL, "⚠ DEVELOPMENT RIGHTS — the priced transfer"),
"AIRRIGHT":  ("ZLDA",   SIGNAL, "air rights"),
"ZLDA":      ("ZLDA",   SIGNAL, "zoning lot development & easement agreement"),
"ZONE":      ("DECL",   SIGNAL, "zoning lot declaration"),
"DECL":      ("DECL",   SIGNAL, "declaration of restrictions"),
"EASE":      ("EASE",   SIGNAL, "easement"),
"PARTYWALL": ("EASE",   SIGNAL, "party wall agreement"),
"RESTR":     ("DECL",   SIGNAL, "restrictive covenant"),

# ---- TAX FORMS — THE COVER *IS* THE DOCUMENT ------------------------------
"RPTT&RET":  ("STAMP",  STAMP,  "⚠ transfer tax return — price lives here"),
"RPTT":      ("STAMP",  STAMP,  "NYC real property transfer tax return"),
"RETT":      ("STAMP",  STAMP,  "NYS real estate transfer tax return"),
"RP-5217":   ("STAMP",  STAMP,  "⚠ prints Full Sale Price outright"),
"SMOKE":     ("STAMP",  STAMP,  "smoke detector affidavit — no substance"),

# ---- LIENS, DISTRESS, LITIGATION -----------------------------------------
"LIS":       ("DISTRESS", SIGNAL, "⚠ lis pendens — litigation on title"),
"NOTICE":    ("DISTRESS", SIGNAL, "notice of pendency"),
"FEDLIEN":   ("DISTRESS", SIGNAL, "federal tax lien"),
"LIEN":      ("DISTRESS", SIGNAL, "lien"),
"MECHLIEN":  ("DISTRESS", SIGNAL, "⚠ mechanic's lien — construction unpaid"),
"JUDG":      ("DISTRESS", SIGNAL, "judgment"),
"BKRT":      ("DISTRESS", SIGNAL, "bankruptcy"),
"DISLIEN":   ("RELEASE", CHAIN,  "discharge of lien"),

# ---- UCC ------------------------------------------------------------------
"UCC1":      ("UCC",    CHAIN,  "UCC financing statement — fixtures"),
"UCC3":      ("UCC",    CHAIN,  "UCC amendment / continuation / termination"),
"UCC5":      ("UCC",    CHAIN,  "UCC correction"),

# ---- THE JUNK BUCKET THAT ISN'T ------------------------------------------
"SAGE":      ("SAGE",   RARE,   "⚠ sundry agreement — NEVER skip on label"),
"SMIS":      ("SAGE",   RARE,   "⚠ sundry miscellaneous — the REAL code"),
"SMISC":     ("SAGE",   RARE,   "⚠ sundry miscellaneous (variant)"),
"CERT":      ("DECL",   SIGNAL, "title-company certification of parties in "
                                "interest — names every owner and mortgagee "
                                "on a zoning lot, and whether each SIGNED or "
                                "WAIVED"),
"AALR":      ("ASST",   CHAIN,  "assignment OF an assignment of leases/rents"),
"ZONE":      ("DECL",   SIGNAL, "zoning lot description / declaration"),
"MISC":      ("SAGE",   RARE,   "⚠ miscellaneous"),
"AGREE":     ("SAGE",   RARE,   "agreement, unclassified"),
"POA":       ("SAGE",   RARE,   "power of attorney"),
"CONSENT":   ("SAGE",   RARE,   "consent"),
"WAIVER":    ("SUBORD", SIGNAL, "waiver"),
"MEMO":      ("SAGE",   RARE,   "⚠ memorandum — gives notice, states no terms"),
}

# specialists that exist with measured priors (see specialists.py)
BUILT = {"MTGE", "CEMA", "ZLDA", "DEED", "ASST", "SAGE"}

# specialists still to build, in the order the corpus will demand them
TODO = ["ALR", "RELEASE", "STAMP", "DECL", "SUBORD", "LEASE", "EASE",
        "DISTRESS", "UCC"]

TIER_BUDGET = {SIGNAL: 10, CHAIN: 4, STAMP: 2, RARE: 8}


def route(acris_type):
    """Every type resolves. ⚠ Unknown types go to RARE, never to 'skip'."""
    t = (acris_type or "").strip().upper()
    if t in REGISTRY:
        return REGISTRY[t]
    for k, v in REGISTRY.items():          # prefix match for variants
        if t.startswith(k) or k.startswith(t):
            return v
    # ⚠ AN UNRECOGNISED TYPE IS THE MOST DANGEROUS KIND, NOT THE SAFEST.
    # It is unrecognised because nobody has decoded one yet.
    return ("SAGE", RARE, f"⚠ UNKNOWN TYPE '{t}' — read it properly once")


def report():
    import collections
    by_spec = collections.defaultdict(list)
    by_tier = collections.Counter()
    for t, (spec, tier, _) in REGISTRY.items():
        by_spec[spec].append(t)
        by_tier[tier] += 1
    print(f"ACRIS DOC-TYPE REGISTRY · {len(REGISTRY)} types -> "
          f"{len(by_spec)} specialists\n")
    print("  specialist   types  tier budget  status")
    for spec in sorted(by_spec, key=lambda s: -len(by_spec[s])):
        tiers = {REGISTRY[t][1] for t in by_spec[spec]}
        bud = min(TIER_BUDGET[x] for x in tiers)
        mark = "BUILT" if spec in BUILT else "⚠ TO BUILD"
        print(f"  {spec:<12} {len(by_spec[spec]):>5}  {bud:>10}  {mark}")
    print()
    for tier in (SIGNAL, CHAIN, STAMP, RARE):
        print(f"  {tier:<8} {by_tier[tier]:>3} types · "
              f"{TIER_BUDGET[tier]:>2} pages each")
    print()
    gen = sum(40 for _ in REGISTRY)
    spec = sum(TIER_BUDGET[REGISTRY[t][1]] for t in REGISTRY)
    print(f"  ⚠ one document of every type, read by a GENERALIST at 40 pages: "
          f"{gen:,} pages")
    print(f"    the same set, routed to specialists:                        "
          f"{spec:,} pages")
    print(f"    {100*(1-spec/gen):.0f}% fewer page-reads · at ~3,100 tokens a "
          f"page that is ~{(gen-spec)*3100/1e6:.1f}M tokens")


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    report()
