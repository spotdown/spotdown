# main.py
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import FileResponse
from downloader import download_spotify_track
import os

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Spotify Downloader is up."}

@app.get("/download")
def download(url: str = Query(...)):
    try:
        mp3_path = download_spotify_track(url)
        return FileResponse(mp3_path, filename=os.path.basename(mp3_path), media_type='audio/mpeg')
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
