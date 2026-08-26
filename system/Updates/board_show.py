"""READ-ONLY board viewer. Nothing here writes; safe while the lanes run.

    python board_show.py            print the board once
    python board_show.py --watch    reprint every 30s until Ctrl+C

The board itself is computed by routine_update.py (the 60s/5m windows) and
board_truth.py (the counted-from-the-column truth). This only DISPLAYS
Updates.db, so a stale row here means a stopped writer, never a stale view.
"""
import sqlite3, sys, time, pathlib

DB = pathlib.Path(__file__).parent / "Updates.db"


def show():
    c = sqlite3.connect("file:%s?mode=ro" % DB, uri=True, timeout=30)
    cols = [r[1] for r in c.execute("PRAGMA table_info(update_board)")]
    rows = [dict(zip(cols, r)) for r in c.execute("SELECT * FROM update_board")]
    c.close()
    if rows:
        print(str(rows[0]["as_of"]).replace("\ufffd", "\u00b7"))
    print("%-10s %-8s %13s %13s %8s %9s %9s %11s"
          % ("SOURCE", "STATUS", "LANDED", "NEEDED", "PCT",
             "NOW/s", "5MIN/s", "ETA"))
    for d in rows:
        print("%-10s %-8s %13s %13s %7.2f%% %9s %9s %11s"
              % (d["source"], d["status"], f"{d['landed']:,}",
                 f"{d['needed']:,}", d["pct_of_total"], d["rate_now"],
                 d["rate"], d["eta"]))


if __name__ == "__main__":
    if "--watch" in sys.argv:
        while True:
            print("\033[2J\033[H", end="")
            show()
            print("\n(refreshing every 30s - Ctrl+C to stop)")
            time.sleep(30)
    else:
        show()
