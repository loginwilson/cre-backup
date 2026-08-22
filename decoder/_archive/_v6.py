import os, sys, time, pathlib
os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"]="True"
os.environ["OMP_NUM_THREADS"]=str(os.cpu_count())
sys.stdout.reconfigure(encoding="utf-8",errors="replace")
import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS=None
from paddleocr import PaddleOCR
t=time.time()
ocr=PaddleOCR(text_detection_model_name="PP-OCRv6_medium_det",
              text_recognition_model_name="PP-OCRv6_medium_rec",
              use_doc_orientation_classify=False,
              use_doc_unwarping=False,
              use_textline_orientation=False,
              enable_mkldnn=False,
              device="cpu")
print(f"  init {time.time()-t:.1f}s", flush=True)
arrs=[]
for i in (2,3,4):
    g=Image.open(f"devr_pages/2003010601086002/p{i:03d}.tif").convert("L")
    w,h=g.size; s=1600/max(w,h)
    arrs.append(np.array(g.resize((int(w*s),int(h*s)),Image.LANCZOS).convert("RGB")))
ocr.predict(arrs[0])
t=time.time(); ch=0
for a in arrs:
    r=ocr.predict(a)
    for page in r:
        ch+=len(" ".join(page.get("rec_texts", [])))
el=time.time()-t
print(f"  PP-OCRv6 medium: {el:.2f}s / 3 pages = {el/3:.2f}s per page   {ch} chars")
