"""WHERE IS THIS DOCUMENT? - resolve a doc id to a real file on disk.

    python document_locate.py 2002122000001001
    python document_locate.py RC_988537 --open
    python document_locate.py 2002122000001001 2002122000002001   (many)

login 2026-08-29: "how do I search it up? ... it should be easy for both
human and code to find."

⚠ WHY THIS EXISTS. `navigation.pdf` stores a RELATIVE path
(`By Document\\2003\\01 Jan\\06\\<id>.pdf`) and that is deliberate: the
store lives on a USB drive that has already come back as a different
letter, so an absolute path would put ~4.5M rows wrong on a remount while
a relative one needs ONE constant changed. The cost of that choice is
that the stored value alone does not tell a human where the file is -
which is what this closes.

⚠ THE ROOT IS `CP.DOC_STORE`, NEVER `CP.STORE`. corpus_paths defines both
and BOTH EXIST ON DISK:

    DOC_STORE  D:\\CRE Decoding System\\02 Acquisitions\\Legal Instruments
               Acquisition                                    <- the files
    STORE      D:\\Ignore\\...\\Acquisition Outputs\\Documents  <- resolves,
               but never contains them

`STORE` is the more obvious-sounding name and `Test-Path` says True, so
reaching for it fails as "file not found" - which reads like missing data
rather than a wrong root. That is a decoy, and it is why this module
hardcodes the join instead of letting each caller guess.

⚠ AND WINDOWS SEARCH WILL NOT FIND THESE. External volumes are excluded
from the search index by default, so Explorer's search box returns
nothing for a file that is sitting right there. Do not read a failed
Explorer search as a missing document - ask this tool.
"""
import argparse
import os
import pathlib
import sqlite3
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import corpus_paths as CP                                      # noqa: E402

# THE JOIN RULE, in one place: full path = DOC_STORE / navigation.pdf
ROOT = pathlib.Path(CP.DOC_STORE)

# the non-path values `pdf` can legitimately hold - each is a STATE, not a
# defect, and each means a different thing to a caller (see the reproduction
# MDs: pending/absent/imageless are DETERMINATIONS and count as landed;
# '' is the only unlanded state and NULL must never appear).
STATES = {
    "": "NOT YET CHECKED - the honest todo; the documentation floor has"
        " not reached this row",
    "pending": "CHECKED - the source says the scan is not up yet; re-asked"
               " until it resolves",
    "absent": "CHECKED - determined to have no image (richmond)",
    "imageless": "CHECKED - aged, no image; this is the verdict (acris)",
}

ap = argparse.ArgumentParser(
    description="resolve document id(s) to a full path on disk")
ap.add_argument("ids", nargs="+", help="document id(s), e.g. 2002122000001001"
                                       " or RC_988537")
ap.add_argument("--open", action="store_true",
                help="open the file with the default application")
ap.add_argument("--reveal", action="store_true",
                help="open Explorer at the file, with it selected - the"
                     " human bridge when you want the FOLDER, not the file")
a = ap.parse_args()

c = sqlite3.connect("file:%s?mode=ro" % CP.NAV_DB, uri=True)
# ⚠ the register lane writes constantly; a reader must wait rather than
# raise "database is locked" and look like the document is missing.
c.execute("PRAGMA busy_timeout=30000")

rc = 0
for did in a.ids:
    row = c.execute("SELECT pdf FROM navigation WHERE id=?", (did,)).fetchone()
    if row is None:
        print("%s\n  NOT IN THE DB - this id has never been minted."
              " Check the id, or the source's sync." % did)
        rc = 1
        continue
    val = row[0]
    if val is None:
        # documented as impossible; report it loudly rather than crash
        print("%s\n  ⚠ pdf IS NULL - this should never happen (NULL is not"
              " one of the four states). Worth investigating." % did)
        rc = 1
        continue
    if val in STATES:
        print("%s\n  no file yet - pdf=%r\n  %s"
              % (did, val, STATES[val]))
        continue
    full = ROOT / val
    exists = full.exists()
    size = ("%.1f KB" % (full.stat().st_size / 1024)) if exists else "-"
    print("%s\n  %s\n  %s   %s"
          % (did, full, "EXISTS" if exists else "⚠ RECORDED BUT MISSING",
             size))
    if not exists:
        # a path in the db with no file behind it is an integrity problem,
        # not a lookup failure - say which one it is.
        print("  ⚠ the db claims this path; the file is not there. That is"
              " a store/db disagreement, not a bad search.")
        rc = 1
    elif a.reveal:
        # ⚠ /select, TAKES NO SPACE AFTER THE COMMA and the path must be
        # one argument - explorer silently opens Documents instead if you
        # get either wrong, which looks like the file was not found.
        subprocess.run(["explorer", "/select,%s" % full])
    elif a.open:
        os.startfile(str(full))          # noqa: S606 - user-invoked, Windows

sys.exit(rc)
