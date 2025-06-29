from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import subprocess
import uuid
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from yt_dlp import YoutubeDL
import time

app = Flask(__name__)
CORS(app)

# Set your Spotify API credentials
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", "your_spotify_client_id")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "your_spotify_client_secret")

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET
))

@app.route("/")
def home():
    return "Spotify Downloader API is running!"

@app.route("/download", methods=["POST"])
def download():
    data = request.get_json()
    spotify_url = data.get("spotify_url")

    if not spotify_url:
        return jsonify({"error": "No Spotify URL provided"}), 400

    try:
        track_info = sp.track(spotify_url)
        song_name = track_info["name"]
        artist_name = track_info["artists"][0]["name"]
        search_query = f"{song_name} {artist_name}"

        unique_id = str(uuid.uuid4())
        output_filename = f"{song_name} - {artist_name}.mp3"
        temp_filename = f"{unique_id}.webm"
        cookies_path = "cookies.txt"

        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": temp_filename,
            "noplaylist": True,
            "quiet": True,
            "cookiefile": cookies_path,
        }

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{search_query}", download=True)
            if "entries" in info:
                info = info["entries"][0]

        mp3_file = f"{song_name} - {artist_name}.mp3"
        subprocess.run([
            "ffmpeg", "-i", temp_filename, "-vn",
            "-ab", "192k", "-ar", "44100", "-y", mp3_file
        ], check=True)

        os.remove(temp_filename)

        return send_file(mp3_file, as_attachment=True)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)