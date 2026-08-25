"""WHERE IS RICHMOND AGAINST login's SPEC? — one bounded pass, written to file.

login 2026-08-25 stated the pipeline: doc id mapped -> rd_url minted ->
pdf_url minted -> rd acquired -> key by parcel/BBL fills automatically ->
pdf acquired (a real path, or 'no pdf' when none exists, or held 'pending'
while inside the scan-lag distribution). Sync keeps it current by date range
and hands new ids to the BACKFILL rather than jumping the queue.

This measures each of those stages. ⚠ It writes its answer to rc_state.txt
because a long run piped through a terminal has been lost twice today.

⚠ BOUND THE ID RANGE. `id LIKE 'RC_%'` scans 21M acris rows before reaching
richmond - it cost two timeouts today. `id > 'RC' AND id < 'RD'` seeks
straight into the richmond block on the primary key.
"""
import sqlite3, sys, time, io
sys.path.insert(0, ".")
import corpus_paths as CP

out = io.open("rc_state.txt", "w", encoding="utf-8")
def say(m=""):
    print(m, flush=True); out.write(m + "\n"); out.flush()

con = sqlite3.connect("file:%s?mode=ro" % CP.NAV_DB, uri=True, timeout=900)
con.execute("PRAGMA busy_timeout=900000")
B = "id > 'RC' AND id < 'RD'"
t = time.time()
r = con.execute("""
 SELECT COUNT(*),
   SUM(CASE WHEN COALESCE(rd_url,'')  != '' THEN 1 ELSE 0 END),
   SUM(CASE WHEN COALESCE(pdf_url,'') != '' THEN 1 ELSE 0 END),
   SUM(CASE WHEN COALESCE(recorded_details,'') != '' THEN 1 ELSE 0 END),
   SUM(CASE WHEN COALESCE(key,'') != '' THEN 1 ELSE 0 END),
   SUM(CASE WHEN COALESCE(pdf,'') != '' THEN 1 ELSE 0 END),
   SUM(CASE WHEN COALESCE(pdf,'') = '' AND recorded_details LIKE '%"image_state":"present"%' THEN 1 ELSE 0 END),
   SUM(CASE WHEN COALESCE(pdf,'') = '' AND recorded_details LIKE '%"image_state":"pending"%' THEN 1 ELSE 0 END),
   SUM(CASE WHEN COALESCE(pdf,'') = '' AND recorded_details LIKE '%"image_state":"absent"%'  THEN 1 ELSE 0 END)
 FROM navigation WHERE %s""" % B).fetchone()
tot, rdu, pdu, rd, key, pdf, pres, pend, absent = [x or 0 for x in r]
say("RICHMOND vs THE SPEC     (one pass, %.0fs)" % (time.time() - t))
say("  %-34s %12s" % ("doc ids mapped", "{:,}".format(tot)))
def line(lbl, n):
    say("  %-34s %12s  %6.2f%%" % (lbl, "{:,}".format(n), 100.0*n/tot if tot else 0))
line("rd_url minted", rdu)
line("pdf_url minted", pdu)
line("rd acquired", rd)
line("key (parcel/BBL) filled", key)
line("pdf path acquired", pdf)
say()
say("  OF THE ROWS WITH NO PDF YET:")
line("  image PRESENT - fetchable now", pres)
line("  image PENDING - scan lag, hold", pend)
line("  image ABSENT  - NO PDF EXISTS", absent)
say()
say("  ⚠ 100%% IS UNREACHABLE UNTIL 'no pdf' IS A RECORDED VERDICT.")
say("     today  landed/total            = %6.2f%%" % (100.0*pdf/tot if tot else 0))
say("     with an absent verdict written = %6.2f%%" % (100.0*(pdf+absent)/tot if tot else 0))
say("     still to actually FETCH        = %s docs" % "{:,}".format(pres))
con.close(); out.close()
