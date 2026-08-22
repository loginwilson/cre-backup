import pathlib, re, sqlite3, time, datetime, sys
ROOT=pathlib.Path("D:/acris")
out=ROOT/"00-run"/"logs"/"completeness.log"
while True:
    try:
        c=p=docs=0
        for f in (ROOT/"02-acquisition"/"by-parcel").rglob("_INDEX.md"):
            t=f.read_text(encoding="utf-8",errors="replace")
            m=re.search(r"\*\*(\d+) documents\*\*",t)
            if not m: continue
            docs+=int(m.group(1))
            if t.count("| not acquired |")==0: c+=1
            else: p+=1
        led=sqlite3.connect(f"file:{ROOT/'00-run'/'state'/'ledger.sqlite'}?mode=ro",uri=True)
        ok,pg=led.execute("select count(*),coalesce(sum(got),0) from doc where status='ok'").fetchone()
        emp=led.execute("select count(*) from doc where status='empty'").fetchone()[0]
        led.close()
        line=(f"[{datetime.datetime.now():%H:%M}] parcels {c+p} ({c} complete, {p} partial) · "
              f"spec-docs {docs:,} · fetched {ok:,} docs / {pg:,} pages · image-less found {emp}")
        with open(out,"a",encoding="utf-8") as fh: fh.write(line+"\n")
    except Exception as e:
        with open(out,"a",encoding="utf-8") as fh: fh.write(f"[err] {e}\n")
    time.sleep(900)
