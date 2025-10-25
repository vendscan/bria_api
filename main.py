import os
import io
import zipfile
from typing import List
from fastapi import FastAPI, UploadFile, File, HTTPException, Header
from fastapi.responses import Response, JSONResponse
from transformers import pipeline
from PIL import Image

app = FastAPI(title="Bria RMBG Service")

# Load model once
pipe = pipeline(
    "image-segmentation",
    model="briaai/RMBG-1.4",
    trust_remote_code=True
)

FINAL_DEFAULT = 1024  # output size (1024x1024)

def autocrop_center_resize(img: Image.Image, final_size: int) -> Image.Image:
    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)
    img.thumbnail((final_size, final_size), Image.LANCZOS)
    canvas = Image.new("RGBA", (final_size, final_size), (0, 0, 0, 0))
    x = (final_size - img.width) // 2
    y = (final_size - img.height) // 2
    canvas.paste(img, (x, y), img)
    return canvas

def read_image(file_bytes: bytes) -> Image.Image:
    try:
        return Image.open(io.BytesIO(file_bytes)).convert("RGB")
    except:
        raise HTTPException(status_code=400, detail="Invalid image file")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/remove-bg")
async def remove_bg(
    file: UploadFile = File(...),
    size: int = FINAL_DEFAULT,
    api_key: str = Header(None)
):
    if api_key != os.getenv("ALLOW_API_KEY"):
        raise HTTPException(status_code=401, detail="Invalid or missing API Key")

    data = await file.read()
    img = read_image(data)
    cut = pipe(img)
    final = autocrop_center_resize(cut, size)

    buf = io.BytesIO()
    final.save(buf, format="PNG")
    buf.seek(0)

    filename_noext = os.path.splitext(file.filename or "output")[0]
    headers = {"Content-Disposition": f'attachment; filename="{filename_noext}.png"'}
    return Response(buf.getvalue(), media_type="image/png", headers=headers)

@app.post("/remove-bg/batch")
async def remove_bg_batch(
    files: List[UploadFile] = File(...),
    size: int = FINAL_DEFAULT,
    api_key: str = Header(None)
):
    if api_key != os.getenv("ALLOW_API_KEY"):
        raise HTTPException(status_code=401, detail="Invalid or missing API Key")

    if not files:
        return JSONResponse({"detail": "No files provided"}, status_code=400)

    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in files:
            data = await f.read()
            img = read_image(data)
            cut = pipe(img)
            final = autocrop_center_resize(cut, size)

            out_buf = io.BytesIO()
            final.save(out_buf, format="PNG")
            out_buf.seek(0)

            filename_noext = os.path.splitext(f.filename or "output")[0]
            zf.writestr(f"{filename_noext}.png", out_buf.getvalue())

    zip_buf.seek(0)
    headers = {"Content-Disposition": 'attachment; filename="processed_images.zip"'}
    return Response(zip_buf.getvalue(), media_type="application/zip", headers=headers)
