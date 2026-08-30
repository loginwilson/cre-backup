-- trigger: mint_urls
CREATE TRIGGER mint_urls AFTER INSERT ON navigation
WHEN COALESCE(NEW.rd_url,'')='' OR COALESCE(NEW.pdf_url,'')=''
BEGIN
  UPDATE navigation SET
    rd_url = CASE WHEN NEW.id GLOB 'RC_*'
      THEN 'https://www.richmondcountyclerk.com/Search/viewDocumentInfo/' || substr(NEW.id, 4)
      ELSE 'https://a836-acris.nyc.gov/DS/DocumentSearch/DocumentDetail?doc_id=' || NEW.id END,
    pdf_url = CASE WHEN NEW.id GLOB 'RC_*'
      THEN 'https://www.richmondcountyclerk.com/ViewVscmsDocument/ViewContent?p_endorsementId=' || substr(NEW.id, 4)
      ELSE 'https://a836-acris.nyc.gov/DS/DocumentSearch/DocumentImageView?doc_id=' || NEW.id END
  WHERE id = NEW.id;
END;

-- trigger: pdf_state_on_rd
CREATE TRIGGER pdf_state_on_rd AFTER UPDATE OF recorded_details ON navigation
WHEN NEW.id GLOB 'RC_*'
 AND COALESCE(NEW.recorded_details,'') != ''
 AND COALESCE(NEW.pdf,'') = ''
 AND COALESCE(json_extract(NEW.recorded_details,'$.image_state'),'')
       NOT IN ('', 'present')
BEGIN
  -- THE PDF CELL IS ASSIGNED THE MOMENT THE rd SAYS THERE IS NO IMAGE
  -- (login 2026-08-26: "we need to make sure the pdf pending absent ''
  -- rules are in the sync system"). Same shape as key_on_rd: the verdict
  -- is arithmetic on data already in the row, written inside the landing
  -- transaction, so it cannot be forgotten and cannot race a batch job.
  --
  -- 'pending' = ASSIGNED but STILL QUEUED. rc_lane's miner selects
  -- pdf IN ('','pending'), so the doc keeps its place and the image is
  -- collected the moment it attaches - login: "it should continuously
  -- fill the que until it reaches day 7".
  --
  -- ⚠ MATURATION IS NOT HERE. pending -> 'absent' at the 7-day boundary
  -- needs date arithmetic on M/D/YYYY and a clock; rc_pdf_state.py owns
  -- it on the nightly pass. This trigger only guarantees a row is never
  -- left UNASSIGNED after its rd lands.
  --
  -- ⚠ image_state 'present' is deliberately NOT touched: pdf stays ''
  -- so the miner still sees it as work. ⚠ image_state MISSING is also
  -- untouched - "we never asked" is not "there is none".
  UPDATE navigation SET pdf = 'pending' WHERE id = NEW.id;
END;

-- table: navigation
CREATE TABLE navigation(
    id TEXT PRIMARY KEY,
    rd_url TEXT,
    pdf_url TEXT,
    recorded_details TEXT,
    pdf TEXT,
    keyed_by TEXT,
    key TEXT);

-- index: ix_nav_key
CREATE INDEX ix_nav_key ON navigation(key);

-- index: ix_nav_pdf_todo
CREATE INDEX ix_nav_pdf_todo ON navigation(id) WHERE pdf IN ('','pending');

-- index: ix_nav_rd_todo
CREATE INDEX ix_nav_rd_todo ON navigation(id) WHERE recorded_details = '';