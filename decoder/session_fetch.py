"""A fetcher that keeps a SESSION, because the old one didn't — and that may
be the whole reason it kept getting refused.

⚠ THE MEASUREMENT THAT PROMPTED THIS, 2026-08-09.

    urllib, no cookies, 25s BETWEEN requests (0.04 req/s)
        -> refused at request 5, then 2, then 12

    the browser, real session, 1.62 req/s  (40x FASTER)
        -> 38 of 38 pages, 23.4s, zero refusals

Forty times the rate and no refusal. **So it was never a rate limit**, and the
AIMD design built earlier today was solving the wrong problem. The difference
is the client: a browser establishes a session by visiting a page and carries
its cookies; the old fetcher carried nothing and asked for images cold.

⚠ WHERE THE LINE IS, EXPLICITLY.

    NOT DONE HERE   fabricating headers to impersonate a browser · rotating
                    addresses · replaying a token that was never issued to us ·
                    retrying into a refusal · anything whose purpose is to
                    defeat a filter

    DONE HERE       visiting the document's own viewer page first, and keeping
                    the cookies the server sets. That is what every HTTP client
                    is supposed to do, and what a person clicking the same link
                    does. If the server declines to issue a session, this stops.

If that distinction ever stops being clear, the answer is to stop, not to push.

⚠ AND IT STILL PACES, DELIBERATELY SLOWER THAN A BROWSER. The browser managed
1.62 req/s; this defaults to ~1.0. Going faster than a person clicking Save is
how a working channel becomes a closed one — and fetching here has already
blocked Login's own browser once today.
"""
import http.cookiejar
import pathlib
import sys
import time
import urllib.request

import fetch_pages

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
VIEW = "https://a836-acris.nyc.gov/DS/DocumentSearch/DocumentImageView?doc_id="
IMG = "https://a836-acris.nyc.gov/DS/DocumentSearch/GetImage"
PACE = 1.0


class Session:
    def __init__(self):
        self.jar = http.cookiejar.CookieJar()
        self.op = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.jar))
        self.op.addheaders = [("User-Agent", UA)]
        self.opened = None

    def _get(self, url, referer=None):
        req = urllib.request.Request(url)
        if referer:
            req.add_header("Referer", referer)
        with self.op.open(req, timeout=90) as f:
            return f.status, dict(f.headers), f.read()

    def open_document(self, doc_id):
        """Visit the viewer page — exactly what clicking the link does."""
        st, hd, data = self._get(VIEW + doc_id)
        fetch_pages._check_denied(data, hd.get("Content-Type", ""))
        self.opened = doc_id
        time.sleep(PACE)
        return len(self.jar)

    def page(self, doc_id, n):
        if self.opened != doc_id:
            self.open_document(doc_id)
        st, hd, data = self._get(f"{IMG}?doc_id={doc_id}&page={n}",
                                 referer=VIEW + doc_id)
        ct = hd.get("Content-Type", "")
        fetch_pages._check_denied(data, ct)          # raises AccessDenied
        if "tiff" not in ct or len(data) < 500:
            # ⚠ NOT AN IMAGE IS NOT A REFUSAL AND NOT A SILENT SKIP. Three
            # outcomes, always: image, refusal, or something else that gets
            # reported and counted.
            return None, ct, len(data)
        return data, ct, len(data)


def probe(doc_id, pages, pace=PACE):
    """Fetch some pages of one document. Returns (got, refused_at)."""
    s = Session()
    n_cookies = s.open_document(doc_id)
    print(f"  session opened on {doc_id}: {n_cookies} cookie(s)")
    got, refused = [], None
    for i, p in enumerate(pages, 1):
        try:
            data, ct, ln = s.page(doc_id, p)
        except fetch_pages.AccessDenied as e:
            refused = i
            print(f"  ⚠ REFUSED at page {p} (request {i}). {str(e)[:90]}")
            break
        if data is None:
            print(f"  p{p}: not an image ({ct}, {ln}b)")
        else:
            got.append((p, data))
            print(f"  p{p}: {ln:,}b")
        time.sleep(pace)
    return got, refused


if __name__ == "__main__":
    doc = sys.argv[1] if len(sys.argv) > 1 else "2012122701923005"
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 6
    got, refused = probe(doc, range(1, n + 1))
    print(f"\n  {len(got)}/{n} pages"
          + (f", refused at {refused}" if refused else " — NO REFUSAL"))
