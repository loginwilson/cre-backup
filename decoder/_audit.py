import pathlib, random, io, sys, json, hashlib
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import fitz
from PIL import Image
Image.MAX_IMAGE_PIXELS=None
store=pathlib.Path("D:/acris/02-acquisition/documents")
pdfs=list(store.rglob("*.pdf"))
random.seed(11)
s=random.sample(pdfs,min(200,len(pdfs)))
ok=bad=pages=g4=0; errs={}
for p in s:
    try:
        d=fitz.open(str(p)); n=d.page_count
        if n<1: raise ValueError("zero pages")
        for pno in (0,n//2,n-1):
            xr=d[pno].get_images(full=True)
            if not xr: raise ValueError(f"p{pno+1} no image")
            im=d.extract_image(xr[0][0])
            if not im.get("image"): raise ValueError("empty stream")
            i=Image.open(io.BytesIO(im["image"]))
            if i.mode in ("1","L"): g4+=1
        pages+=n; ok+=1; d.close()
    except Exception as e:
        bad+=1; errs[str(e)[:70]]=errs.get(str(e)[:70],0)+1
r={"sampled":len(s),"valid":ok,"bad":bad,"pages":pages,"bitonal_checks":g4,"errors":errs,
   "store_total":len(pdfs)}
pathlib.Path("D:/acris/_audit.json").write_text(json.dumps(r,indent=1),encoding="utf-8")
print(json.dumps(r,indent=1))
