"""THE HAND-READ ANSWER KEY for FT_1680008647768. The slow answer.

Every value here was transcribed by LOOKING AT THE 1800px RENDER, never copied
from any engine's output. `ambiguous` entries are ones the human reader could
not resolve either, so no engine is credited or penalised for them.

⚠ THE POINT OF THIS FILE IS THAT IT EXISTS BEFORE THE OCR RUNS. A key written
after seeing engine output silently inherits that engine's blind spots — the
artifacts it never mentions stop looking like misses and start looking like
things that were not on the page.
"""
import collections
import json
import pathlib

D = "FT_1680008647768"


def A(i, t, v, alts=None):
    return {"id": i, "tier": t, "value": v, "alts": alts or []}


K = collections.OrderedDict()
K["_doc"] = D
K["_note"] = ("HAND-READ FROM THE 1800px RENDER before any OCR was run on this "
              "document. Tiers: CRITICAL = lineage/parcel/party/money breaks "
              "without it. MATERIAL = a function agent wants it. ROUTINE = "
              "boilerplate.")
K["_summary"] = (
    "MTGE recorded 1981-10-02, REEL 586 PAGES 761-770 (sequential). $4,000,000 "
    "from CITIBANK N.A. (399 Park Ave) to 387 P.A.S. ENTERPRISES, a NY limited "
    "partnership c/o O.S.L. Shipping & Development, 1270 Ave of the Americas. "
    "General partner Sisson Realty N.V. Inc.; signed by attorney-in-fact Ariel "
    "Gratch under a POA dated 1981-09-14, acknowledged 1981-09-17 before notary "
    "Elliott Bakst. Premises = Section 3 BLOCK 883 LOT 1, New York County: the NE "
    "corner of E 27th St and Fourth Ave (now PARK AVENUE SOUTH), 98 ft 9 in by "
    "166 ft 8 in. Recording tax $60,000 incl. $10,000 special additional.")
K["_structure"] = (
    "p1 mortgage first page (marked-up conformed copy) | p2 Schedule A | p3 SAME "
    "first page, clean duplicate | p4 covenants 1-5a | p5 covenants 5b-13 | p6 "
    "covenants 14-17 (Art 16 = assignment of leases and rents) | p7 Article 18 "
    "defaults a-p | p8 covenants 22-27 | p9 covenants 28-32 + execution | p10 "
    "acknowledgement + backer")
K["_match_checks"] = [
    "$4,000,000 x 1.5% = $60,000 -> equals the handwritten figure on p1 AND the "
    "RECORDING TAX stamp on p10",
    "p1 bottom column 40,000 + 10,000 + 10,000 = 60,000 -> internally consistent",
    "'387 P.A.S.' in the mortgagor name = 387 Park Avenue South -> independently "
    "confirmed by Schedule A (Fourth Ave = Park Ave South, corner of 27th)",
    "p1 left-margin scrawl '883 / 1' = BLOCK 883 LOT 1 printed on the p10 backer",
    "map recorded=1981-10-02 -> register stamp '1981 OCT 2 AM 10:25' and '(S) 10-2-81'",
    "metes and bounds CLOSES: N 98-9, E 166-8, S 98-9, W 166-8 (a rectangle)",
    "chronology: POA 1981-09-14 < acknowledged 1981-09-17 < recorded 1981-10-02",
]

K["p001.png"] = {"kind": "mortgage first page, MARKED-UP conformed copy - the money page", "artifacts": [
    A("reel", "CRITICAL", "REEL 586", ["REEL586", "586"]),
    A("reel_page", "CRITICAL", "761"),
    A("doc_type", "CRITICAL", "THIS MORTGAGE"),
    A("year", "CRITICAL", "1981"),
    A("mortgagor", "CRITICAL", "387 P.A.S. ENTERPRISES", ["387 P.A.S.ENTERPRISES", "387 PAS ENTERPRISES"]),
    A("mortgagor_form", "CRITICAL", "a New York limited partnership", ["New York limited partnership"]),
    A("care_of", "MATERIAL", "Shipping & Development", ["O.S.L. Shipping", "OSL Shipping"]),
    A("mortgagor_addr", "CRITICAL", "1270 Avenue of the Americas"),
    A("mortgagor_zip", "MATERIAL", "10021"),
    A("mortgagee", "CRITICAL", "CITIBANK, N.A.", ["CITIBANK N.A.", "CITIBANK"]),
    A("mortgagee_form", "MATERIAL", "a national banking association"),
    A("mortgagee_addr", "CRITICAL", "399 Park Avenue"),
    A("mortgagee_zip", "MATERIAL", "10043"),
    A("amount_words", "CRITICAL", "Four Million"),
    A("amount_figs", "CRITICAL", "$4,000,000", ["4,000,000"]),
    A("witnesseth", "ROUTINE", "WITNESSETH"),
    A("the_note", "ROUTINE", "the Note"),
    A("schedule_a", "CRITICAL", "Schedule A"),
    A("bldg_equip", "MATERIAL", "Building Equipment"),
    A("ucc", "MATERIAL", "Section 9-105 of the Uniform Commercial Code", ["Section 9-105"]),
    A("sec_agree", "ROUTINE", "Security Agreements"),
    A("eminent", "MATERIAL", "eminent domain"),
    A("so_in_orig", "MATERIAL", "SO IN ORIGINAL")],
    "ambiguous": [
    {"id": "exec_day", "note": "day of month left blank/faded on the form"},
    {"id": "exec_month", "note": "month left blank/faded on the form"},
    {"id": "hw_tax_top", "note": "handwritten '$60,000.00' top-left margin - handwriting"},
    {"id": "hw_block_lot", "note": "handwritten '883' and '1' left margin - matches p10 but is a scrawl"},
    {"id": "hw_tax_column", "note": "handwritten column 40,000/10,000/10,000/60,000 bottom-left"}]}

K["p002.png"] = {"kind": "SCHEDULE A - the legal description; closes as a rectangle", "artifacts": [
    A("reel", "CRITICAL", "REEL 586", ["586"]),
    A("reel_page", "CRITICAL", "762"),
    A("schedule", "CRITICAL", "SCHEDULE A"),
    A("borough", "CRITICAL", "Borough of Manhattan"),
    A("county", "CRITICAL", "County and State of New York"),
    A("begin", "CRITICAL", "BEGINNING at the corner", ["BEGINNING"]),
    A("street", "CRITICAL", "27th Street"),
    A("avenue", "CRITICAL", "Fourth Avenue"),
    A("side1", "MATERIAL", "Northerly side of 27th Street"),
    A("side2", "MATERIAL", "Easterly side of Fourth Avenue"),
    A("dim_ns", "CRITICAL", "98 feet 9 inches"),
    A("dim_ew", "CRITICAL", "166 feet 8 inches"),
    A("centerline", "MATERIAL", "center line of the block"),
    A("cross_st", "MATERIAL", "28th Streets", ["27th and 28th Streets"]),
    A("alias", "CRITICAL", "PARK AVENUE SOUTH"),
    A("alias_phrase", "CRITICAL", "now known as PARK AVENUE SOUTH", ["is now known as"])],
    "ambiguous": [{"id": "stray_head", "note": "faint typed fragment above SCHEDULE A, illegible"}]}

K["p003.png"] = {"kind": "mortgage first page AGAIN - clean duplicate of p1, no annotations", "artifacts": [
    A("reel", "CRITICAL", "REEL 586", ["586"]),
    A("reel_page", "CRITICAL", "763"),
    A("mortgagor", "CRITICAL", "387 P.A.S. ENTERPRISES", ["387 P.A.S.ENTERPRISES"]),
    A("mortgagee", "CRITICAL", "CITIBANK, N.A.", ["CITIBANK"]),
    A("amount_words", "CRITICAL", "Four Million"),
    A("amount_figs", "CRITICAL", "$4,000,000", ["4,000,000"]),
    A("mortgagor_addr", "CRITICAL", "1270 Avenue of the Americas"),
    A("mortgagee_addr", "CRITICAL", "399 Park Avenue"),
    A("year", "CRITICAL", "1981"),
    A("schedule_a", "MATERIAL", "Schedule A"),
    A("bldg_equip", "MATERIAL", "Building Equipment"),
    A("witnesseth", "ROUTINE", "WITNESSETH")],
    "ambiguous": [{"id": "exec_date", "note": "day and month blank on this copy too"}]}

K["p004.png"] = {"kind": "covenants 1-5(a); HANDWRITTEN interlineations change legal meaning", "artifacts": [
    A("reel", "CRITICAL", "REEL 586", ["586"]),
    A("reel_page", "CRITICAL", "764"),
    A("covenants", "ROUTINE", "covenants with the Mortgagee"),
    A("insurance", "MATERIAL", "extended coverage endorsement"),
    A("flood", "MATERIAL", "National Flood Insurance Act"),
    A("hud", "MATERIAL", "Housing and Urban Development"),
    A("rpl254", "CRITICAL", "Section 254 of the Real Property Law", ["Section 254"]),
    A("renewal", "MATERIAL", "fifteen (15) days", ["fifteen 15 days"]),
    A("rider_tenant", "CRITICAL", "except for tenant work and cosmetic work",
      ["tenant work and cosmetic work"]),
    A("rider_struct", "MATERIAL", "does not affect the structure of the building"),
    A("taxes", "MATERIAL", "water rates, sewer rents"),
    A("art4", "ROUTINE", "Article 4"),
    A("art13", "ROUTINE", "Article 13")],
    "ambiguous": [
    {"id": "hw_commonly", "note": "handwritten 'commonly' inserted over struck text"},
    {"id": "hw_reasonably", "note": "handwritten 'reasonably' inserted over struck text"}]}

K["p005.png"] = {"kind": "covenants 5(b)-13; heavy strikethrough + typed insertions", "artifacts": [
    A("reel", "CRITICAL", "REEL 586", ["586"]),
    A("reel_page", "CRITICAL", "765"),
    A("escrow", "CRITICAL", "one-twelfth (1/12)", ["one twelfth"]),
    A("receiver", "CRITICAL", "appointment of a receiver"),
    A("estoppel", "MATERIAL", "offsets or defenses exist"),
    A("warrants", "CRITICAL", "warrants the title to the Premises"),
    A("one_parcel", "MATERIAL", "sold in one parcel"),
    A("counsel", "MATERIAL", "reasonable counsel fees"),
    A("repair", "MATERIAL", "good condition and repair"),
    A("waste", "MATERIAL", "commit or suffer any waste"),
    A("rider_law", "CRITICAL", "unless required by law or court decree",
      ["required by law or court decree"]),
    A("emdomain", "MATERIAL", "eminent domain"),
    A("ten_days", "MATERIAL", "within ten days upon request"),
    A("art18", "ROUTINE", "Article 18")],
    "ambiguous": [
    {"id": "struck_5b", "note": "opening of 5(b) struck: 'at its option to be exercised by twenty (20) days written notice'"},
    {"id": "struck_7", "note": "'within five days upon request in person or' struck"},
    {"id": "hw_shall", "note": "'may' struck, 'shall' typed above, in covenant 8"}]}

K["p006.png"] = {"kind": "covenants 14-17; Article 16 = ASSIGNMENT OF LEASES AND RENTS", "artifacts": [
    A("reel", "CRITICAL", "REEL 586", ["586"]),
    A("reel_page", "CRITICAL", "766"),
    A("inspect", "MATERIAL", "enter and inspect the Premises"),
    A("financials", "MATERIAL", "generally accepted accounting principles"),
    A("ninety", "MATERIAL", "ninety (90) days", ["ninety 90 days"]),
    A("rent_roll", "CRITICAL", "rent roll showing the names of tenants", ["rent roll"]),
    A("psf", "MATERIAL", "per square foot"),
    A("assign_rents", "CRITICAL", "assigns to the Mortgagee"),
    A("rents_phrase", "CRITICAL", "rents, issues and profits"),
    A("quiet", "MATERIAL", "covenant of quiet enjoyment"),
    A("dispossess", "MATERIAL", "usual summary proceedings"),
    A("rpl291f", "CRITICAL", "Section 291-f of the Real Property Law", ["Section 291-f"]),
    A("five_years", "MATERIAL", "not less than five (5) years", ["five 5 years"]),
    A("sublease", "MATERIAL", "leases or subleases")],
    "ambiguous": [
    {"id": "hw_14", "note": "handwritten insertion in covenant 14 over struck text, partly illegible"},
    {"id": "hw_17", "note": "handwritten insertion in covenant 17 over struck text, partly illegible"},
    {"id": "hw_materially", "note": "'materially' handwritten in 17, low confidence"}]}

K["p007.png"] = {"kind": "ARTICLE 18 events of default (a)-(p) + negotiated change-of-control carve-out", "artifacts": [
    A("reel", "CRITICAL", "REEL 586", ["586"]),
    A("reel_page", "CRITICAL", "767"),
    A("default", "CRITICAL", "due at the option of the Mortgagee"),
    A("five_days", "MATERIAL", "five (5) days", ["five 5 days"]),
    A("twenty_days", "MATERIAL", "twenty (20) days", ["twenty 20 days"]),
    A("thirty_days", "MATERIAL", "thirty (30) days", ["thirty 30 days"]),
    A("judgment", "CRITICAL", "Fifty Thousand ($50,000)", ["$50,000", "Fifty Thousand"]),
    A("bankruptcy", "MATERIAL", "petition in bankruptcy"),
    A("receiver", "MATERIAL", "receiver, liquidator or trustee"),
    A("due_on_sale", "CRITICAL", "sold or otherwise transferred"),
    A("stock", "CRITICAL", "controlling amount of its voting stock"),
    A("partnership", "CRITICAL", "partnership, joint venture, syndicate"),
    A("carveout", "CRITICAL", "remains the general partner",
      ["Sisson Realty, N.V., Inc. remains the general partner", "except in such circumstances"]),
    A("sisson", "CRITICAL", "Sisson Realty", ["Sisson Realty, N.V., Inc."]),
    A("lien_law", "CRITICAL", "Section 13 of the Lien Law", ["Lien Law"]),
    A("trust_fund", "MATERIAL", "trust fund")],
    "ambiguous": [
    {"id": "struck_18e", "note": "'if without such consent the Mortgagor shall further encumber the Premises for debt' struck"}]}

K["p008.png"] = {"kind": "covenants 22-27", "artifacts": [
    A("reel", "CRITICAL", "REEL 586", ["586"]),
    A("reel_page", "CRITICAL", "768"),
    A("stamps", "MATERIAL", "internal revenue stamps"),
    A("ucc_fs", "CRITICAL", "Uniform Commercial Code Financing Statement", ["Financing Statement"]),
    A("debtor", "MATERIAL", "Debtor and Secured Party"),
    A("ucc9402", "CRITICAL", "Section 9-402(2)(e)", ["9-402"]),
    A("moratorium", "MATERIAL", "stay or extension or moratorium law"),
    A("marshaled", "MATERIAL", "Premises marshaled"),
    A("joint_several", "CRITICAL", "jointly and severally liable"),
    A("rpl254", "CRITICAL", "Section 254 of the Real Property Law", ["Section 254"]),
    A("valid_lien", "MATERIAL", "valid mortgage lien upon the Premises"),
    A("form_rev", "ROUTINE", "Mtg. Rev. 1/80", ["Mtg Rev 1/80"])],
    "ambiguous": [
    {"id": "hw_adversely", "note": "'adversely' handwritten into covenant 24 over struck text"}]}

K["p009.png"] = {"kind": "covenants 28-32 + EXECUTION; clause 32 typed in a different face (negotiated rider)", "artifacts": [
    A("reel", "CRITICAL", "REEL 586", ["586"]),
    A("reel_page", "CRITICAL", "769"),
    A("late_charge", "CRITICAL", "four cents for each dollar", ["four cents"]),
    A("arrears", "MATERIAL", "ten (10) days in arrears", ["ten 10 days"]),
    A("cure_mon", "CRITICAL", "monetary default - 10 days", ["monetary default 10 days"]),
    A("cure_non", "CRITICAL", "non-monetary default - 30 days", ["non-monetary default 30 days"]),
    A("art18a", "MATERIAL", "Article 18(a)"),
    A("run_with_land", "CRITICAL", "run with the land"),
    A("witness", "ROUTINE", "IN WITNESS WHEREOF"),
    A("presence", "ROUTINE", "IN PRESENCE OF"),
    A("mortgagor", "CRITICAL", "387 P.A.S. ENTERPRISES", ["387 P.A.S.ENTERPRISES"]),
    A("gen_partner", "CRITICAL", "Sisson Realty, N.V., Inc.", ["Sisson Realty"]),
    A("gp_title", "CRITICAL", "General Partner"),
    A("aif", "CRITICAL", "Attorney-in-Fact", ["Attorney in Fact"]),
    A("no_recourse", "CRITICAL", "without personal", ["without personal liability"]),
    A("form_rev", "ROUTINE", "Mtg. Rev. 1/80", ["Mtg Rev 1/80"])],
    "ambiguous": [
    {"id": "sig_aif", "note": "attorney-in-fact signature, cursive, approximately 'A. Gratch' - not legible alone"},
    {"id": "sig_witness", "note": "witness signature, cursive, approximately 'Stuart ...' - illegible"}]}

K["p010.png"] = {"kind": "ACKNOWLEDGEMENT + BACKER - the parcel key and every recording stamp", "artifacts": [
    A("reel", "CRITICAL", "REEL 586", ["586"]),
    A("reel_page", "CRITICAL", "770"),
    A("ack_day", "CRITICAL", "17 day of September", ["day of September"]),
    A("ack_year", "CRITICAL", "1981"),
    A("aif_name", "CRITICAL", "Ariel Gratch", ["Arial Gratch"]),
    A("aif_role", "CRITICAL", "attorney-in-fact"),
    A("gen_partner", "CRITICAL", "Sisson Realty", ["Sisson Realty, N.V., Inc."]),
    A("partnership", "CRITICAL", "387 P.A.S.", ["387 P.A.S. Enterprises"]),
    A("poa", "CRITICAL", "power of attorney"),
    A("poa_simul", "CRITICAL", "recorded simultaneously", ["simultaneously herewith"]),
    A("notary", "CRITICAL", "ELLIOTT BAKST", ["Elliott Bakst"]),
    A("notary_no", "CRITICAL", "24-0141715", ["No 24-0141715"]),
    A("notary_county", "MATERIAL", "Kings County", ["Qual. in Kings County"]),
    A("notary_exp", "MATERIAL", "March 30, 1983"),
    A("section", "CRITICAL", "SECTION 3"),
    A("block", "CRITICAL", "BLOCK 883", ["883"]),
    A("lot", "CRITICAL", "LOT 1"),
    A("county", "CRITICAL", "NEW YORK"),
    A("instrument", "CRITICAL", "Mortgage"),
    A("title_no", "CRITICAL", "732441", ["7,32441"]),
    A("to_citibank", "CRITICAL", "CITIBANK, N.A.", ["CITIBANK"]),
    A("return_to", "CRITICAL", "JOHN GUTHEIL", ["John Gutheil"]),
    A("law_firm", "CRITICAL", "TRUBIN SILLCOCKS EDELMAN & KNAPP", ["Trubin Sillcocks"]),
    A("firm_addr", "MATERIAL", "375 PARK AVENUE"),
    A("firm_zip", "MATERIAL", "10022"),
    A("file_no", "MATERIAL", "35201"),
    A("title_co", "CRITICAL", "ABSTRACT CORP", ["TITLE ABSTRACT CORP"]),
    A("title_addr", "MATERIAL", "280 BROADWAY"),
    A("title_zip", "MATERIAL", "10007"),
    A("rec_tax", "CRITICAL", "RECORDING TAX"),
    A("rec_date", "CRITICAL", "1981 OCT 2", ["OCT 2 1981"]),
    A("rec_time", "MATERIAL", "AM 10:25", ["10:25"]),
    A("register", "CRITICAL", "CITY REGISTER", ["OFFICE OF CITY REGISTER"]),
    A("register_co", "MATERIAL", "New York County"),
    A("recorded", "ROUTINE", "RECORDED"),
    A("seal", "ROUTINE", "official seal", ["Witness my hand and official seal"]),
    A("serial", "MATERIAL", "12973"),
    A("form_rev", "ROUTINE", "Mtg Rev. 1/80", ["Mtg Rev 1/80"])],
    "ambiguous": [
    {"id": "hw_rec_tax_amt", "note": "'$60,000' handwritten diagonally across the RECORDING TAX stamp"},
    {"id": "hw_received", "note": "RECEIVED Recording Tax of $__ / Addt'l Tax of $__ - handwritten 60,000 and 10,000"},
    {"id": "serial_no", "note": "SERIAL NO. handwritten, partly overprinted"},
    {"id": "sig_register", "note": "City Register signature, cursive, illegible"},
    {"id": "loc_ver", "note": "'LOC. VER.' handwritten annotation top-right, illegible"},
    {"id": "usr", "note": "'(USR 11836)' beside the title number - handwritten, digits uncertain"}]}

p = pathlib.Path("answer_key_testdoc.json")
p.write_text(json.dumps(K, indent=1, ensure_ascii=False), encoding="utf-8")

pages = [k for k in K if not k.startswith("_")]
na = sum(len(K[k]["artifacts"]) for k in pages)
nm = sum(len(K[k].get("ambiguous") or []) for k in pages)
tc = collections.Counter(a["tier"] for k in pages for a in K[k]["artifacts"])
print(f"  {p}")
print(f"  {len(pages)} pages | {na} artifacts | {nm} ambiguous excluded")
print(f"  {dict(tc)}\n")
for k in pages:
    c = collections.Counter(a["tier"] for a in K[k]["artifacts"])
    print(f"    {k}  {len(K[k]['artifacts']):>3} art "
          f"({c['CRITICAL']}C/{c['MATERIAL']}M/{c['ROUTINE']}R)  "
          f"{len(K[k].get('ambiguous') or []):>2} amb")
