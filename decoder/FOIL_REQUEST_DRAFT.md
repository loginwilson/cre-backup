# FOIL request — ACRIS document images in bulk

**Status: DRAFT for Login to review, fill in and send.** Nothing has been sent.

## Why this route

New York's Freedom of Information Law (Public Officers Law, Article 6) obliges an
agency to provide records in the medium requested where it can do so, and — the
part that matters here — **§87(1)(b)(iii) limits the fee for electronic records to
the actual cost of reproduction**, not a commercial licence price. DOF's published
"Index and Image Electronic Data Services" schedule quotes **$8,670 for 30 days**
of real-property images citywide and **$93,640 for a year**. A FOIL request is a
different legal basis for the same records and is the cheapest legitimate path.

**Expect resistance.** Agencies commonly argue that records they also sell
commercially are "available in another form", and some read the fee provision
narrowly. That is worth testing: the request costs a letter, and the worst
realistic outcome is being pointed back at the subscription you already know
about. Ask for the subset, not everything, so the request is hard to refuse as
burdensome.

## Send to

**Records Access Officer, NYC Department of Finance**
Look up the current RAO and address at nyc.gov/finance before sending — do not
guess. NYC also runs a central FOIL portal (OpenRecords) which timestamps the
request and starts the statutory clock; prefer it to email.

The City Register (212-487-6300) administers ACRIS and is worth a call in
parallel, with one question ahead of price: **does the subscription deliver bulk
transfer of images, or only credentials to the online viewer?** If the latter, it
is worthless at this scale and the FOIL route is the only one.

---

## Draft

Subject: FOIL request — bulk copy of ACRIS document images (electronic)

To the Records Access Officer:

Under the Freedom of Information Law, Public Officers Law Article 6, I request a
copy of the following records held by the Department of Finance, Office of the
City Register.

**Records requested**

Digital images of recorded real property instruments in the Automated City
Register Information System (ACRIS), limited to the following document classes:

  ZONE (Zoning Lot Description) · DEVR (Development Rights) · AIRRIGHT (Air
  Rights) · EASE (Easement) · DECL (Declaration) · AGMT (Agreement) · SAGE
  (Sundry Agreement) · SMIS (Sundry Miscellaneous) · CERT (Certificate) ·
  MISC (Miscellaneous) · TERA (Termination of Agreement) · LDMK (Landmark
  Designation) · LIC (License) · CONS (Consent) · DEED, RC (Deed with
  Restrictive Covenant)

for all boroughs, for all recording dates available in ACRIS.

Per the ACRIS index published on NYC Open Data (dataset bnx9-e6tj), these classes
comprise approximately **1.28 million documents**, which is about **7.5%** of the
17.0 million documents in ACRIS. I am requesting a defined subset rather than the
complete image library specifically to keep the request narrow.

**Format requested**

Electronic copies in their native format (TIFF), delivered in bulk by whichever
means the Department finds least burdensome: physical media supplied at my
expense, SFTP or other network transfer, or a cloud storage location to which I
am granted read access. I will supply storage media or a destination bucket if
that is helpful.

I also request any accompanying manifest or index that maps image files to
document identifiers, so the images can be associated with the corresponding
ACRIS index records.

**Fees**

I am willing to pay the actual cost of reproduction as provided by Public Officers
Law §87(1)(b)(iii). Please advise of the estimated cost before incurring it. If
the estimated cost exceeds $500, please contact me first.

**If the request is too broad**

If the Department considers this request unreasonably burdensome, I would welcome
a conversation about narrowing it. I would accept, in order of preference:

  1. the classes above for Manhattan only (approximately 6,204 of the 9,068
     parcel records in the development-rights subset);
  2. the classes ZONE, DEVR, AIRRIGHT, EASE and DECL only (approximately 87,000
     documents);
  3. the classes ZONE, DEVR and AIRRIGHT only (approximately 47,000 documents).

**Response**

Please acknowledge this request within five business days as required by
§89(3)(a). If any portion is denied, please cite the specific exemption relied
upon and identify the person to whom an appeal may be directed.

I can be reached at [EMAIL] and [PHONE].

Sincerely,
[NAME]
[ADDRESS]

---

## Before sending — fill in / check

- [ ] current Records Access Officer name and address (nyc.gov/finance)
- [ ] submit via NYC OpenRecords portal rather than email if possible
- [ ] your name, address, email, phone
- [ ] decide the fee ceiling (draft says $500)
- [ ] keep a copy and diary the 5-business-day acknowledgement date

## If it is granted

Switch the architecture from **fetch → read → delete** to **store → query**.
Today's session fixed eight parser bugs; with transient images, only the
transcriptions already made could be re-checked, so anything mis-read before a
fix stayed mis-read. With the corpus in hand every parser improvement re-runs
against everything. Storage is not the constraint — the requested subset is
roughly **0.3–1.4 TB**, about **$70–300 a year** to host.
