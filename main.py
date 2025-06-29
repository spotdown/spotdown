from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from downloader import download_spotify_track
import os

app = FastAPI()

@app.get("/download")  # ✅ must be GET
def download(url: str = Query(...)):
    if not url:
        raise HTTPException(status_code=400, detail="Missing 'url' parameter.")

    mp3_path = download_spotify_track(url)

    if not os.path.exists(mp3_path):
        raise HTTPException(status_code=500, detail="MP3 file not found.")

    return FileResponse(mp3_path, filename=os.path.basename(mp3_path), media_type="audio/mpeg")
