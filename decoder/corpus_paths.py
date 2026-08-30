"""WHERE DOES EVERY FILE LIVE? One answer, imported everywhere.

⚠ WHY THIS EXISTS. Login, 2026-08-18, looking at 19 loose files at the corpus root:
*"this is how disorganization forms. are they important and if they are, then you should
probably be put into some kind of folder."* They were all important — a ledger, singleton
PID files, the refusal flag, run logs, worklists, audit results — and every one of them
had been dropped at the top level by whichever script happened to need it.

⚠ THE STRUCTURAL FIX IS NOT A TIDY-UP, IT IS A SINGLE SOURCE OF TRUTH. Sweeping the
files into folders once just delays the mess: the next script still writes
`ROOT / "whatever.log"`. Paths belong in ONE module that everything imports, so a new
file cannot land in the wrong place without editing this file first.

    D:/acris/
      00-run/            operational state — NOT the corpus, safe to delete and rebuild
        state/           ledger.sqlite · *.pid · _STOP        (the run's memory)
        logs/            *.log                                (append-only history)
        worklists/       *.txt                                (job inputs, derived)
        audits/          *.json                               (verification results)
      01-specification/  the index: what EXISTS
      02-acquisition/    documents/ (the one copy) · by-parcel/ (the readable view)
      backup/            code and irreplaceable non-corpus data
      _legacy-pages/     pre-PDF loose page corpus, kept until superseded

⚠ 00-run IS DISPOSABLE, 01/02 ARE NOT. Everything under 00-run can be rebuilt by
re-running; the ledger only records what was fetched and could be re-derived from the
store itself. Keeping that boundary visible is the point of the numbering.
"""
from __future__ import annotations

import os
import pathlib
import re as _re

# ⚠ RESTRUCTURED 2026-08-19 (Login's layout): phase -> phase.md + source folder ->
# source.md + source Outputs. The corpus root is now the Commercial Real Estate
# Decoding folder; "acris" no longer exists on the drive.
# ⚠ MOVED AGAIN 2026-08-20 (login): the old tree was RENAMED INTO D:\Ignore
# — "the old tree is supposed to be ignored", literally. The system tree
# (D:\CRE Decoding System) is where the mds + the one nav table live; this
# ROOT covers the LEGACY outputs (sync state, spec db, old acquisition)
# until each migrates deliberately. Discovered when the spec attach died
# mid-keying: the path a config asserts is a claim like any other.
ROOT = pathlib.Path(os.environ.get("ACRIS_CORPUS_ROOT", "D:/Ignore"))

# ── THE SYSTEM TREE'S PHASES ────────────────────────────────────────────────
# ⚠ THE NUMBER IS A DISPLAY DETAIL. THE NAME IS THE IDENTITY.
#
# Login 2026-08-23: *"we now need a monitorization folder so everything bumps up
# a number like sync becoming 01."* Monitorization is a real phase (phase_monitor
# has been running as a service since last night) and it belongs at 00, which
# pushes every folder below it up one.
#
# That renumber would have edited 26 hardcoded paths across 22 files — and the
# NEXT renumber would edit them all again. So the fix is not to change the
# numbers in the code, it is to stop the code from knowing them: `phase()`
# resolves a folder by its NAME and accepts whatever two-digit prefix is on
# disk. Rename `00 Synchronizations` to `01 Synchronizations` and every caller
# keeps working, with no edit and no restart.
#
# ⚠ IT RESOLVES AGAINST THE DISK, NOT AGAINST THIS TABLE. The glob is the
# authority; PHASE_ORDER below is only the number to use when CREATING a folder
# that does not exist yet. A table that disagrees with the filesystem must lose,
# because the filesystem is what the lanes actually write to.
SYS = pathlib.Path(r"D:\CRE Decoding System")

PHASE_DIRS = {
    "monitorization": "Monitorizations",
    "synchronization": "Synchronizations",
    "navigation": "Navigations",
    "acquisition": "Acquisitions",
    "organization": "Organizations",
    "extraction": "Extractions",
    "resolution": "Resolutions",
    "derivation": "Derivations",
    "productization": "Productizations",
}
# the intended numbering AFTER the 2026-08-23 bump — used only to create
PHASE_ORDER = {n: i for i, n in enumerate(PHASE_DIRS)}


def phase(name):
    """The folder for a phase, whatever number currently prefixes it.

    ⚠ Never build a system-tree path from a literal like "00 Synchronizations".
    That literal is a claim about the numbering, and the numbering changed."""
    want = PHASE_DIRS[name]
    hit = sorted(SYS.glob("[0-9][0-9] " + want))
    if hit:
        return hit[0]
    return SYS / ("%02d %s" % (PHASE_ORDER[name], want))


MONITOR_DIR = phase("monitorization")
SYNC_DIR = phase("synchronization")
NAV_DIR = phase("navigation")
ACQ_DIR = phase("acquisition")
ORG_DIR = phase("organization")

RUN = (ROOT / "00 Live Syncs" / "Legal Instruments Live Sync"
       / "Legal Instruments Live Sync Outputs")
STATE = RUN / "state"
LOGS = RUN / "logs"
WORKLISTS = RUN / "worklists"
AUDITS = RUN / "audits"
ARCHIVE = RUN / "Raw source archive"     # landed raw pulls — rebuild insurance

SPEC = (ROOT / "01 Specifications" / "Legal Instruments Specification"
        / "Legal Instruments Specification Outputs")
SPEC_DB = SPEC / "parcel_spec.db"
INDEX = RUN / "Working state"            # live pull state: rc_detail.jsonl etc.
NOIMAGE_IDS = INDEX / "noimage_ids.txt"
NOIMAGE_INDEX = INDEX / "noimage_index"

# ⚠ NAV LIVES IN THE SYSTEM TREE (login, 2026-08-20): "that level 3 of the
# cre decoding system folder is meant to be legal instruments md and ONE
# TABLE that constantly updates when sync hands it new doc id." So level 3
# holds exactly: the md + the table, named as a pair. Everything
# operational - ledgers, logs, state, superseded builds, sorted views -
# lives under _working, out of sight. The old Commercial-Real-Estate-
# Decoding tree is IGNORED for navigation.
NAV = pathlib.Path(r"D:\CRE Decoding System\01 Navigations"
                   r"\Legal Instruments Navigation")
NAV_WORK = NAV / "_working"
# THE ONE TABLE IS SQLITE (login, 2026-08-20 evening: "yes flip it to
# sqlite - as long as it is readable"). Landing = in-place upsert, consumers
# read by index, csv is an EXPORT VIEW (nav_view.py), never the store.
# RENAMED + MOVED TO TREE ROOT 2026-08-21 (login: "call it legal
# instruments db since navigations is just the first phase of multiple ways
# we intend to land into it") - columns reordered to phase accretion:
# id|rd_url|pdf_url (01 nav) · recorded_details|pdf (02 acq) ·
# keyed_by|key (03 org). The old file in 01 Navigations is a frozen backup.
NAV_DB = pathlib.Path(r"D:\CRE Decoding System\Legal Instruments.db")
# legacy csv machinery (nav_build/verify/sort generation) writes under
# _working - still useful as a landing source, never the table of record.
NAV_TABLE = NAV_WORK / "legal_instrument_navigation.csv"

# ⚠ DEPRECATED - points at the OLD tree (zero code references as of
# 2026-08-21; a probe that trusted it read "file missing" for a file that
# exists). The store is DOC_STORE + doc_store_dir() below. Kept only so
# any unimported legacy script fails loudly here, at a named constant.
ACQ = (ROOT / "02 Acquisitions" / "Legal Instruments Acquisition"
       / "Legal Instruments Acquisition Outputs")
STORE = ACQ / "Documents"
BYPARCEL = ACQ / "Acquisition by parcel"

LEDGER = STATE / "ledger.sqlite"
STOP = STATE / "_STOP"

# THE ACQUISITION STORE (system tree). Files sleep under By Document; the
# TABLE is the organizer (login: "the table is how we filter... this table
# is essentially the guide"). The path is a pure function of the doc id.
DOC_STORE = pathlib.Path(r"D:\CRE Decoding System\02 Acquisitions"
                         r"\Legal Instruments Acquisition")
_MON = ("Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


def doc_store_dir(did, recorded=""):
    """By Document folder: year -> '04 Apr' -> day, from the RECORDED date
    (login, 2026-08-20: recorded is the axis that aligns RC and ACRIS - a
    digital id's embedded date is the SUBMISSION date and can lag recording
    by days, and RC ids carry no date at all). Callers pass the rd row's
    recorded string ('1/7/2026 3:49:03 PM'); both pdf lanes run BEHIND the
    rd pass so it is always available. Months are '04 Apr' so Explorer's
    alphabetical sort IS calendar order. Fallbacks: the id's own date
    (digital), else the plain 4+4 id split."""
    m = _re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})", recorded or "")
    if m:
        mm, dd, yy = int(m.group(1)), int(m.group(2)), m.group(3)
        if 1 <= mm <= 12 and 1 <= dd <= 31:
            return (DOC_STORE / "By Document" / yy
                    / f"{mm:02d} {_MON[mm-1]}" / f"{dd:02d}")
    if len(did) >= 8 and did[:8].isdigit():
        mm, dd = int(did[4:6]), int(did[6:8])
        if 1 <= mm <= 12 and 1 <= dd <= 31:
            return (DOC_STORE / "By Document" / did[:4]
                    / f"{mm:02d} {_MON[mm-1]}" / f"{dd:02d}")
    return DOC_STORE / "By Document" / did[:4] / did[4:8]


# ── READING A DOCUMENT: the ONE rule, for extraction and for humans ──────
# ⚠⚠ WRITING AND READING ARE NOT THE SAME OPERATION AND MUST NOT SHARE A
# FUNCTION. `doc_store_dir()` above DECIDES where a file goes, from the
# recorded date, WITH FALLBACKS (id date, then a plain 4+4 split). Which
# branch it took is not recoverable later: normalise the recorded string,
# or fix a bad date, and the same id re-derives a DIFFERENT folder. So a
# reader that recomputes finds nothing and reports "missing" for a file
# that is on disk. THE TRUTH OF WHERE A FILE IS, IS `navigation.pdf` -
# written at the moment it landed. Read it; never re-derive it.
#
# ⚠ AND USE THIS, NOT A HAND-JOIN. corpus_paths defines TWO plausible
# roots and BOTH EXIST ON DISK: DOC_STORE (the files) and the deprecated
# STORE (resolves, never contains them). A hand-rolled `STORE / pdf`
# returns a valid-looking path and fails as "file not found", which reads
# like missing data rather than a wrong root. login hit exactly this by
# hand on 2026-08-29.
STATE_VALUES = frozenset({"", "pending", "absent", "imageless"})


def doc_path(pdf_value):
    """Resolve a `navigation.pdf` cell to an absolute path.

    Returns a pathlib.Path, or None when the cell holds a STATE rather
    than a filename ('' not yet checked - 'pending' scan not up yet -
    'absent'/'imageless' determined to have no image). Returning None for
    a state is deliberate: a state must never be string-joined onto the
    root, because DOC_STORE / '' silently yields the store ROOT, which
    exists - so the caller would 'find' a directory and carry on.

        >>> doc_path("By Document/1917/03 Mar/28/RC_988537.pdf")
        WindowsPath('D:/.../Legal Instruments Acquisition/By Document/...')
        >>> doc_path("pending") is None
        True

    Existence is NOT checked here - that is the caller's decision, and a
    recorded path with no file behind it is a store/db disagreement worth
    reporting, not a lookup failure to swallow.
    """
    if pdf_value is None or pdf_value in STATE_VALUES:
        return None
    return DOC_STORE / pdf_value


def pid_file(tag):
    return STATE / f"_{tag}.pid"


def log(name):
    return LOGS / f"{name}.log"


def ensure():
    """⚠ Called by every entry point. A path that only exists when some other script
    happened to run first is a path that fails at 3am."""
    for d in (RUN, STATE, LOGS, WORKLISTS, AUDITS, SPEC, NAV, ACQ, STORE, BYPARCEL):
        d.mkdir(parents=True, exist_ok=True)
    return ROOT


def drive_present():
    """Is the corpus drive actually there? Checked against the SPEC DB itself, not
    the drive letter — a mounted drive with the corpus missing is just as absent."""
    return SPEC_DB.exists()


def connect_spec(timeout=600, attempts=(2, 10, 30, 60, 120)):
    """Open the spec DB, surviving the transient open failure the One Touch throws
    under heavy concurrent I/O.

    ⚠ MEASURED 2026-08-19 04:01: sqlite3.connect raised 'unable to open database
    file' while rc_detail_pull was writing to the same drive — and the identical
    call had succeeded at 23:34 under the same pull. That error is the Windows
    file-OPEN failing (sharing violation / device momentarily busy), which the
    `timeout` parameter does NOT cover: timeout only paces lock waits AFTER a
    successful open ('database is locked' is the contention error, a different
    animal). So the open itself gets the retry, with backoff.

    Raises sqlite3.OperationalError only after every attempt fails — callers that
    can defer their write should catch it and defer, never die."""
    import sqlite3
    import time as _t
    last = None
    for i, wait in enumerate((0,) + tuple(attempts)):
        if wait:
            _t.sleep(wait)
        try:
            con = sqlite3.connect(SPEC_DB, timeout=timeout)
            con.execute("PRAGMA busy_timeout=%d" % int(timeout * 1000))
            return con
        except sqlite3.OperationalError as e:
            last = e
            print(f"  ⚠ spec DB open failed (attempt {i+1}): {e} — "
                  f"{'retrying' if i < len(attempts) else 'giving up'}")
    raise last
