from fastapi import FastAPI, UploadFile, File, HTTPException, Header
...

@app.post("/remove-bg")
async def remove_bg(
    file: UploadFile = File(...),
    size: int = FINAL_DEFAULT,
    api_key: str = Header(None)
):
    # ✅ Require API Key
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
