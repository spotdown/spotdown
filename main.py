from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, PlainTextResponse
from downloader import download_spotify_track
import os

app = FastAPI()

@app.get("/download")
@app.head("/download")  # ✅ handles HEAD requests from WordPress
@app.options("/download")  # optional for preflight requests
def download(request: Request, url: str = Query(default=None)):
    if not url:
        return PlainTextResponse("Missing URL", status_code=400)

    if request.method == "HEAD":
        return PlainTextResponse("OK", status_code=200)

    mp3_path = download_spotify_track(url)
    return FileResponse(mp3_path, filename=os.path.basename(mp3_path), media_type='audio/mpeg')
