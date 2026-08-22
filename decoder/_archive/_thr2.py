import os, sys, time, types, pathlib
import numpy as np
_O=None
def _init(threads):
    global _O
    import openvino
    shim=types.ModuleType("openvino.runtime")
    for n in dir(openvino): setattr(shim,n,getattr(openvino,n))
    sys.modules["openvino.runtime"]=shim
    import rapidocr_openvino.utils.infer_engine as IE
    from openvino import Core
    def patched(self, config):
        core=Core(); self._verify_model(config["model_path"])
        m=core.read_model(config["model_path"])
        core.set_property("CPU", {"INFERENCE_NUM_THREADS": str(threads)})
        self.session=core.compile_model(model=m, device_name="CPU").create_infer_request()
    IE.OpenVINOInferSession.__init__=patched
    from rapidocr_openvino import RapidOCR
    _O=RapidOCR()

def work(path):
    from PIL import Image
    Image.MAX_IMAGE_PIXELS=None
    g=Image.open(path).convert("L"); w,h=g.size; s=1600/max(w,h)
    a=np.array(g.resize((int(w*s),int(h*s)),Image.LANCZOS).convert("RGB"))
    r,_=_O(a)
    return len(" ".join(x[1] for x in (r or [])))

if __name__=="__main__":
    from multiprocessing import Pool
    pages=[str(p) for p in sorted(pathlib.Path("devr_pages/2003010601086002").glob("*.tif"))][:12]
    for nproc, thr in ((1,8),(2,4),(4,2),(8,1)):
        t=time.time()
        with Pool(nproc, initializer=_init, initargs=(thr,)) as pool:
            ch=sum(pool.map(work, pages))
        el=time.time()-t
        print(f"  {nproc} proc x {thr} thr : {el:6.1f}s / {len(pages)} pg = "
              f"{el/len(pages):5.2f}s per page   {ch} chars", flush=True)
