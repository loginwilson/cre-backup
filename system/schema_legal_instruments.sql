-- trigger: key_on_rd
CREATE TRIGGER key_on_rd AFTER UPDATE OF recorded_details ON navigation
WHEN COALESCE(NEW.recorded_details,'') != ''
 AND COALESCE(NEW.keyed_by,'') = ''
BEGIN
  -- ROUTE 1, STRUCTURAL (2026-08-22): the rd carries the BBL for ~99.7%
  -- of the corpus, so the key is arithmetic on data already in the row -
  -- exactly like mint_urls mints a url on insert. Keying here costs no
  -- extra read, cannot contend with any lane (same transaction as the
  -- landing write), and cannot be forgotten. A sweeping keyer was the
  -- alternative and it blocks the walkers.
  UPDATE navigation SET
    keyed_by = CASE WHEN (SELECT COUNT(*) FROM json_each(
                            NEW.recorded_details, '$.parcels')) > 0
                    THEN 'parcel' ELSE 'pdf-pass' END,
    key = COALESCE((SELECT group_concat(json_extract(value,'$.bbl'), ';')
                      FROM json_each(NEW.recorded_details, '$.parcels')), '')
  WHERE id = NEW.id;
END;

-- trigger: key_rules
CREATE TRIGGER key_rules BEFORE UPDATE OF keyed_by, key ON navigation
BEGIN
  SELECT CASE
    WHEN COALESCE(NEW.keyed_by,'') NOT IN ('', 'parcel', 'reference', 'pdf-pass', 'pdf')
      THEN RAISE(ABORT, 'keyed_by must be parcel/reference/pdf-pass/pdf - the three-route ladder (party is DECODING, not a key)')
    WHEN NEW.keyed_by IN ('parcel','reference') AND (COALESCE(NEW.recorded_details,'')='' OR COALESCE(NEW.key,'')='')
      THEN RAISE(ABORT, 'parcel/reference keys need the rd landed and a non-empty key')
    WHEN NEW.keyed_by = 'pdf-pass' AND (COALESCE(NEW.recorded_details,'')='' OR COALESCE(NEW.key,'')!='')
      THEN RAISE(ABORT, 'pdf-pass = rd read and unkeyable: rd required, key must stay empty')
    WHEN NEW.keyed_by = 'pdf' AND (COALESCE(NEW.pdf,'')='' OR COALESCE(NEW.key,'')='')
      THEN RAISE(ABORT, 'a pdf key needs the pdf on disk and a non-empty key')
    WHEN COALESCE(NEW.keyed_by,'')='' AND COALESCE(NEW.key,'')!=''
      THEN RAISE(ABORT, 'a key with no route is unattributed evidence')
  END;
END;

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
CREATE INDEX ix_nav_pdf_todo ON navigation(id) WHERE pdf = '';

-- index: ix_nav_rd_todo
CREATE INDEX ix_nav_rd_todo ON navigation(id) WHERE recorded_details = '';