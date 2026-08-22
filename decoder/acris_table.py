"""The ACRIS decode, as a table a broker can read.

WHAT THIS IS FOR

    Four questions get asked of every parcel:
        what did it trade for · what debt is really on it ·
        what can be built · who do I call
    `decoder_facts` holds the evidence for those answers. It cannot BE the
    answer: a predicate/value row per page is the right shape for assembling
    and the wrong shape for reading.

    This module is the decoded layer — the traps already applied, not left for
    the reader to re-derive. Two tables, because ACRIS has two grains:

        acris_documents   one row per DOCUMENT   — the atom, 96 for lot 49
        acris_events      one row per EVENT      — the transaction, 28 for lot 49

    A refinancing is FIVE documents and ONE event. Reading at document grain
    triple-counts the money; reading at event grain loses the citations. Both,
    joined, is the only honest shape.

THE RULE THE SCHEMA ENFORCES, BECAUSE REMEMBERING IT FAILED

    ⚠ ONLY THE PRINCIPAL INSTRUMENT IN A BATCH CARRIES MONEY.

    Measured on this parcel: the 2023 batch shows $265,490,000 of face across
    eleven documents. The borrowing was $25,490,000 — an 18x error available to
    anyone who sums a column.

    So `amount_real` is NULL on every companion, never 0.
        0    = "we read it and the amount is zero"     (the 2023 reorg deed)
        NULL = "this instrument does not carry money"  (the ASST beside it)
    A SUM() over NULLs cannot double-count. A SUM() over zeros looks identical
    and is a different claim. The check constraint at the bottom refuses any row
    that carries money without being flagged principal.

THE OTHER RULE: THE INDEX'S OWN FIELDS ARE KEPT, NOT REPLACED

    `doc_type` and `amount_indexed` are stored verbatim beside `true_type` and
    `amount_real`. A decode that overwrites its source cannot be audited, and on
    this parcel the two disagree constantly — EASE was twice a ZLDA, SMIS three
    times a DECL, DEVR once a confirmation, and every DEVR indexes at $0 while
    having a real price on its cover page.
"""
import csv, json, pathlib, re, sys, urllib.request

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = pathlib.Path(__file__).parent
LEGALS = "https://data.cityofnewyork.us/resource/8h5j-fqxa.json"
MASTER = "https://data.cityofnewyork.us/resource/bnx9-e6tj.json"

DDL = """
-- one row per DOCUMENT ------------------------------------------------------
create table if not exists acris_documents (
  bbl            text not null,
  document_id    text not null,
  event_id       text not null,          -- FK to acris_events
  -- the index, verbatim and unmodified
  doc_type       text,                   -- what ACRIS calls it
  amount_indexed numeric,                -- what ACRIS says it is worth
  instrument_date date,                  -- when the parties acted
  recorded_date   date,                  -- when the register filed it
  -- the decode
  true_type      text,                   -- what it actually IS  (EASE -> ZLDA)
  role           text not null,          -- principal | companion | return
  amount_real    numeric,                -- NULL on companions. NEVER 0.
  amount_means   text,                   -- new_money | consolidated | face | price | none
  evidence       text not null,          -- read | index | inferred
  cited_pages    text,                   -- 'p038,p028' — where the decode came from
  note           text,
  updated_at     timestamptz default now(),
  primary key (bbl, document_id),
  -- money without principal status is the double-counting bug, refused at write
  constraint acris_money_only_on_principal
    check (amount_real is null or role = 'principal')
);
create index if not exists acris_documents_bbl on acris_documents(bbl, instrument_date);
create index if not exists acris_documents_event on acris_documents(event_id);

-- one row per EVENT ---------------------------------------------------------
create table if not exists acris_events (
  bbl          text not null,
  event_id     text not null,
  seq          int not null,             -- chronological order, 1..n
  happened     date not null,            -- INSTRUMENT date, not recording date
  recorded     date,
  kind         text not null,            -- see EVENT KINDS below
  headline     text not null,            -- one line, plain language
  party_from   text,
  party_to     text,
  person       text,                     -- the human, when an instrument names one
  amount       numeric,                  -- the ONE number that matters here
  amount_means text,
  -- ⚠ ADDED after a design review found the table could not answer "what debt
  -- is on it". `amount` on a financing event is the NEW money; the outstanding
  -- position is a different number that lives on the AGMT beside it. Storing
  -- only one of them meant the current position ($123,000,000) was recoverable
  -- only by knowing which row to look at — which is not a table, it is a
  -- puzzle. NULL means the instrument did not state a position, never zero.
  position_after numeric,
  sf           numeric,                  -- floor area, on rights transfers
  per_bsf      numeric,                  -- amount / sf, computed not typed
  answers      text[] not null,          -- WHICH QUESTIONS THIS EVENT ANSWERS
  evidence     text not null,
  cited_pages  text,
  detail       text,
  updated_at   timestamptz default now(),
  primary key (bbl, event_id)
);
create index if not exists acris_events_bbl on acris_events(bbl, happened);
create index if not exists acris_events_kind on acris_events(kind);
create index if not exists acris_events_answers on acris_events using gin(answers);

-- EVENT KINDS (closed vocabulary — a new kind is a decision, not a typo)
--   ACQUISITION  title in            SALE         title out
--   REORG        title moves, no money changes hands
--   FINANCING    new money           CONSOLIDATION  debt rolled forward, no new money
--   AIR_RIGHTS   development rights bought
--   ENTITLEMENT  declarations, certifications, zoning-lot formalities
--   RIGHTS_SPLIT envelope divided between lots
--   SERVICING    assignments and terminations only

-- ---------------------------------------------------------------------------
-- THE SIXTEEN QUESTIONS (Login, 2026-08-06)
--
-- "You timeline the index, but then you use ACRIS to answer THIS."
--
-- That is the correct separation and it reorganises the whole system. `kind`
-- describes how documents CLUSTER. `answers` describes what a person ASKS. A
-- table organised by kind makes you know which instrument type carries the fact
-- before you can look it up — which is precisely the expertise the system is
-- supposed to remove the need for.
--
--   IDENTIFY  what is this thing            PARCEL    lot geometry and lineage
--   TITLE     who owns it, and before       VALUE     what it is worth / traded for
--   ENCUMBER  what is recorded against it   DISTRESS  foreclosure, liens, defaults
--   ENVELOPE  what can be built             OCCUPY    who is in it, at what rent
--   ENTITLE   approvals and overrides       PARTY     the entities and the people
--   PERMIT    what was filed to build       CAPITAL   the debt and equity stack
--   ASBUILT   what actually got built       COST      what building it cost
--                                           CONTEXT   the block around it
--
-- ⚠ ACRIS ANSWERS SEVEN OF THE SIXTEEN, and it is important to say which seven
-- rather than let silence read as absence:
--
--   TITLE     fully      — deeds are the chain of title
--   ENCUMBER  fully      — mortgages, easements, declarations
--   CAPITAL   fully      — but only once face is separated from new money
--   PARTY     partly     — entity from the deed, PERSON from the mortgage jurat
--   VALUE     partly     — recorded prices only; DOF sales cover the rest
--   ENVELOPE  partly     — the rights CHARTS are here; the zoning rule is DCP's
--   PARCEL    partly     — lineage appears in RECITALS; the tax map is DOF's
--
--   IDENTIFY DOF/spine · ENTITLE BSA+LPC+DCP · PERMIT DOB · ASBUILT DOB ·
--   COST DOB · OCCUPY HPD · DISTRESS courts+DOF liens · CONTEXT derived
--
-- A blank column in acris_question_coverage means ACRIS CANNOT ANSWER IT, never
-- "there is nothing there" — the distinction that makes the handoff to the
-- other lanes explicit instead of implied.
-- ---------------------------------------------------------------------------

-- what a broker actually opens ----------------------------------------------
create or replace view acris_parcel_story as
select e.bbl, e.seq, e.happened, e.kind, e.headline,
       e.party_from, e.party_to, e.person,
       e.amount, e.amount_means, e.sf, e.per_bsf,
       e.evidence, e.cited_pages,
       (select count(*) from acris_documents d
         where d.bbl = e.bbl and d.event_id = e.event_id) as documents
from acris_events e
order by e.bbl, e.seq;

-- ONE VIEW PER QUESTION — you ask the question, not the document type ---------
create or replace view acris_title as
select bbl, happened, headline, party_from as from_owner, party_to as to_owner,
       person, amount as price, evidence, cited_pages
from acris_events where 'TITLE' = any(answers) order by bbl, happened;

create or replace view acris_capital as
select bbl, happened, headline, party_from as lender,
       amount as new_money, position_after, amount_means, evidence, cited_pages
from acris_events where 'CAPITAL' = any(answers) order by bbl, happened;

create or replace view acris_envelope as
select bbl, happened, headline, sf, amount, per_bsf, evidence, cited_pages, detail
from acris_events where 'ENVELOPE' = any(answers) order by bbl, happened;

create or replace view acris_party as
select bbl, happened, kind, party_from, party_to, person, cited_pages
from acris_events
where 'PARTY' = any(answers) and (person is not null or party_to is not null)
order by bbl, happened;

-- ⚠ the point of this view is the BLANKS. A null column is "ACRIS cannot answer
-- this", which is a routing instruction to another lane — not an empty finding.
create or replace view acris_question_coverage as
select bbl,
       count(*) filter (where 'TITLE'    = any(answers)) as title,
       count(*) filter (where 'ENCUMBER' = any(answers)) as encumber,
       count(*) filter (where 'CAPITAL'  = any(answers)) as capital,
       count(*) filter (where 'PARTY'    = any(answers)) as party,
       count(*) filter (where 'VALUE'    = any(answers)) as value,
       count(*) filter (where 'ENVELOPE' = any(answers)) as envelope,
       count(*) filter (where 'PARCEL'   = any(answers)) as parcel,
       count(*) filter (where 'DISTRESS' = any(answers)) as distress,
       null::int as identify, null::int as entitle, null::int as permit,
       null::int as asbuilt,  null::int as cost,    null::int as occupy,
       null::int as context   -- ^ not ACRIS's to answer; see the note above
from acris_events group by bbl;

-- the money question, answered without double counting.
-- NOTE the filters: face is excluded, and only new_money is summed. Summing
-- `amount` across all events would add consolidations to the borrowings that
-- created them.
create or replace view acris_parcel_money as
select bbl,
       max(amount) filter (where kind = 'ACQUISITION')            as acquired_for,
       max(amount) filter (where kind = 'SALE')                   as sold_for,
       sum(amount) filter (where kind = 'AIR_RIGHTS')             as air_rights_spend,
       sum(sf)     filter (where kind = 'AIR_RIGHTS')             as air_rights_sf,
       round(sum(amount) filter (where kind = 'AIR_RIGHTS')
           / nullif(sum(sf) filter (where kind = 'AIR_RIGHTS'),0), 2) as avg_per_bsf,
       sum(amount) filter (where amount_means = 'new_money')      as total_new_money,
       max(amount) filter (where amount_means = 'consolidated')   as debt_position
from acris_events group by bbl;
"""

# ---------------------------------------------------------------------------
# THE LOT 49 DECODE.
#
# Every entry here was established by reading the document or by arithmetic on
# figures read from it. `cites` names the page. Where a fact is the index's and
# not the page's, evidence is 'index' and it says so.
#
# `docs` assigns documents to the event. A document belongs to exactly one
# event; the builder REFUSES to run if any of the 96 is unassigned or claimed
# twice — the check that would have caught the 1998 deed missing from the prose.
# ---------------------------------------------------------------------------
BBL = "1008000049"

EVENTS = [
 dict(id="1971-deed", happened="1971-10-04", kind="ACQUISITION",
      headline="112 West 25 Realty Corp reorganises into a co-partnership",
      party_from="112 WEST 25 REALTY CORP", party_to="112 WEST 25 COMPANY",
      amount=None, means="none", evidence="read", cites="FT_1320008495632 p001",
      detail="Recites 'Ten Dollars' — the consideration trap, 54 years ago. Taken "
             "subject to a Greenwich Savings Bank mortgage with $127,795.81 "
             "unpaid, the only real number on it. Reel 220 p836. Both parties "
             "c/o Abraham I. Kirschenbaum Esq, 370 Seventh Ave. Metes and "
             "bounds compute to 15,642 sf.",
      docs=["FT_1320008495632", "FT_1330008495633"], principal="FT_1320008495632"),

 dict(id="1990-mtge", happened="1990-07-05", kind="FINANCING",
      headline="The mortgage every later loan descends from",
      party_to="(lender not read)", amount=1_000_000, means="face",
      evidence="index", cites="FT_1980000345898 [index]",
      detail="Reel 1707 Page 1285. Cross-referenced by the 2003 CEMA and again "
             "by the 2023 MetLife consolidation; four assignments 2007-2023 "
             "resolve back to it. 33 years of rolled-forward debt start here. "
             "WARNING: its own terms are unread — known only from what its "
             "descendants say about it.",
      docs=["FT_1980000345898", "FT_1990000345899"], principal="FT_1980000345898"),

 dict(id="1998-deed", happened="1998-11-23", recorded="1999-06-29",
      kind="ACQUISITION",
      headline="Partnership conveys to the Edelman family partnership",
      party_from="112 WEST 25 COMPANY", party_to="EDELMAN FAMILY LIMITED PARTNERSHIP",
      person="Norman Edelman; Rita Edelman (co-partners)",
      amount=None, means="none", evidence="read", cites="FT_1570006671557 p002",
      detail="Bargain and Sale with Covenant, Title No. 380-LY-8710. Reel 2903 "
             "p1236. Notary Mark J. Mandell, Nassau County. Return-to Glen S. "
             "Edelman Esq, 3000 Marcus Avenue, Lake Success — the same person "
             "who signs the 2007 sale. Recorded 7 MONTHS after execution, the "
             "longest lag on this parcel. This event was missing from two "
             "drafts of the ledger: without it there is no conveyance between "
             "a 1971 co-partnership and a 2007 seller of a different name.",
      docs=["FT_1570006671557"], principal="FT_1570006671557"),

 dict(id="1998-mtge", happened="1998-11-24", recorded="1999-06-29",
      kind="FINANCING",
      headline="Family partnership borrows from Queens County Savings Bank",
      party_from="QUEENS COUNTY SAVINGS BANK", party_to="EDELMAN FAMILY LP",
      amount=226_378.12, means="new_money", evidence="read",
      cites="FT_1710006669171 (margin note 'MT $4527.56')",
      detail="Filed the day after the deed that gave the borrower title. The "
             "handwritten tax note is EXACTLY 2.0000% of principal — the era's "
             "rate, and proof the modern 2.800% table cannot be run backwards.",
      docs=["FT_1710006669171", "FT_1370006667337", "FT_1730006667273",
            "FT_1810006667281", "FT_1260006667226"],
      principal="FT_1710006669171"),

 dict(id="2003-cema", happened="2003-10-28", recorded="2003-11-28",
      kind="CONSOLIDATION",
      headline="New York Community Bank consolidates — no new money",
      party_from="NEW YORK COMMUNITY BANK", party_to="EDELMAN FAMILY LP",
      amount=969_656.99, means="consolidated", evidence="read",
      cites="2003110900238001 p001",
      detail="Taxable $0 under exemption 255. Cross-references MANHATTAN 1990 "
             "Reel 1707 Page 1285 — the root was already rolling forward 20 "
             "years before MetLife. CRFN 2003000476358. Cover page gives the "
             "property type as APARTMENT BUILDING: what stood here before the "
             "hotel. Also missing from two drafts of the ledger.",
      docs=["2003110900238001"], principal="2003110900238001"),

 dict(id="2007-sale", happened="2007-06-20", recorded="2007-06-29",
      kind="ACQUISITION",
      headline="Extell buys the site for $42.7M",
      party_from="EDELMAN FAMILY LP", party_to="112-118 WEST 25TH LLC (c/o Extell)",
      person="Glen S. Edelman (signs for seller)",
      amount=42_700_000, means="price", evidence="read",
      cites="2007062101109001",
      detail="Bargain and sale with covenant. WARNING p3 is scanned upside "
             "down — a page a text pipeline drops silently. WARNING the "
             "RPTT&RET companion carries $2,300,000 in the index, which "
             "matches nothing about this sale and is UNRESOLVED — that page "
             "has not been read.",
      docs=["2007062101109001", "2007062101109002"], principal="2007062101109001"),

 dict(id="2007-fin", happened="2007-06-20", recorded="2007-06-29",
      kind="FINANCING", headline="Acquisition financing, consolidated to $39.2M",
      amount=38_311_288, means="new_money", evidence="index",
      cites="2007062101109004 [index]",
      detail="MTGE $38,311,288 new; AGMT and AL&R both restate $39,229,334. "
             "The two $39.2M figures are the SAME debt seen twice.",
      docs=["2007062101109003", "2007062101109004", "2007062101109005",
            "2007062101109006"], principal="2007062101109004"),

 dict(id="2010-air", happened="2010-10-14", recorded="2010-11-16",
      kind="AIR_RIGHTS",
      headline="Air rights #1 — Sabetfard lots 53/55/56, 53,578 sf",
      party_from="124-26 W 25 STREET LLC; 120-22 W 25 STREET LLC (Sabet Mgmt)",
      party_to="112-118 WEST 25TH LLC",
      amount=5_000_000, means="price", sf=53_578, evidence="read",
      cites="2010102601040006 p038 (Exhibit D), p028 (schedule), p047 (survey)",
      detail="Zoning Lot Development and Easement Agreement merging lots 53, 55 "
             "and 56 with lot 49. ACRIS indexes the price as $0; recovered from "
             "the cover stamps — RPTT $131,250 / 2.625% and RETT $20,000 / "
             "0.4%, both landing on $5,000,000. Exhibit D implies FAR 10.0, not "
             "the 12.0 PLUTO shows today. Sellers keep their buildings and grant "
             "a light-and-air easement 20 ft deep from 23 ft above curb.",
      docs=["2010102601040002", "2010102601040003", "2010102601040004",
            "2010102601040005", "2010102601040006", "2010110900202001"],
      principal="2010102601040006"),

 dict(id="2011-serv", happened="2011-11-08", recorded="2011-12-06",
      kind="SERVICING", headline="Mortgage assigned; leases-and-rents amended",
      amount=None, means="none", evidence="index", cites="[index]",
      detail="Two ASST and two AALR. No money moves; the lender changes hands.",
      docs=["2011112200806001", "2011112200841001", "2011112200888001",
            "2011112200913001"], principal=None),

 dict(id="2012-cema", happened="2012-10-05", recorded="2012-10-31",
      kind="FINANCING", headline="Refinancing — $1.6M new against a $39M position",
      amount=1_607_226, means="new_money", evidence="index",
      cites="2012101500666006 [index]",
      detail="Eight documents. AGMT and AL&R each restate $39,000,000; the "
             "taxed MTGE shows the actual borrowing was $1.6M.",
      docs=["2012101500666002", "2012101500666003", "2012101500666004",
            "2012101500666005", "2012101500666006", "2012101500666007",
            "2012101500666008"], principal="2012101500666006"),

 dict(id="2012-air", happened="2012-12-19", recorded="2013-01-08",
      kind="AIR_RIGHTS",
      headline="Air rights #2 — the Horne co-op, the through-block linchpin",
      party_from="THE HORNE BUILDING OWNERS CORP (co-op, 127 W 24th, lot 23)",
      party_to="112-118 WEST 25TH LLC",
      amount=4_614_690, means="price", sf=22_845, evidence="read",
      cites="2012122701550003 p043 (Exhibit D), p031 (schedule)",
      detail="A residential co-op board selling its unused floor area. THE "
             "QUANTITY IS STATED NOWHERE: derived by differencing this chart "
             "against the 2010 chart — developer allocation 209,968 -> 232,813. "
             "$4,614,690 / 22,845 = $202.00 EXACT TO THE CENT, which is how you "
             "know the parties negotiated per square foot. This parcel connects "
             "the 25th Street frontage to 24th Street and priced at more than "
             "double the 2010 deal 26 months earlier.",
      docs=["2012122701550001", "2012122701550002", "2012122701550003",
            "2012122701550004"], principal="2012122701550003"),

 dict(id="2013-air3", happened="2013-05-17", recorded="2013-06-19",
      kind="AIR_RIGHTS", headline="Air rights #3 — Brick Farms co-op, lot 22",
      party_from="BRICK FARMS COOPERATIVE LTD (c/o Forest City Ratner, 131 W 24th)",
      party_to="112-118 WEST 25TH LLC",
      person="David L. Berliner, VP (seller); Marc Kwestel, VP (buyer)",
      amount=1_450_000, means="price", sf=10_726, evidence="read",
      cites="2013052101674004 p040 (Exhibit D), p028 (schedule), p042 (Exhibit F)",
      detail="Chart: lot 22 generated 28,625, retained 17,899, excess 10,726; "
             "developer after transfer 243,539 = 232,813 + 10,726. Ridgewood "
             "Savings Bank was mortgagee and consented. ALSO grants a "
             "light-and-air easement over lot 22 above elevation 130 ft — the "
             "tower is buying protected exposure, not only floor area. "
             "Exhibit D is a LANDSCAPE scan whose file size reads like a survey. "
             "Companion 2013052101674003 is typed SMIS and is really a "
             "Declaration of Zoning Lot Restrictions.",
      docs=["2013052101674001", "2013052101674002", "2013052101674003",
            "2013052101674004"], principal="2013052101674004"),

 dict(id="2013-air4", happened="2013-05-17", recorded="2013-06-19",
      kind="AIR_RIGHTS", headline="Air rights #4 — 133 West 24th co-op, lot 21",
      party_from="133 WEST 24TH STREET CORPORATION (co-op)",
      party_to="112-118 WEST 25TH LLC",
      person="Jonathan Pressman (board member, seller)",
      amount=1_340_250, means="price", sf=10_722, evidence="read",
      cites="2013052101674008 p041 (Exhibit D), p029 (schedule)",
      detail="Developer after transfer 254,261 = 243,539 + 10,722. Wells Fargo "
             "as CMBS trustee consented. The agreement CAPS LOT 21 AT SEVEN "
             "DWELLING UNITS in perpetuity — the seller's own future is "
             "constrained by the sale, which is a fact about the neighbour "
             "worth carrying forward. $1,340,250 / 10,722 = $125.00 exact.",
      docs=["2013052101674005", "2013052101674006", "2013052101674007",
            "2013052101674008"], principal="2013052101674008"),

 dict(id="2013-air5", happened="2013-08-07", recorded="2013-08-27",
      kind="AIR_RIGHTS",
      headline="Air rights #5 — Extell buys airspace over lot 20 FROM ITSELF",
      party_from="112-118 WEST 25TH LLC (as airspace owner)",
      party_to="112-118 WEST 25TH LLC (as developer)",
      amount=None, means="none", sf=14_703, evidence="read",
      cites="2013080901116002 p040 (Exhibit D)",
      detail="Filed as EASE; it is the fifth ZLDA. One entity contracting in two "
             "capacities over the airspace above 135 W 24th (lot 20) above "
             "elevation 130 ft. Zero tax because there are not two parties. "
             "Envelope 254,261 -> 268,964; totals 390,160. WARNING THE PRICE IS "
             "NOT ON THIS PARCEL — it was recorded against lot 20, so $/BSF for "
             "this transfer cannot be computed from lot 49's record at all. "
             "Companion 2013080901116001 is typed SMIS and is really the "
             "declaration covering ALL EIGHT lots with a single declarant.",
      docs=["2013080901116001", "2013080901116002"], principal=None),

 dict(id="2013-sale", happened="2013-08-07", recorded="2013-08-27",
      kind="SALE", headline="Extell sells to the Lam Group for $67.5M, having built nothing",
      party_from="112-118 WEST 25TH LLC (Extell)", party_to="LAM GEN 25 LLC",
      amount=67_500_000, means="price", evidence="read",
      cites="2013080901116003 (margin 'TT 270,000')",
      detail="Body recites 'Ten Dollars'; RPTT $1,771,875 / 2.625% and RETT "
             "$270,000 / 0.4% BOTH resolve to $67,500,000 exactly. Conveys 'any "
             "development rights appurtenant'. Recorded in the SAME BATCH as the "
             "fifth ZLDA and the eight-lot declaration: Extell completed the "
             "envelope and sold it in one motion.",
      docs=["2013080901116003"], principal="2013080901116003"),

 dict(id="2013-fin", happened="2013-08-07", recorded="2013-08-28",
      kind="FINANCING", headline="Lam finances; income pledged to Goldman Sachs",
      party_from="GOLDMAN SACHS BANK USA", party_to="LAM GEN 25 LLC",
      amount=1_500_000, means="new_money", evidence="read",
      cites="2013081200922004 (AL&R $40,500,000)",
      detail="MTGE $1.5M new; AGMT and AL&R both restate $40,500,000. The ASST "
             "in this batch resolves to the 1999 agreement — a 14-year chain.",
      docs=["2013081200922001", "2013081200922002", "2013081200922003",
            "2013081200922004", "2013081200922005"],
      principal="2013081200922002"),

 dict(id="2014-sage", happened="2014-07-14", recorded="2014-08-13",
      kind="SERVICING", headline="Supporting agreement", amount=None, means="none",
      evidence="index", cites="[index]", detail="Unread; batch position only.",
      docs=["2014080700619001"], principal=None),

 dict(id="2014-mtge", happened="2014-11-25", recorded="2014-12-02",
      kind="FINANCING", headline="$7.5M new money — and the document that names the human",
      party_to="LAM GEN 25 LLC", person="JEFFREY LAM",
      amount=7_500_000, means="new_money", evidence="read",
      cites="2014112601161004 p007 (jurat), p008 (Exhibit A)",
      detail="Consolidated to $48,000,000. The jurat types JEFFREY LAM appearing "
             "personally before notary Helen Eng, Queens County — the deed gave "
             "an entity, the mortgage gives the person. Its Exhibit A lists "
             "benefit easements WITH CRFNs including a Lot 20 ZLDA recorded "
             "2008-02-26, CRFN 2008000078652: the assemblage's FIRST instrument, "
             "two years before Sabetfard, and indexed only against lot 20.",
      docs=["2014112601161001", "2014112601161002", "2014112601161003",
            "2014112601161004", "2014112601161005", "2014112601161006"],
      principal="2014112601161004"),

 dict(id="2015-confirm", happened="2015-03-31", recorded="2015-06-18",
      kind="ENTITLEMENT", headline="Sabetfard CONFIRMS the 2010 transfer to the new owner",
      amount=None, means="none", evidence="read", cites="2015041300292001",
      detail="8 pages, zero tax, cross-references CRFN 2010000384312. WARNING "
             "this is a DEVR that is NOT A PURCHASE — counting it as a fifth "
             "air-rights buy would have inflated the assemblage. A DEVR with "
             "zero tax may be a confirmation.",
      docs=["2015041300292001"], principal=None),

 dict(id="2015-entitle", happened="2015-05-12", recorded="2015-10-15",
      kind="ENTITLEMENT", headline="Zoning lot formalised for construction",
      amount=None, means="none", evidence="index", cites="[index]",
      detail="Five documents across five distinct dates (2015-04-29 SAGE, "
             "05-12 ZONE, 05-22 CERT, 08-12 SAGE, 10-12 ZONE). Unread.",
      docs=["2015043000681001", "2015051301826001", "2015052900388001",
            "2015091001439001", "2015101301338001"], principal=None),

 dict(id="2015-constr", happened="2015-09-02", recorded="2015-09-17",
      kind="FINANCING", headline="Construction loan — $65.7M, income pledged at $113.7M",
      party_to="LAM GEN 25 LLC",
      amount=65_710_000, means="new_money", evidence="index",
      cites="2015091001439003 + 2015091001439004 [index]",
      detail="Two mortgages, $31,930,000 and $33,780,000, both new money — this "
             "is the one batch where two MTGEs are genuinely additive. AL&R "
             "pledges $113,710,000. THE CONSTRUCTION TRIGGER: the second witness "
             "that a project actually started.",
      docs=["2015091001439002", "2015091001439003", "2015091001439004",
            "2015091001439005"], principal="2015091001439003"),

 dict(id="2016-sage", happened="2016-05-13", recorded="2016-06-16",
      kind="SERVICING", headline="Supporting agreement", amount=None, means="none",
      evidence="index", cites="[index]",
      detail="The only ACRIS trace near delivery. THE HOTEL OPENING IS NOT AN "
             "ACRIS EVENT — PLUTO yearbuilt says 2016; ACRIS records money and "
             "rights and never records that a building exists. That line belongs "
             "to the DOB lane.",
      docs=["2016060801066001"], principal=None),

 dict(id="2018-cons", happened="2018-11-19", recorded="2018-12-03",
      kind="CONSOLIDATION", headline="Consolidated at $48M",
      amount=48_000_000, means="consolidated", evidence="index",
      cites="2018113000347001 [index]",
      detail="WARNING documents ...347002 through ...347005 from this same batch "
             "are indexed against LOT 50 — so lot 50 existed as a separate tax "
             "lot by 2018, BEFORE the 2019 instrument that describes the split.",
      docs=["2018113000347001"], principal="2018113000347001"),

 dict(id="2019-split", happened="2019-05-20", recorded="2019-07-22",
      kind="RIGHTS_SPLIT", headline="One envelope divided into two Lam projects",
      party_from="LAM GEN 25 LLC (lot 49)", party_to="LG CHELSEA LLC (lot 50)",
      person="Jeffrey Lam (signs BOTH sides)",
      amount=None, means="none", evidence="read",
      cites="2019071700601003 p044 (Exhibit D)",
      detail="Filed as EASE; the sixth ZLDA. States the split in a RECITAL: 'the "
             "Lot 50 Land and Lot 49 Land previously constituted a single tax "
             "lot... formerly designated as Lot 49.' The 112,574 sf of acquired "
             "excess splits 56,659 to lot 49 (envelope 141,929) and 55,915 to "
             "lot 50 (envelope 127,035); 8,527 + 7,112 = 15,639. WARNING this "
             "instrument ALLOCATES RIGHTS; the tax lot was already divided by "
             "2018 — the actual split date is a DOF tax-map question, not an "
             "ACRIS one.",
      docs=["2019071700601001", "2019071700601002", "2019071700601003"],
      principal=None),

 dict(id="2020-smis", happened="2020-06-08", recorded="2020-06-16",
      kind="ENTITLEMENT", headline="Miscellaneous instrument, 19 pp — unread",
      amount=None, means="none", evidence="index", cites="[index]",
      detail="Typed SMIS. On this parcel SMIS has been a DECL three times out of "
             "three, so this is a candidate for a declaration and is NOT assumed "
             "to be one.",
      docs=["2020061600455001"], principal=None),

 dict(id="2020-mtge", happened="2020-08-05", recorded="2020-08-19",
      kind="FINANCING", headline="$5M from Shanghai Commercial Bank",
      party_from="SHANGHAI COMMERCIAL BANK", party_to="LAM GEN 25 LLC",
      person="Jeffrey Lam, Manager",
      amount=5_000_000, means="new_money", evidence="read",
      cites="2020081400407001 cover + p037",
      detail="Tax $140,000 = 2.800%, the commercial rate, verified to the cent. "
             "WARNING p37 carries a section 255-a affidavit swearing 'not more "
             "than six residential dwelling units' on a 40-storey hotel with "
             "unitsres = 0. The box did NOT change the tax. Whether it was "
             "appropriate is a legal question the documents do not answer.",
      docs=["2020081400407001", "2020081400407002"], principal="2020081400407001"),

 dict(id="2023-reorg", happened="2023-10-16", recorded="2023-11-06",
      kind="REORG", headline="Entity reorganisation — NOT a sale",
      party_from="LAM GEN 25 LLC", party_to="CHELSEA 25 HOTEL LLC",
      amount=0, means="none", evidence="read", cites="2023110100486001",
      detail="$0 consideration, all taxes $0, SAME ADDRESS on both sides. "
             "Recording this as a $0 sale would corrupt every comparable that "
             "touches this block; dropping it would lose the ownership change. "
             "It is its own event kind for exactly that reason.",
      docs=["2023110100486001"], principal="2023110100486001"),

 dict(id="2023-recap", happened="2023-10-16", recorded="2023-11-06",
      kind="FINANCING", headline="MetLife recapitalisation — $25.49M new inside $265M of face",
      party_from="METROPOLITAN LIFE INSURANCE CO", party_to="CHELSEA 25 HOTEL LLC",
      amount=25_490_000, means="new_money", evidence="read",
      cites="2023110100486009 (MTGE), 2023110100486010 (AGMT)",
      detail="MTGE $25,490,000 taxable IN FULL, tax $713,720 = 2.800% with all "
             "seven components verified. AGMT consolidates $120,000,000 taxable "
             "$0 under exemption 255, cross-referencing 1990 Reel 1707 Page 1285. "
             "Eleven documents whose face sums to $265,490,000. The borrowing "
             "was $25,490,000 — an 18x error for anyone summing a column.",
      docs=["2023102700777001", "2023110100486002", "2023110100486003",
            "2023110100486004", "2023110100486005", "2023110100486006",
            "2023110100486007", "2023110100486008", "2023110100486009",
            "2023110100486010", "2023110100486011"],
      principal="2023110100486009"),

 dict(id="2025-refi", happened="2025-10-16", recorded="2025-10-23",
      kind="FINANCING", headline="$3M new money; position now $123M",
      amount=3_000_000, means="new_money", evidence="index",
      cites="2025101700864003 [index]",
      detail="AGMT restates $123,000,000 (52 pp) and AL&R repeats it. The most "
             "recent lot 49 recording — verified against the live index "
             "2026-08-06, nothing after this date.",
      docs=["2025101700864001", "2025101700864002", "2025101700864003",
            "2025101700864004", "2025101700864005"],
      principal="2025101700864003"),
]

# ---------------------------------------------------------------------------
# WHICH QUESTIONS EACH KIND ANSWERS. Derived from kind, then overridden per
# event where the instrument does something extra — the 2013 Brick Farms deal
# also grants an easement, so it answers ENCUMBER as well as ENVELOPE.
# ---------------------------------------------------------------------------
KIND_ANSWERS = {
    "ACQUISITION":   ["TITLE", "VALUE", "PARTY"],
    "SALE":          ["TITLE", "VALUE", "PARTY"],
    "REORG":         ["TITLE", "PARTY"],
    "FINANCING":     ["ENCUMBER", "CAPITAL", "PARTY"],
    "CONSOLIDATION": ["ENCUMBER", "CAPITAL"],
    "AIR_RIGHTS":    ["ENVELOPE", "VALUE", "PARTY"],
    "ENTITLEMENT":   ["ENVELOPE", "ENCUMBER"],
    "RIGHTS_SPLIT":  ["PARCEL", "ENVELOPE"],
    "SERVICING":     ["ENCUMBER"],
}
ANSWER_EXTRA = {
    "2010-air":   ["ENCUMBER"],           # light-and-air easement granted
    "2013-air3":  ["ENCUMBER"],           # easement above elev. 130 ft
    "2013-air5":  ["ENCUMBER", "PARCEL"], # declaration over all eight lots
    "2019-split": ["TITLE", "PARTY"],     # names both Lam entities and the human
    "1971-deed":  ["ENCUMBER"],           # recites the Greenwich Savings mortgage
    "2014-mtge":  ["ENVELOPE"],           # Exhibit A lists the benefit easements
}

# The OUTSTANDING position after each financing event — a different number from
# the new money, and the one asked for by "what debt is on it".
POSITION_AFTER = {
    "1998-mtge":   226_378.12,
    "2003-cema":   969_656.99,
    "2007-fin":    39_229_334,
    "2012-cema":   39_000_000,
    "2013-fin":    40_500_000,
    "2014-mtge":   48_000_000,
    "2015-constr": 113_710_000,
    "2018-cons":   48_000_000,     # ⚠ LOWER than 2015 — see note below
    "2023-recap":  120_000_000,
    "2025-refi":   123_000_000,
}

# what the decode calls each type when the index is wrong
TRUE_TYPE = {
    "2013052101674003": "DECL", "2013052101674007": "DECL",
    "2013080901116001": "DECL", "2013080901116002": "ZLDA",
    "2019071700601003": "ZLDA", "2015041300292001": "DEVR-CONFIRMATION",
    "2003110900238001": "CEMA", "2012101500666007": "CEMA",
    "2023110100486010": "CEMA", "2007062101109005": "CEMA",
}


def get(u):
    with urllib.request.urlopen(u.replace(" ", "%20")) as r:
        return json.load(r)


def live_index(boro, block, lot):
    ids, off = set(), 0
    while True:
        r = get(f"{LEGALS}?borough={boro}&block={block}&lot={lot}"
                f"&$select=document_id&$order=:id&$limit=1000&$offset={off}")
        ids |= {x["document_id"] for x in r}
        if len(r) < 1000:
            break
        off += 1000
    rows, sid = [], sorted(ids)
    for i in range(0, len(sid), 50):
        w = " in (" + ",".join("'" + c + "'" for c in sid[i:i + 50]) + ")"
        rows += get(f"{MASTER}?$where=document_id{w}&$select=document_id,doc_type,"
                    "document_date,recorded_datetime,document_amt&$limit=200")
    return {r["document_id"]: r for r in rows}


def build():
    idx = live_index("1", "800", "49")

    # ---- the completeness check that would have caught the 1998 deed --------
    assigned, dupes = {}, []
    for e in EVENTS:
        for d in e["docs"]:
            if d in assigned:
                dupes.append((d, assigned[d], e["id"]))
            assigned[d] = e["id"]
    missing = sorted(set(idx) - set(assigned))
    extra = sorted(set(assigned) - set(idx))
    if missing or extra or dupes:
        print("REFUSING TO BUILD — the event map does not cover the index:")
        for m in missing:
            r = idx[m]
            print(f"  UNASSIGNED  {m}  {r.get('doc_type')}  "
                  f"{(r.get('document_date') or '')[:10]}")
        for x in extra:
            print(f"  NOT IN INDEX {x}")
        for d, a, b in dupes:
            print(f"  CLAIMED TWICE {d}: {a} and {b}")
        sys.exit(1)

    docs, events = [], []
    for seq, e in enumerate(EVENTS, 1):
        for d in sorted(e["docs"]):
            r = idx[d]
            is_p = (d == e.get("principal"))
            amt = r.get("document_amt")
            docs.append({
                "bbl": BBL, "document_id": d, "event_id": e["id"],
                "doc_type": r.get("doc_type"),
                "amount_indexed": float(amt) if amt and float(amt) else None,
                "instrument_date": (r.get("document_date") or "")[:10] or None,
                "recorded_date": (r.get("recorded_datetime") or "")[:10] or None,
                "true_type": TRUE_TYPE.get(d, r.get("doc_type")),
                "role": "principal" if is_p else "companion",
                # NULL, not 0, on companions — see the module docstring
                "amount_real": e.get("amount") if is_p else None,
                "amount_means": e.get("means") if is_p else None,
                "evidence": e["evidence"] if is_p else "index",
                "cited_pages": e["cites"] if is_p else None,
                "note": None,
            })
        sf, amt = e.get("sf"), e.get("amount")
        ans = sorted(set(KIND_ANSWERS[e["kind"]]) | set(ANSWER_EXTRA.get(e["id"], [])))
        events.append({
            "bbl": BBL, "event_id": e["id"], "seq": seq,
            "happened": e["happened"],
            "recorded": e.get("recorded") or e["happened"],
            "kind": e["kind"], "headline": e["headline"],
            "party_from": e.get("party_from"), "party_to": e.get("party_to"),
            "person": e.get("person"), "amount": amt,
            "amount_means": e.get("means"),
            "position_after": POSITION_AFTER.get(e["id"]),
            "sf": sf,
            "per_bsf": round(amt / sf, 2) if (amt and sf) else None,
            "answers": ans,
            "evidence": e["evidence"], "cited_pages": e["cites"],
            "detail": e.get("detail"),
        })

    # ---- arithmetic self-checks, refusing rather than reporting a nice number
    air = [x for x in events if x["kind"] == "AIR_RIGHTS" and x["amount"]]
    spend, sf_total = sum(x["amount"] for x in air), sum(x["sf"] for x in air)
    money_rows = [d for d in docs if d["amount_real"] is not None]
    bad = [d for d in money_rows if d["role"] != "principal"]
    assert not bad, f"money on a companion: {bad}"
    print(f"documents {len(docs)}  ·  events {len(events)}  ·  "
          f"money-bearing rows {len(money_rows)}")
    print(f"air rights: ${spend:,.0f} over {sf_total:,.0f} sf = "
          f"${spend/sf_total:,.2f}/BSF avg")
    face = sum(float(d['amount_indexed'] or 0) for d in docs)
    print(f"SUM of amount_indexed across all 96 documents: ${face:,.0f}"
          f"   <-- the number a naive query returns")
    print(f"SUM of amount_real  (new money only):          "
          f"${sum(x['amount'] for x in events if x['amount_means']=='new_money'):,.0f}")

    pos = [x for x in events if x["position_after"]]
    print(f"debt position today: ${pos[-1]['position_after']:,.0f} "
          f"({pos[-1]['happened']})")
    # ⚠ the position must not be assumed monotonic — flag any fall, because a
    # position that DROPS is either a repayment (a real finding) or a decode
    # error, and both deserve to be seen rather than averaged away.
    for a, b in zip(pos, pos[1:]):
        if b["position_after"] < a["position_after"]:
            print(f"  ⚠ POSITION FELL  {a['happened']} ${a['position_after']:,.0f}"
                  f"  ->  {b['happened']} ${b['position_after']:,.0f}"
                  f"   ({b['event_id']}) — repayment or decode error, UNRESOLVED")

    from collections import Counter
    c = Counter(q for x in events for q in x["answers"])
    print("questions ACRIS answers here: " +
          ", ".join(f"{k} {v}" for k, v in c.most_common()))
    print("questions it CANNOT: IDENTIFY, ENTITLE, PERMIT, ASBUILT, COST, "
          "OCCUPY, CONTEXT  -> other lanes")
    return docs, events


def write_csv(docs, events):
    for name, rows in (("acris_documents", docs), ("acris_events", events)):
        p = HERE / f"{name}_{BBL}.csv"
        with open(p, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        print(f"  wrote {p.name}  ({len(rows)} rows)")


def push(docs, events):
    """Upsert into Supabase. Reuses supabase_sync's retrying poster.

    ⚠ The check constraint lives in the DATABASE, not here. If a companion row
    ever carries money, PostgREST returns 400 and the write fails loudly. That
    is the point: a rule enforced only in the writer protects only the writer.
    """
    sys.path.insert(0, str(HERE))
    import supabase_sync as S
    for table, rows, key in (("acris_events", events, "bbl,event_id"),
                             ("acris_documents", docs, "bbl,document_id")):
        try:
            S._post(table, rows, key)
            print(f"  {table:<18} {len(rows):>4} rows -> {S.count(table)} in table")
        except Exception as ex:
            msg = str(ex)
            if "PGRST205" in msg or "404" in msg:
                print(f"  {table:<18} TABLE MISSING — run:  python acris_table.py --ddl")
            else:
                print(f"  {table:<18} FAILED: {msg[:200]}")


if __name__ == "__main__":
    if "--ddl" in sys.argv:
        print(DDL)
        sys.exit(0)
    d, e = build()
    write_csv(d, e)
    if "--push" in sys.argv:
        push(d, e)
