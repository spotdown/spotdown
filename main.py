import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import requests

app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# Spotify API auth
client_id = os.getenv("SPOTIPY_CLIENT_ID")
client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")
if not client_id or not client_secret:
    raise RuntimeError("Missing Spotify credentials.")

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=client_id,
    client_secret=client_secret
))

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

@app.get("/")
def root():
    return {"message": "Public Spotify → MP3 Downloader (Deezer-based)"}

@app.get("/download")
def download(url: str = Query(...)):
    if "track" not in url:
        raise HTTPException(status_code=400, detail="Only Spotify track URLs supported")

    try:
        track = sp.track(url)
        title = track["name"]
        artist = track["artists"][0]["name"]
        search_query = f"{title} {artist}"

        deezer_api = f"https://api.deezer.com/search?q={requests.utils.quote(search_query)}"
        response = requests.get(deezer_api).json()

        if not response["data"]:
            raise HTTPException(status_code=404, detail="Track not found on Deezer")

        track_info = response["data"][0]
        preview_url = track_info["preview"]
        if not preview_url:
            raise HTTPException(status_code=404, detail="No audio available")

        safe_name = f"{title}-{artist}".replace(" ", "_").replace("/", "_") + ".mp3"
        mp3_path = os.path.join(DOWNLOAD_DIR, safe_name)

        with open(mp3_path, "wb") as f:
            f.write(requests.get(preview_url).content)

        return FileResponse(mp3_path, filename=safe_name, media_type="audio/mpeg")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
