"""THE LEXICON — one definition of what language means, read by every tool.

    from lexicon import FUNCTIONS, REGIONS, REFERENCES, fire, clauses

⚠ THIS FILE EXISTS BECAUSE THE DEFINITIONS WERE IN FIVE PLACES AND HAD ALREADY
DRIFTED. phrase_propose.py, claim_read.py, rot_compare.py and v6_probe.py each
carried their own copy, and two of them disagreed about what a clause even IS:
one split on [.;:\n], severing "Mortgage Amount:" from "$ 50,000.00" so every
cover-page trigger was unfireable, while the other kept the colon and reported
9 hits on the same text. Two tools disagreeing about a clause boundary will
disagree about everything downstream, silently.

⚠ THREE KINDS, NEVER MIXED. Login, 2026-08-14: "cover page isnt a function."
Correct, and it matters — a region that leaks into event.functions[] would put a
meaningless function on every document in the corpus.

    FUNCTION   what CHANGED     -> may become event.functions[]
    REGION     where to LOOK    -> routes extraction, never an event
    REFERENCE  what it POINTS AT-> identifies, never changes

The test is the charter's: "If nothing changes, there is no function and no
event — change is what makes a function apply." ACRIS wraps every document in a
cover page and it changes nothing. A metes description in a DEVR IDENTIFIES the
parcel; the same description in a subdivision CHANGES it — which is why
`identity` is the function and `metes` is the reference.

⚠ COVERAGE IS RECORDED NEXT TO THE PATTERN, AND IT DIAGNOSES THE PATTERN. A
function at 0/25 can be correct (a DEVR has no debt). A REGION at 9/25 cannot —
every recorded instrument is signed. Measured coverage is therefore part of the
definition, not a separate report.
"""
from __future__ import annotations

import json
import pathlib
import re

# ── FUNCTIONS — what changed ────────────────────────────────────────────────
# Vocabulary is Login's: title (not "ownership"), debt (not "financing").
FUNCTIONS = {
    "title": {
        "means": "title passes, is confirmed, or is clouded",
        "patterns": [r"do(?:es)?\s+hereby\s+grant", r"grant,?\s+bargain",
                     r"sell\s+and\s+convey", r"remise,?\s+release", r"quitclaim",
                     r"conveys?\s+and\s+warrants?"],
        # 0/25 on DEVR is CORRECT — a rights transfer is not a conveyance.
        "coverage": {"devr_upright": "0/25 — CORRECT, not a gap: a DEVR is not a deed",
                     "DEED": "46% of 50 — hidden-function matrix, misses unexplained",
                     "measured_against": "666-doc census, all detectors vs all types",
                     "⚠": "the highest-volume function after CAPITAL and the least proven "
                          "ON the documents it exists for"},
        "status": "weak",   # never fired on any corpus yet
    },
    "envelope": {
        "means": "buildable envelope changes — rights severed, transferred, merged",
        "patterns": [r"development\s+rights", r"floor\s+area\s+ratio",
                     r"unused\s+development", r"zoning\s+lot",
                     r"transferable\s+development"],
        "coverage": {"devr_upright": "21/25 · 1,104 hits"},
        "status": "proven",
    },
    "encumbrance": {
        "means": "a burden is created, released, or modified",
        "patterns": [r"excepting\s+and\s+reserving", r"easement",
                     r"covenants?\s+running\s+with", r"restrictive\s+covenant"],
        # ⚠ "subject to" was REMOVED from this list: it fires on ordinary prose
        # and inflated encumbrance from 128 to 220 hits. A pattern that matches
        # boilerplate is worse than no pattern — it manufactures a function.
        "coverage": {"devr_upright": "12/25 · 128 hits"},
        "status": "proven",
    },
    "capital": {
        "means": "an obligation is secured, assigned, or discharged",
        # ⚠ REBUILT FROM MEASURED TEXT, 2026-08-16. The original four patterns
        # were deed-era phrasing and fired on 16% of MORTGAGES — the instrument
        # whose entire purpose is debt. The census showed MTGE reading
        # encumbrance 28% ABOVE debt 16%, which is not a fact about mortgages,
        # it is a vocabulary tuned to the wrong document type.
        #
        # Counted over 208 financing documents (MTGE/SAT/ASST/AL&R/AGMT heads):
        #   security instrument 40% · the note 48% · secures 34% · repayment 32%
        #   principal sum 28% · loan 44% · indebtedness · consolidat 70% on AGMT
        # The modern uniform mortgage says "This Security Instrument secures to
        # Lender: (a) the repayment of the Loan ... evidenced by the Note", and
        # none of the old four patterns touch any of it.
        "patterns": [r"secures?\s*to\s*\w+",
                     r"repayment\s*of\s*the\s*(?:loan|note|indebtedness)",
                     r"principal\s*sum",
                     r"evidenced\s*by\s*(?:a|the|that)?\s*\w*\s*note",
                     r"\bindebtedness\b", r"promissory\s*note",
                     r"to\s+secure\s+the\s+payment",
                     # ⚠ CEMAs ARE FILED AS AGMT AND THIS IS HOW THEY READ.
                     # "consolidat" appears on 70% of AGMT documents — the
                     # single strongest signal of any pattern in this file, and
                     # the reason AGMT is 922,096 documents rather than a
                     # miscellany. Consolidation is a DEBT event.
                     r"consolidat\w+", r"extension\s*and\s*modification",
                     r"releases?\s+and\s+discharges?",
                     r"do(?:es)?\s+hereby\s+assign"],
        # ⚠ ROLE WORDS ARE DELIBERATELY ABSENT. "mortgagor" 59%, "lender" 57%,
        # "borrower" 46% are the strongest raw signals here and NONE of them is
        # a function pattern — they say WHO, not WHAT CHANGED. Putting them in
        # this list would make every mortgage fire debt for having a lender,
        # which is true of the parties and says nothing about the instrument.
        # They live in roles.py, where direction is read.
        "coverage": {"MTGE": "59% (was 16%)", "SAT": "61% (was 40%)",
                     "ASST": "65% (was 42%)", "AL&R": "55% (was 10%)",
                     "AGMT": "85% (was 18%)",
                     "specificity": "DEED 0/50 · EASE 1/50 · DEVR 5/1181"},
        "status": "proven",
    },
    "identity": {
        "means": "which parcel this is — STATED (observes) or CHANGED (transacts)",
        # ⚠ THE OLD VOCABULARY WAS NOT WRONG, IT WAS HALF. It read
        # subdivid|merge|apportion|tax lot creat — the TRANSACTS side, where the
        # parcel itself changes — and fired on 68 of 666 documents. Reading one
        # mortgage to page 11 showed the other half: pages 10 and 11 are
        # SCHEDULE A, "BEGINNING at a point on the Westerly side of Nostrand
        # Avenue", the metes and bounds for both parcels — the strongest identity
        # claim in the instrument, scoring ZERO. A description is IDENTITY in
        # observes mode. Mode already separates the two, which was the whole
        # argument for absorbing PARCEL into IDENTITY.
        #
        # ⚠ AND IT LIVES IN THE BODY. Measured over 40 stratified documents read
        # to the last page (456 pages, 2.23 s/page): `metes` fires on 18
        # documents in the body against 3 in the head. Any head-page rate for
        # this function is an understatement by construction.
        "patterns": [
            # observes — the parcel is stated
            r"\bBEGINNING\s+at\s+a\s+point\b|\bRUNNING\s+THENCE\b|\bTHENCE\s+(?:North|South|East|West)",
            r"\ball\s+that\s+certain\b|\b(?:plot|piece|parcel)\s+of\s+land\b",
            r"\bSCHEDULE\s*[\"\u201c']?\s*A\b|\bTITLE\s*N[O0]\b",
            r"\bBlock\s*:?\s*\d{1,5}\b.{0,24}\bLots?\b",
            r"bounded\s+and\s+described|more\s+(?:fully|particularly)\s+described",
            # transacts — the parcel changed
            r"\bsubdivid", r"\bmerge[sd]?\s+into\b|\bzoning\s+lot\s+merger\b",
            r"\bapportion"],
        "coverage": {
            "corpus (head pages)": "418/666 = 63% vs 68/666 = 10% before",
            "depth n=40 full reads": "stated in head AND body 50% · head only 12.5% "
                                     "· ⚠ BODY ONLY 15% · neither 22.5%",
            "by cue head vs body": "metes 3/18 · parcel_land 4/13 · schedule 8/10 "
                                   "· block_lot 12/8 · bounded 12/18 · "
                                   "subdivide 1/4 · merge 0/3 · apportion 1/3",
            "⚠ dropped": "`tax lot creat` fired 0 in head and 0 in body across 456 "
                         "pages — a pattern nobody uses, removed rather than left "
                         "to look like coverage",
            "⚠ not a discriminator": "nearly every real-property instrument "
                                     "identifies its parcel, so this function is "
                                     "NOT for telling document types apart. Its "
                                     "value is the CONTENT of the claim — the "
                                     "metes, the block/lot — which is what can be "
                                     "compared across time and against the tax map",
            "measured_against": "666-doc census heads + 40 stratified documents read "
                                "to the last page (456 pages, 18 doc types)"},
        "status": "proven",
    },
    "occupancy": {
        "means": "who is in it and on what terms — the leasehold, not the fee",
        # ⚠ BUILT BY MEASUREMENT, NOT BY INTUITION — occupy_build.py scores every
        # candidate separately on the lease family AND on DEED/MTGE/EASE/DEVR.
        # 18 candidates were tried; 11 were REJECTED. `the premises` looked like
        # the obvious lease word and reads 55% of leases — and 100% of DEVRs,
        # 38% of mortgages, 36% of deeds. It would have relabelled a third of
        # ACRIS as leases while every downstream check still passed.
        #
        # ⚠ THE KEEP RULE HAD TO BECOME PER-TYPE. A global recall threshold threw
        # away `terminate` (22% overall, 100% of TERL) and `assign_lease` (23%
        # overall, 100% of ASSTO): perfect readers of one sub-type, discarded for
        # being poor readers of the other four. That is precisely the
        # type-specific vocabulary this project already knows a function has.
        "patterns": [r"\blessor\b|\blessee\b",
                     r"\blandlord\b|\btenant\b",
                     r"memorandum\s*of\s*lease",
                     r"assign\w*\s*of\s*(?:the\s*)?lease|assigns?\s*(?:the\s*)?lease",
                     r"terminat\w+\s*of\s*(?:the\s*)?lease|lease\s*is\s*(?:hereby\s*)?terminated",
                     r"commencement\s*date|expiration\s*date|lease\s*year",
                     r"subordinat\w+\s*(?:of|to)\s*(?:the\s*)?(?:lease|mortgage)"],
        # ⚠ NO RATE WITHOUT ITS DENOMINATOR AND ITS CORPUS.
        "coverage": {"MLEA": "100% (n=20)", "ASSTO": "100% (n=20)",
                     "TERL": "100% (n=20)", "LEAS": "95% (n=48)",
                     "SUBL": "85% (n=40)",
                     "union": "140/148 = 95%",
                     "leak": "13/150 = 9% vs DEED 50 · MTGE 49 · EASE 50 · DEVR 1",
                     "measured_against": "occupy_sample.py, 151 documents spread "
                                         "across 5 eras incl. microfilm and pre-1990; "
                                         "HEAD=6 pages only, body NOT read",
                     "residual": "8 misses, ALL film/book — and NOT bad reads "
                                 "(3.1k-12.3k clean chars). 6 are SUBL used for "
                                 "MORTGAGE subordination, 1 is a MEMORANDUM OF "
                                 "OPTION TO PURCHASE filed as LEAS. The refusals "
                                 "are CORRECT; the register is wrong about SUBL."},
        "status": "proven",
    },
}


# ── THE CANONICAL FUNCTION LABELS — eleven, all nouns, closed 2026-08-16 ────
# A function names a domain of fact, not an action. Detector keys below are the
# lowercase of these labels; five have no detector yet and every read of them
# is `unread`, never 0%.
CANONICAL = ["IDENTITY", "TITLE", "OCCUPANCY", "ENCUMBRANCE", "ENVELOPE",
             "ENTITLEMENT", "PERMIT", "ASBUILT", "CAPITAL", "VALUE", "COST"]

# ⚠ ONE NORMALISER FOR EVERY TOOL. Register labels, legacy labels and struck
# labels all resolve HERE — the day two tools carry their own maps is the day
# they disagree silently. CONTEXT returns None on purpose: it is not a function
# (derived context is an inference over lineage; exogenous facts belong to
# subject_type), and forcing it to a function would hide exactly that decision.
_CANON = {"IDENTIFY": "IDENTITY", "PARCEL": "IDENTITY",
          "ENCUMBER": "ENCUMBRANCE",
          "OCCUPY": "OCCUPANCY",
          "ENTITLE": "ENTITLEMENT",
          "DISTRESS": "CAPITAL",   # the register's distress types are liens/arrears — claims on value
          "PARTY": "TITLE",        # POA: TITLE · signals · subject=entity
          "CONTEXT": None}


def canon(label):
    """Canonical function label, or None if the input is not a function."""
    u = str(label or "").strip().upper()
    u = _CANON.get(u, u)
    return u if u in CANONICAL else None


# ── DOCUMENT TYPE — one vocabulary, resolved from ACRIS's OWN code table ──
# ⚠ TWO WRITE PATHS WERE SPELLING THE SAME TYPE TWO WAYS. The bulk/Socrata path
# stores the CODE ("MTGE"); the live path scrapes DOC. TYPE off the detail page,
# which renders the DESCRIPTION ("MORTGAGE"). Both landed in document.doc_type,
# so every GROUP BY doc_type silently split one type into two buckets — and this
# file's own calibrations are keyed on the codes (MTGE 59%, SAT 61%, DEED 0/50).
#
# ⚠ THE CODE IS CANONICAL, NOT THE DESCRIPTION. 21.6M historical rows and every
# measurement in this module already use codes. Normalising the other way would
# invalidate the calibrations rather than the handful of live rows.
#
# ⚠ RESOLVED FROM THE AUTHORITY, NOT TRANSCRIBED. _doctype_codes.json is ACRIS's
# Document Control Codes table as pulled (126 types). A hand-written map here
# would drift the moment ACRIS adds a type, and would have nowhere to record that
# the vocabulary is 126 and not the 95 an earlier count assumed.
# Measured 2026-08-19: 126 codes -> 126 distinct descriptions, ZERO collisions,
# so description -> code is a function and this normalisation is lossless.
_DOCTYPE_PATH = pathlib.Path(__file__).with_name("_doctype_codes.json")
_DOCTYPE_BY_DESC = None
_DOCTYPE_CODES = None
_DOCTYPE_UNRESOLVED = set()


def _doctype_load():
    global _DOCTYPE_BY_DESC, _DOCTYPE_CODES
    if _DOCTYPE_BY_DESC is not None:
        return
    _DOCTYPE_BY_DESC, _DOCTYPE_CODES = {}, set()
    try:
        table = json.loads(_DOCTYPE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return                      # absent table -> canon becomes a no-op, never a crash
    for code, row in table.items():
        c = str(code).strip().upper()
        _DOCTYPE_CODES.add(c)
        desc = str(row.get("doc__type_description") or "").strip().upper()
        if desc:
            _DOCTYPE_BY_DESC[desc] = c


def is_acris_document(document_id):
    """ACRIS document ids carry no source prefix; other registers do (RC_ = the
    Richmond County Clerk). One place to ask 'whose vocabulary governs this row'."""
    return not str(document_id or "").upper().startswith(("RC_",))


def doc_type_canon(label, document_id=None):
    """Canonical ACRIS doc_type CODE for a code or a description.

    ⚠ THIS IS ACRIS'S VOCABULARY AND ONLY ACRIS'S. On 2026-08-19 a sweep applied
    this map to the whole document table without scoping it, and rewrote ~644,000
    RICHMOND rows from their native MORTGAGE to ACRIS's MTGE (plus DECLARATION ->
    DECL, EASEMENT -> EASE, LEASE -> LEAS). Richmond is a separate register with
    its own 64-type vocabulary. The mapping check said "lossless, idempotent, 0
    remaining" - all true, and all measured on the wrong population.

    ⚠ PASS document_id WHENEVER YOU HAVE IT. With it, a foreign-source row is
    returned untouched instead of being silently translated. Without it this
    cannot tell whose vocabulary it is being handed, which is exactly how the
    incident happened - so the caller that omits it is asserting ACRIS.

    Already a code -> returned unchanged. A description -> its code. Anything
    else -> the cleaned input, recorded in doc_type_unresolved() so an unknown
    label is VISIBLE rather than silently becoming a second spelling. It never
    returns None: this runs in a write path, and a null doc_type would be a
    worse failure than an unrecognised one.
    """
    if document_id is not None and not is_acris_document(document_id):
        return str(label or "").strip()          # foreign register - not ours to canon
    _doctype_load()
    u = str(label or "").strip().upper()
    if not u:
        return u
    if u in _DOCTYPE_CODES:
        return u
    hit = _DOCTYPE_BY_DESC.get(u)
    if hit:
        return hit
    _DOCTYPE_UNRESOLVED.add(u)
    return u


def doc_type_unresolved():
    """Labels seen that matched neither a code nor a description."""
    return sorted(_DOCTYPE_UNRESOLVED)


# ── MODES — did the world change, was it merely claimed, or just measured? ──
# ⚠ MEASURED AT CLAUSE LEVEL, NOT DOCUMENT LEVEL (mode_build.py). ACRIS is a
# register of TRANSACTIONS: of 21.6M documents essentially all transact, so a
# document-level bench would have had one class and produced a meaningless
# number. One document emits SEVERAL events and a single deed carries all three
# at clause level, so the clause is both the measurable unit and the right one.
#
# ⚠ GROUND TRUTH IS STRUCTURAL AND INDEPENDENT OF THE CUES: legal drafting puts
# recitals under WHEREAS (state facts) and operative language under NOW
# THEREFORE (change them). 473 recital / 191 operative clauses over 23,282.
#
# ⚠ WHAT THIS TRUTH CANNOT DO: it separates transacts from NOT-transacts. Both
# observes and signals live in recitals, so it cannot tell them apart. The
# observes coverage below therefore means "reliably recital", not "proven to be
# an observation" — a weaker claim, stated weakly on purpose.
MODES = {
    "transacts": {
        "means": "the world changed — only these may assert that state changed",
        "patterns": [r"do(?:es)?\s*hereby\s*(?:grant|convey|demise|mortgage|assign|"
                     r"release|remise|bargain|sell|transfer|quitclaim)",
                     r"\bhereby\s+(?:grants?|conveys?|assigns?|releases?|declares?|"
                     r"covenants?|agrees?|transfers?)\b",
                     r"\bin\s+consideration\s+of\s+the\s+sum\b|\breceipt\s+whereof\b"],
        "coverage": {"perform_grant": "100% operative (0 recital / 10 operative)",
                     "hereby_verb": "97% operative (1 / 30)",
                     "consideration": "95% operative (2 / 35)",
                     "measured_against": "census_head 666 docs · 23,282 clauses · "
                                         "WHEREAS/NOW-THEREFORE structural labels"},
        "status": "proven",
    },
    "observes": {
        "means": "state was measured or recited, nothing changed",
        "patterns": [r"\bis\s+the\s+(?:owner|holder|lessee|fee\s+owner)\s+of\b",
                     r"\b(?:known\s+as|designated\s+as|identified\s+as)\b",
                     r"\bas\s+of\s+the\s+date\s+hereof\b|\bpresently\b|\bcurrently\b",
                     r"\b(?:outstanding|unpaid|principal)\s+(?:balance|amount)\s+"
                     r"(?:is|of)\b|\bthere\s+(?:is|remains)\s+(?:now\s+)?(?:due|owing)\b",
                     r"\bwas\s+(?:duly\s+)?recorded\b|\bhas\s+been\s+(?:duly\s+)?recorded\b"],
        "coverage": {"is_owner": "100% recital (41 / 0)", "known_as": "94% (31 / 2)",
                     "as_of_state": "100% (10 / 0)", "balance_is": "91% (10 / 1)",
                     "was_recorded": "100% (10 / 0)",
                     "⚠ what it proves": "RELIABLY RECITAL, not proven observation — "
                                         "the structural truth cannot separate "
                                         "observes from signals",
                     "measured_against": "same 23,282-clause bench"},
        "status": "weak",
    },
    "signals": {
        "means": "intent or expectation asserted by an interested party, not yet fact",
        # ⚠ MEASURED ON BSA, NOT ACRIS (signals_build.py). ACRIS could not teach
        # this: 4 of 5 first candidates fired FEWER THAN 10 TIMES in 23,282
        # clauses, because ACRIS records what happened, not what is proposed.
        # DOB NOW rows ARE signals events but carry no prose to learn from, and
        # DOB BIS documents are NOT YET ACQUIRED. BSA resolutions recite the
        # application before granting it, so one document holds both sides.
        #
        # ⚠ AND THE DOB GAP IS NOT A VOCABULARY GAP. Login, 2026-08-16:
        # acquisition precedes extraction, and PW1/ZD1 are FORMS — they follow a
        # fixed layout, so once acquired they are read by a FIELDMAP against
        # known positions, not by learning prose. Do not queue vocabulary work
        # for PERMIT/ASBUILT/ENTITLEMENT-via-DOB; queue acquisition, then a
        # fieldmap. Prose vocabulary is only needed where the instrument is
        # free-drafted: ACRIS bodies, BSA resolutions, private agreements.
        #
        # ⚠ GROUND TRUTH IS THE AGENT: the APPLICANT proposes, the BOARD
        # resolves. Who acts is independent of the verbs being tested.
        # 3,335 applicant-agent clauses vs 3,903 board-agent, 300 decisions.
        "patterns": [r"\bseeks?\b|\brequests?\b|\bapplies\s+for\b",
                     r"\bproposes?\b|\bproposed\b",
                     r"\bsubmitt?ed\b|\brepresents?\s+that\b|\bstates?\s+that\b|"
                     r"\basserts?\s+that\b",
                     r"\bwould\s+(?:be|have|permit|allow|result)\b|"
                     r"\bwill\s+(?:be|have|permit|allow|result)\b"],
        "coverage": {"submitted": "97% applicant (1050/27) · ACRIS leak 0.2%",
                     "seeks": "90% (196/22) · leak 0.3%",
                     "would_will": "86% (37/6) · leak 0.9% — weakest, modal verbs are common",
                     "proposes": "79% (239/62) · leak 0.1%",
                     "union": "fires on 279/300 BSA decisions = 93%",
                     "⚠ CLAUSE LEVEL ONLY": "document-level the union fires on "
                                            "164/666 ACRIS documents = 25%. That is "
                                            "NOT a defect: a deed may contain one "
                                            "forward-looking clause without being a "
                                            "signal. Mode belongs to the EVENT; "
                                            "never label a document from it.",
                     "rejected": "intends 6 hits · if_granted 0 · upon_future 0 · "
                                 "estimated 3 — all unread even in BSA. `to_permit`, "
                                 "`application`, `resolved`, `board_finds` proved to be "
                                 "the DECISION side (83-100% board) and are kept as a "
                                 "contrast set, not as signals.",
                     "measured_against": "300 cached BSA decisions (45 dropped as "
                                         "scan-only) · control 666 ACRIS census docs, "
                                         "23,282 clauses"},
        "status": "proven",
    },
}

# ⚠ REJECTED, AND WHY — kept so the mistake cannot be re-proposed.
#   WITNESSETH   read as performative; measured 65 RECITAL vs 18 operative. It is
#                a HEADER that introduces recitals, not a grant. It alone produced
#                the "8% quoted-performative" figure that looked like a document
#                trap and was my error.
#   executed     0 hits either side — unread, not rejected.
#   estimated    fired 80% recital while proposed as a SIGNALS cue; the bench
#                cannot tell observes from signals, so it proves nothing.
#
# ⚠ THE QUOTED-PERFORMATIVE TRAP DID NOT MATERIALISE HERE. Predicted: a signal
# quoting a transaction's own words. Measured on the KEPT cues: 255 clauses fire,
# 38 also carry a citation, and only 1 pairs a citation with a PAST-TENSE
# performative — which on inspection is a false positive. The risk is real for
# lis pendens and application streams; ACRIS does not hold them, so it stays
# UNREAD rather than disproven.
MODE_C = {m: [re.compile(p, re.I) for p in v["patterns"]] for m, v in MODES.items()}


def mode(clause):
    """Modes whose cues fire on one clause. Empty = mode must come from elsewhere.

    ⚠ 95% OF CLAUSES FIRE NOTHING, and that is correct: most clauses are
    description and boilerplate carrying no mode marker at all. Mode then comes
    from the SOURCE prior (a recorded instrument transacts), and this function
    exists to CONTRADICT that prior, not to replace it.
    """
    return [m for m, pats in MODE_C.items() if any(p.search(clause) for p in pats)]

# ── REGIONS — where to look. NEVER a function. ──────────────────────────────
REGIONS = {
    "cover_page": {
        "means": "ACRIS's own recording wrapper — carries the RPTT/RETT stamps",
        # ⚠ THE PRICE LIVES HERE, not in the index: document_amt is 0 for every
        # DEVR. Discarding this region discards the money.
        "patterns": [r"recording\s+and\s+endorsement", r"document\s+type:?",
                     r"fees\s+and\s+taxes", r"\bCRFN\b"],
        "coverage": {"devr_upright": "25/25"},
        "status": "proven",
    },
    "execution": {
        "means": "who actually signed — the human behind the entity",
        # ⚠ REBUILT FROM THE DATA, NOT GUESSED. The first version leaned on
        # "By:" and "in witness whereof" and fired on 9 of 25 documents. Counted
        # over the last 4 pages of all 25: "STATE OF" 81 · "acknowledg" 81 ·
        # "COUNTY OF" 43 · notary 35 · "personally appeared" 29 · but "By:" only
        # 10. The NOTARIAL ACKNOWLEDGMENT is the near-universal marker, because
        # every recorded instrument must be acknowledged to be recordable — and
        # it is also where the PERSON is named ("personally appeared Michael J.
        # Berey"), which is the field the index can never supply.
        # ⚠ OCR DROPS SPACES ON THIS BLOCK ("NOTARYPUBLIC,STATEOFNEWYORK",
        # "FIRSTAMERICANTITLEINSURANCECOMPANY"), so every pattern tolerates
        # missing whitespace. A space-dependent pattern reads as an absent
        # signature block.
        "patterns": [r"state\s*of\s*new\s*york", r"county\s*of\b",
                     r"acknowledg", r"notary\s*public", r"notarypublic",
                     r"personally\s*(?:appeared|came|known)",
                     r"in\s*witness\s*whereof", r"\bby[:,]\s*[A-Z]",
                     r"its\s+(?:managing\s+)?member", r"vice\s*president",
                     r"authorized\s+signator"],
        # ⚠ 9/25 IS A DETECTOR FAULT, NOT A DOCUMENT PROPERTY. Every recorded
        # instrument is signed, so the true coverage is 25/25 and these patterns
        # miss 16 of them. This is the HIGHEST-VALUE region in the system — the
        # index gives you "123 MAIN ST LLC" and only this gives you the person —
        # so its weakness is the most expensive one on this list.
        "coverage": {"devr_upright": "9/25 ⚠ must be 25/25"},
        "status": "WEAK — fix before any corpus run",
    },
    "exhibit": {
        "means": "attached schedules — where SF quantities and descriptions live",
        # ⚠ The SF quantity in a DEVR is in an EXHIBIT, not the granting clause.
        "patterns": [r"\bexhibit\s+[A-Z]\b", r"schedule\s+[A-Z]\b"],
        "coverage": {"devr_upright": "13/25 · 78 hits"},
        "status": "unverified",
    },
}

# ── REFERENCES — what it points at. Identifies, never changes. ──────────────
REFERENCES = {
    "metes": {
        "means": "the boundary description — identifies, does not alter",
        "patterns": [r"\bthence\b", r"feet\s+to\s+a\s+point",
                     r"point\s+or\s+place\s+of\s+beginning"],
        # ⚠ metes.py CANNOT WALK intercardinal courses with interior angles —
        # 23 of 31 Greenpoint descriptions refuse. Detecting one is not parsing one.
        "coverage": {"devr_upright": "25/25 · 429 hits"},
        "status": "proven",
    },
    "parcel_id": {
        "means": "borough / block / lot",
        "patterns": [r"Block\(?s?\)?[:\s]+\d+", r"Lot\(?s?\)?[:\s]+\d+"],
        "coverage": {"devr_upright": "25/25 · 506 hits"},
        "status": "proven",
    },
    "prior_doc": {
        "means": "a pointer to another instrument — what makes lineage a GRAPH",
        "patterns": [r"\bCRFN\s*\d", r"reel\s+\d+", r"recorded\s+in\s+liber"],
        # ⚠ 2/25 IS NOT A PROPERTY OF DEVRs. A rights transfer nearly always
        # references the ZLDA it executes under or a prior severance. Cross-
        # document links are what let a satisfaction find its mortgage, so this
        # weakness blocks resolution directly.
        "coverage": {"devr_upright": "2/25 ⚠ implausibly low"},
        "status": "WEAK — blocks lineage",
    },
}

# ⚠ ONE CLAUSE DEFINITION FOR EVERY TOOL. Do NOT split on ':' — legal text uses
# the colon as an introducer ("WITNESSETH:", "Mortgage Amount:"), not a boundary.
CLAUSE = re.compile(r"[^.;\n]{25,}")

_C = {g: {k: [re.compile(p, re.I) for p in v["patterns"]] for k, v in d.items()}
      for g, d in (("function", FUNCTIONS), ("region", REGIONS),
                   ("reference", REFERENCES))}

# (group, name, doc_type) -> extra compiled patterns. Empty today: the rebuilt
# debt vocabulary turned out to work across every financing type at once, so
# nothing needed splitting. ⚠ That is a RESULT, not a reason to drop the
# mechanism — `encumbrance` is the known case that will need it, because a deed
# says "subject to covenants running with the land" in one clause while a ZLDA
# spends a numbered section on the same function.
_BY_TYPE = {(g, k, t): [re.compile(p, re.I) for p in ps]
            for g, d in (("function", FUNCTIONS), ("region", REGIONS),
                         ("reference", REFERENCES))
            for k, v in d.items()
            for t, ps in (v.get("by_type") or {}).items()}


def clauses(text):
    """(clause, absolute_offset) — offsets are what make a claim verifiable."""
    for m in CLAUSE.finditer(text or ""):
        yield m.group(0), m.start()


def fire(text, group="function", doc_type=None):
    """Which names in `group` match. group: function | region | reference.

    ⚠ ONE SCHEMA, N VOCABULARIES. `doc_type` selects additional patterns from a
    definition's `by_type` map. This is the structural answer to "does every
    document type need its own table": it does NOT need its own SCHEMA, because
    every type produces the same shape — parties, parcels, quantities, dates,
    references. What differs is the WORDS, and words are data.

    A per-type TABLE would make the one query this system exists to answer —
    follow a parcel across every instrument that touched it — a 126-way union,
    and would still have to be rewritten the first time a document does two
    things at once. The census shows that is the normal case, not the edge:
    a mortgage fires debt AND encumbrance; a ZLDA fires envelope AND
    encumbrance AND identity.
    """
    out = []
    for k, pats in _C[group].items():
        extra = _BY_TYPE.get((group, k, doc_type), []) if doc_type else []
        if any(p.search(text) for p in list(pats) + extra):
            out.append(k)
    return out


def counts(text, group="function", doc_type=None):
    return {k: sum(len(p.findall(text)) for p in
                   list(pats) + (_BY_TYPE.get((group, k, doc_type), [])
                                 if doc_type else []))
            for k, pats in _C[group].items()}


def weak():
    """Everything whose measured coverage says the PATTERN is at fault."""
    out = []
    for g, d in (("function", FUNCTIONS), ("region", REGIONS),
                 ("reference", REFERENCES)):
        for k, v in d.items():
            if str(v.get("status", "")).startswith(("WEAK", "weak")):
                out.append((g, k, v["status"], v["coverage"]))
    return out


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    for label, d in (("FUNCTIONS — what changed", FUNCTIONS),
                     ("REGIONS — where to look", REGIONS),
                     ("REFERENCES — what it points at", REFERENCES)):
        print(f"\n  {label}")
        for k, v in d.items():
            cov = " · ".join(f"{a}: {b}" for a, b in v["coverage"].items())
            print(f"    {k:<13} {v['status']:<28} {cov}")
    print(f"\n  ⚠ WEAK — pattern at fault, not the documents ({len(weak())})")
    for g, k, s, c in weak():
        print(f"    {g}/{k}: {s}")
