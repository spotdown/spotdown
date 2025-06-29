# downloader.py

import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import yt_dlp

# Spotify authentication (uses environment variables)
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials())

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def download_spotify_track(url: str) -> str:
    if "track" not in url:
        raise ValueError("Only Spotify track URLs are supported.")

    # Fetch track metadata
    track = sp.track(url)
    title = track["name"]
    artist = track["artists"][0]["name"]
    search_query = f"{title} {artist} audio"

    # Output path
    safe_name = f"{title}-{artist}".replace(" ", "_").replace("/", "_")
    output_path = os.path.join(DOWNLOAD_DIR, f"{safe_name}.mp3")

    # yt-dlp download options
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

    # Download audio from YouTube
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([f"ytsearch1:{search_query}"])

    if not os.path.exists(output_path):
        raise FileNotFoundError("MP3 download failed.")

    return output_path
