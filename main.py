import os
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse
import yt_dlp
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

app = FastAPI()

SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")

if not SPOTIPY_CLIENT_ID or not SPOTIPY_CLIENT_SECRET:
    raise RuntimeError("Missing SPOTIPY_CLIENT_ID or SPOTIPY_CLIENT_SECRET")

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=SPOTIPY_CLIENT_ID,
    client_secret=SPOTIPY_CLIENT_SECRET
))

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

@app.get("/")
def home():
    return {"message": "Spotify Downloader API"}

@app.get("/download")
def download(url: str = Query(...)):
    if "track" not in url:
        raise HTTPException(status_code=400, detail="Only Spotify track URLs are supported")

    try:
        track = sp.track(url)
        title = track['name']
        artist = track['artists'][0]['name']
        search_query = f"{title} {artist} audio"
        safe_name = f"{title}-{artist}".replace(" ", "_").replace("/", "_")
        output_path = os.path.join(DOWNLOAD_DIR, f"{safe_name}.mp3")

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_path,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
            'noplaylist': True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([f"ytsearch1:{search_query}"])

        if not os.path.exists(output_path):
            raise HTTPException(status_code=500, detail="Download failed")

        return FileResponse(output_path, filename=os.path.basename(output_path), media_type="audio/mpeg")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
