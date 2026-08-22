"""THE AGENT REGISTRY — one agent per document type, across every source.

Two halves, and they are different jobs:

    EXTRACT   an agent per document type. It knows one form's geometry and
              traps and nothing else. Writes claims.
    RESOLVE   an agent per function. It reads claims from EVERY source and
              settles them. Never opens a document.

⚠ THE MEASURED FINDING THAT SHAPES ALL OF THIS: on the pilot parcel, NOT ONE
FUNCTION WAS FED BY A SINGLE DOCUMENT TYPE. ENCUMBER drew from nine types,
IDENTIFY from fifteen. And the type named after a function is usually not
its main feeder — ENCUMBER's biggest source was MTGE, not EASE; VALUE's was
DEVR, not DEED. So a resolver can never be pointed at a document type. It is
pointed at a query.

⚠ CONFIDENCE IS MARKED AND IT MATTERS.

    MEASURED   page priors and traps derived from documents actually
               decoded. Trust the budget.
    DECLARED   written from knowledge of the form, never yet measured
               against a real read. ⚠ THE BUDGET IS A GUESS. First run
               reads generously and REPORTS where facts actually sat, and
               the entry graduates to MEASURED.

A DECLARED agent that reports its budget was wrong has done its job. One
that silently reads to the budget and misses half the form has not.

    python agents.py             the full registry
    python agents.py --gaps      what is declared but never measured
    python agents.py --source X  one source
"""
import collections
import sys

MEASURED, DECLARED = "MEASURED", "DECLARED"

# ---------------------------------------------------------------------------
# source · doc type · agent · pages · confidence · functions it feeds
# ---------------------------------------------------------------------------
AGENTS = [

# ===== ACRIS — 69 types routed to 15 agents. See doctype_registry.py =======
("ACRIS", "DEED · DEEDO · CORRD · RDEED",       "acris.deed",     6, MEASURED,
 ["TITLE", "VALUE", "PARCEL", "CONSENT"],
 "⚠ price is NEVER in the grant. The recital says $10 against $42.7M of "
 "stamps. Three witnesses must agree: RPTT/2.625%, RETT/0.4%, RP-5217."),

("ACRIS", "MTGE · BLDG · PROJ · MMTG",          "acris.mtge",    10, MEASURED,
 ["DEBT", "ENCUMBER", "PRIORITY", "INCOME", "OBLIGATION"],
 "⚠ face amounts are NOT additive across a chain; stated outstanding "
 "balances are. Exemption 255 means no new money — find the companion gap."),

("ACRIS", "AGMT · CEMA · SPRD · MODA",          "acris.cema",    10, MEASURED,
 ["DEBT", "PRIORITY", "ENCUMBER"],
 "⚠ the new-money split is usually HANDWRITTEN in the margin; the typed "
 "text states only the consolidated total. No OCR reaches it."),

("ACRIS", "DEVR · AIRRIGHT · ZLDA",             "acris.zlda",    14, MEASURED,
 ["ENVELOPE", "VALUE", "ENCUMBER", "CONSENT"],
 "⚠ the price is deliberately off-record — a Memorandum states no price and "
 "a prepared Termination erases the notice. THE TAX STAMP IS THE ONLY "
 "WITNESS. And 'light, air AND VIEW' — the third word gets dropped."),

("ACRIS", "AL&R · ALR",                         "acris.alr",      8, MEASURED,
 ["INCOME", "ENCUMBER", "TENANCY"],
 "⚠ ABSOLUTE or COLLATERAL changes everything and one instrument here uses "
 "neither word — read the licence-back structurally."),

("ACRIS", "ASST · ASPM · AALR",                 "acris.asst",     4, MEASURED,
 ["DEBT", "PARTY"],
 "⚠ mostly empty — 29 pages produced zero terms once. But consideration "
 "EQUALS the outstanding balance, which is the number that matters."),

("ACRIS", "SAT · PSAT · TL&R · TERML · RELEASE", "acris.release", 4, MEASURED,
 ["DEBT", "INCOME", "ENCUMBER"],
 "⚠ READ WHAT IS ACTUALLY RELEASED. One instrument cancelled only an "
 "assignment of leases; the $1,000,000 mortgage beneath it lived 26 more "
 "years inside today's lien."),

("ACRIS", "ZONE · DECL · RESTR · CERT",         "acris.decl",     8, MEASURED,
 ["ENVELOPE", "CONSENT", "PARCEL"],
 "⚠ a declaration MERGES lots and carries NO floor area — ten of them ran "
 "122 pages and yielded zero square feet. Only a ZLDA moves rights."),

("ACRIS", "EASE · PARTYWALL",                   "acris.ease",     8, MEASURED,
 ["ENCUMBER", "ENVELOPE", "PARCEL"],
 "⚠ a limiting plane is named from the estate being described. Record which "
 "VOLUME was conveyed, never which adjective was used."),

("ACRIS", "SUBM · WSUB · WAIVER",               "acris.subord",   6, MEASURED,
 ["CONSENT", "PRIORITY", "ENCUMBER"],
 "⚠ 'only if and for so long as' is REVERSIBLE. Enumerate every condition; "
 "one here depends on an unrecorded franchise agreement."),

("ACRIS", "RPTT&RET · RPTT · RETT · RP-5217",   "acris.stamp",    2, MEASURED,
 ["VALUE", "TITLE"],
 "⚠ THE COVER IS THE DOCUMENT. 'Page Count: 0' is valid and one such filing "
 "carried a $2,300,000 conveyance recorded nowhere else. $0/$0 on both "
 "stamps is a POSITIVE finding: commonly-controlled, no price exists."),

("ACRIS", "LEAS · MLEA · ASSTM · SUBLEAS",      "acris.lease",    6, DECLARED,
 ["TENANCY", "TITLE", "OCCUPY"],
 "⚠ a memorandum records that a lease exists and none of its terms. The "
 "only trace of an operating tenancy may be inside a lender's collateral "
 "assignment."),

("ACRIS", "LIS · MECHLIEN · FEDLIEN · JUDG",    "acris.distress", 6, DECLARED,
 ["DISTRESS", "TITLE"],
 "⚠ a discharge is a SEPARATE later document — always look for the release "
 "before reporting the lien. A mechanic's lien dates when work stopped "
 "being paid for, which no permit feed gives you."),

("ACRIS", "UCC1 · UCC3 · UCC5",                 "acris.ucc",      3, DECLARED,
 ["DEBT"],
 "⚠ lapses after five years unless continued — a live one dates a lender "
 "relationship, a lapsed one dates its end."),

("ACRIS", "SAGE · SMIS · MISC · MEMO · POA",    "acris.sundry",   8, MEASURED,
 ["ENCUMBER", "CONSENT", "TENANCY", "INTEGRITY"],
 "⚠ NEVER SKIP THIS TYPE ON ITS LABEL. On one parcel the junk bucket held a "
 "Marriott franchise ROFR, an environmental cleanup covenant no mortgage "
 "mentions, and the instrument naming how fee title was conveyed."),

# ===== DOB BIS — scanned forms ============================================
("DOB_BIS", "PW1  plan/work application",       "bis.pw1",       10, DECLARED,
 ["PERMIT", "PARTY", "ENTITLE", "ASBUILT"],
 "⚠ §9F carries CPC approval numbers that appear in NO feed. §26 (the "
 "developer's phone) is only in the PDF — the rendered page throws before "
 "it. Reading documents over pages took one dataset 48% -> 95%."),

("DOB_BIS", "ZD1  zoning diagram",              "bis.zd1",        6, DECLARED,
 ["ENVELOPE", "PARCEL"],
 "★ THE CANARY. This is the developer's OWN computation of buildable area, "
 "signed by an RA and accepted by DOB. Compare it to your resolved ENVELOPE "
 "on every job that filed one — disagreement is the finding."),

("DOB_BIS", "PW2  permit",                      "bis.pw2",        4, DECLARED,
 ["PERMIT"],
 "⚠ work start is the first permit for the SCOPE WORK, not mobilisation. A "
 "fence permit is pre-development."),

("DOB_BIS", "PW3  cost affidavit",              "bis.pw3",        3, DECLARED,
 ["COST", "PERMIT"],
 "⚠ the only public construction cost per job, and it is a filing figure "
 "not an actual — treat as a floor."),

("DOB_BIS", "PAA  post-approval amendment",     "bis.paa",        6, DECLARED,
 ["PERMIT", "ENVELOPE"],
 "⚠ doc numbers DO NOT sort by date and the same number is scanned "
 "repeatedly. §4A states which document it amends — that is the only "
 "reliable ordering."),

("DOB_BIS", "TR1 · TR8  technical reports",     "bis.tr",         4, DECLARED,
 ["PERMIT", "ASBUILT"],
 "special inspections — evidence work actually proceeded."),

("DOB_BIS", "CO   certificate of occupancy",    "bis.co",         4, DECLARED,
 ["ASBUILT", "OCCUPY"],
 "⚠ the join needs the '-I1' suffix STRIPPED or it returns zero. Anything "
 "not 'Final' is a TCO. Only ~19% of scope-bearing jobs ever produce one."),

# ===== DOB NOW — portal ===================================================
("DOB_NOW", "job filing",                       "now.job",        4, DECLARED,
 ["PERMIT", "PARTY"],
 "⚠ NO zoning columns at all — DOB NOW cannot answer ENVELOPE. And a ROW IS "
 "NOT A JOB: doc 01 and its amendments are separate rows."),

("DOB_NOW", "approved permit",                  "now.permit",     3, DECLARED,
 ["PERMIT"],
 "⚠ there is no 'Temporary' filing type despite what the docs imply."),

# ===== DOF ================================================================
("DOF", "sales file",                           "dof.sales",      2, DECLARED,
 ["VALUE"],
 "⚠ starts 2016 — that is the data's edge, not the market's. Pre-2016 "
 "comes from ACRIS + PLUTO archive. And DOF drops condo land sales when a "
 "land lot becomes a billing lot."),

("DOF", "assessment roll",                      "dof.assess",     2, DECLARED,
 ["VALUE", "PARCEL"],
 "assessed value history — lags the market and is not a price."),

("DOF", "RPIE income & expense",                "dof.rpie",       6, DECLARED,
 ["OCCUPY", "VALUE"],
 "⚠ THE ONLY PUBLIC INCOME FIGURE. Every ACRIS assignment pledges the rents "
 "and none of them states one."),

("DOF", "tax lien sale",                        "dof.lien",       2, DECLARED,
 ["DISTRESS"],
 "arrears severe enough to be sold — a hard distress signal."),

# ===== HPD ================================================================
("HPD", "registration",                         "hpd.reg",        3, DECLARED,
 ["PARTY", "OCCUPY"],
 "⚠ names a MANAGING AGENT and an owner contact — often the only natural "
 "person behind an SPE."),

("HPD", "violation",                            "hpd.viol",       2, DECLARED,
 ["DISTRESS", "ASBUILT"],
 "class C violations date real conditions."),

# ===== ENTITLEMENT BODIES =================================================
("BSA", "variance / special permit",            "bsa.cal",        8, DECLARED,
 ["ENTITLE", "ENVELOPE"],
 "⚠ an EXPIRY IS A DATED OPPORTUNITY. A lapsed variance changes what the "
 "site is worth."),

("DCP", "ULURP / ZAP action",                   "dcp.zap",        6, DECLARED,
 ["ENTITLE", "ENVELOPE"],
 "CPC approvals — recorded in the PW1 and in All Comments, nowhere in a "
 "feed."),

("DCP", "zoning district (nyzd)",               "dcp.zone",       1, DECLARED,
 ["ENVELOPE"],
 "⚠ SPLIT-DISTRICT LOTS NEED ZR 77-22 — computed per district portion, "
 "never averaged. FAR is per-use in the same district."),

("LPC", "landmark / historic district",         "lpc.desig",      3, DECLARED,
 ["ENTITLE", "ENCUMBER"],
 "designation constrains the envelope in ways zoning does not show."),

("DEC", "wetlands / E-designation",             "dec.env",        2, DECLARED,
 ["PARCEL", "ENCUMBER"],
 "⚠ an environmental restriction may also arrive via ACRIS as a recorded "
 "covenant — cross-check."),
]


def main():
    args = sys.argv[1:]
    rows = AGENTS
    if "--source" in args:
        s = args[args.index("--source") + 1].upper()
        rows = [r for r in AGENTS if r[0] == s]

    if "--gaps" in args:
        dec = [r for r in AGENTS if r[4] == DECLARED]
        print(f"DECLARED BUT NEVER MEASURED — {len(dec)} agents\n")
        print("  ⚠ their page budgets are GUESSES. First run reads generously")
        print("    and reports where facts actually sat.\n")
        for src, dt, name, pg, _, fns, note in dec:
            print(f"  {name:<16} {src:<8} budget {pg:>2}pp   {dt}")
        return

    print(f"AGENT REGISTRY · {len(AGENTS)} extract agents across "
          f"{len({r[0] for r in AGENTS})} sources\n")
    cur = None
    for src, dt, name, pg, conf, fns, note in rows:
        if src != cur:
            print(f"\n── {src}")
            cur = src
        mark = "✓" if conf == MEASURED else "⚠"
        print(f"  {mark} {name:<16} {pg:>2}pp  {dt}")
        print(f"      → {' · '.join(fns)}")

    print("\n" + "=" * 68)
    m = sum(1 for r in AGENTS if r[4] == MEASURED)
    print(f"  MEASURED {m}   ⚠ DECLARED {len(AGENTS)-m}   "
          f"(budgets unproven)")
    fn = collections.Counter(f for r in AGENTS for f in r[5])
    print(f"\n  EVERY FUNCTION IS FED BY MANY AGENTS — that is the whole point:")
    for f, n in fn.most_common():
        srcs = len({r[0] for r in AGENTS if f in r[5]})
        print(f"    {f:<10} {n:>2} agents across {srcs} source(s)")
    print("\n  ⚠ A RESOLVER IS NEVER POINTED AT A DOCUMENT TYPE.")
    print("    It queries claims by function and gets all of these at once.")


main()
