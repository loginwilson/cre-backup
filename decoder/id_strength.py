"""Identification strength by DOCUMENT TYPE — which document to pull for a person.

Login's observation, 2026-08-05: across document types you meet no signature,
then a signature, then PRINT, then full contact — and the difference is a
property of the TYPE, not the instance. Once it is written down you stop hunting
page by page and start REACHING for the right document.

Five levels, each strictly stronger than the last:

    none          the type identifies no human at all
    signature     a handwritten mark + a printed TITLE. Proves the ACT; the name
                  is low-confidence (see SIGNATURE_LADDER.md)
    printed_name  the name appears typed somewhere — jurat, party index, exhibit
    addressed     name + a street address you could write to
    full_contact  name + address + PHONE, and sometimes email

`observed` is the honest part. A level recorded from a page actually read in this
pilot is `observed: True`. Everything else is an EXPECTATION from the source
workbooks and is marked False — it tells you where to look, not what you will
find, and must not be quoted as if it were measured.
"""
import json

LEVELS = ["none", "signature", "printed_name", "addressed", "full_contact"]


def rank(level):
    return LEVELS.index(level)


REGISTRY = {
    # ---- ACRIS, observed in this pilot ------------------------------------
    "DEVR/ZLDA": {
        "level": "full_contact", "observed": True,
        "carries": ["signature block with TITLE", "jurat naming the signatory + notary",
                    "NOTICES block: party, counsel, attention-party, address, phone, fax",
                    "sealed certifications (architect, with licence number)"],
        "note": "the strongest ACRIS type seen. Notices give a named human behind an SPE "
                "with a phone, from 2004 onward. But the block is not universal — "
                "2014091201052002 has a jurat and no notices."},
    "DECL": {"level": "signature", "observed": True,
             "carries": ["signature block", "jurat"],
             "note": "declarants sign; contact detail generally lives in the paired ZLDA"},
    "DEED": {"level": "printed_name", "observed": False,
             "carries": ["signature", "jurat", "typed party index entry"],
             "note": "EXPECTATION. Deeds are where handwriting is worst; the typed rung "
                     "is the ACRIS party index, not the instrument."},
    "MTGE": {"level": "addressed", "observed": False,
             "carries": ["lender notice address", "borrower notice address"],
             "note": "EXPECTATION. Mortgages carry notice addresses for both sides."},
    "MLEA": {"level": "addressed", "observed": False,
             "carries": ["landlord and tenant notice addresses"],
             "note": "EXPECTATION. Memorandum of Lease — the ground-lease thread."},

    # ---- the ACRIS INDEX (not a document) ----------------------------------
    "ACRIS party index 636b-3b5g": {
        "level": "addressed", "observed": True,
        "carries": ["entity name TYPED", "street address"],
        "note": "⚠ UNDER-REPORTS. For 2017053000419005 it lists three entities and OMITS "
                "the First Presbyterian Church, which signed the instrument. Entities only "
                "— never individuals."},

    # ---- other sources, from the workbooks ---------------------------------
    "DOB PW1 §26": {"level": "full_contact", "observed": False,
                    "carries": ["owner name", "title", "business", "PHONE", "EMAIL"],
                    "note": "EXPECTATION, and the richest rung mapped. ⚠ the BIS page renders "
                            "§1–§24 then throws — §26 exists only in the PDF."},
    "HPD registration contacts feu5-w2e2": {
        "level": "addressed", "observed": False,
        "carries": ["head officer", "managing agent", "SHAREHOLDER", "business address"],
        "note": "EXPECTATION. Refreshed ANNUALLY (calendar-driven), so it ages differently "
                "from anything event-driven. ⚠ no phone in the open feed. Shareholder is "
                "the only public route into co-op ownership."},
    "LPC permit dpm2-m9mq": {"level": "addressed", "observed": False,
                             "carries": ["applicant", "OWNER of record", "mailing addresses"],
                             "note": "EXPECTATION. Names both sides, independent of ACRIS."},
    "DOF DAB Auth_for_Change": {"level": "printed_name", "observed": True,
                                "carries": ["SURVEYOR firm", "survey date", "cited CRFNs"],
                                "note": "observed: 'Survey by: Earl B. Lovell- S.P. Belcher Inc, "
                                        "Survey Date: 11/30/2012'. Firms, not individuals."},
    "NYS DOS corporate filings": {"level": "addressed", "observed": False,
                                  "carries": ["officers", "address for service of process"],
                                  "note": "EXPECTATION, and the rung that turns an SPE into "
                                          "PEOPLE. Not yet touched."},
}


def best_source_for(level="full_contact", observed_only=False):
    """Which document types reach at least this identification level."""
    want = rank(level)
    rows = [(k, v) for k, v in REGISTRY.items() if rank(v["level"]) >= want
            and (v["observed"] or not observed_only)]
    return sorted(rows, key=lambda kv: (-rank(kv[1]["level"]), kv[0]))


if __name__ == "__main__":
    print(f"{'document type':<38} {'level':<14} observed  carries")
    for k, v in sorted(REGISTRY.items(), key=lambda kv: (-rank(kv[1]["level"]), kv[0])):
        mark = "yes" if v["observed"] else "EXPECTED"
        print(f"  {k:<36} {v['level']:<14} {mark:<9} {v['carries'][0][:40]}")
    print("\nreaching a named human with a phone — CONFIRMED sources only:")
    for k, v in best_source_for("full_contact", observed_only=True):
        print(f"  {k}: {v['note'][:100]}")
    print("\nreaching a named human with a phone — still only EXPECTED:")
    for k, v in best_source_for("full_contact"):
        if not v["observed"]:
            print(f"  {k}: {v['note'][:100]}")
