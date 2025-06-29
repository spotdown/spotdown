# downloader.py
import yt_dlp
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET
))

def download_spotify_track(url: str) -> str:
    track_info = sp.track(url)
    title = track_info["name"]
    artist = track_info["artists"][0]["name"]
    query = f"{title} {artist} audio"

    outtmpl = f"downloads/{title}-{artist}.mp3"

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': outtmpl,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([f"ytsearch1:{query}"])

    return outtmpl
