import os, sys, time, pathlib, json
import numpy as np
os.environ.setdefault("OMP_NUM_THREADS","2")
from PIL import Image
Image.MAX_IMAGE_PIXELS=None

def cfg(intra, dml, batch=16):
    import rapidocr_onnxruntime as R
    base=(pathlib.Path(R.__file__).parent/"config.yaml").read_text(encoding="utf-8")
    t=base.replace("&intra_nums -1",f"&intra_nums {intra}").replace("&inter_nums -1","&inter_nums 1")
    t=t.replace("rec_batch_num: 6",f"rec_batch_num: {batch}")
    if dml: t=t.replace("use_dml: false","use_dml: true")
    p=pathlib.Path(f"_cfg_{intra}_{int(dml)}.yaml"); p.write_text(t,encoding="utf-8"); return str(p)

_O=None
def work(args):
    global _O
    path, intra, dml = args
    if _O is None:
        from rapidocr_onnxruntime import RapidOCR
        _O=RapidOCR(config_path=cfg(intra,dml))
    g=Image.open(path).convert("L"); w,h=g.size; s=1600/max(w,h)
    a=np.array(g.resize((int(w*s),int(h*s)),Image.LANCZOS).convert("RGB"))
    r,_=_O(a)
    return len(" ".join(x[1] for x in (r or [])))

if __name__=="__main__":
    from multiprocessing import Pool
    pages=[str(p) for p in sorted(pathlib.Path("devr_pages/2003010601086002").glob("*.tif"))][:16]
    for nproc,intra,dml in ((4,2,False),(8,1,False),(6,2,False)):
        t=time.time()
        with Pool(nproc) as pool:
            ch=sum(pool.map(work,[(p,intra,dml) for p in pages]))
        el=time.time()-t
        print(f"  {nproc} procs x intra{intra} {'DML' if dml else 'CPU'}:  "
              f"{el:6.1f}s / {len(pages)} pages = {el/len(pages):5.2f}s per page   {ch} chars", flush=True)
