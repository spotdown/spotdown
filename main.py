from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import requests
import yt_dlp
import os
import subprocess
import uuid
import base64

app = Flask(__name__)
CORS(app)

SPOTIFY_CLIENT_ID = "ad0720ec13024b85b3843b39cf06ee16"
SPOTIFY_CLIENT_SECRET = "f1469bb0f25d40959b903dd5618ea179"

def get_spotify_token():
    auth_url = "https://accounts.spotify.com/api/token"
    auth_header = base64.b64encode(f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth_header}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}
    response = requests.post(auth_url, headers=headers, data=data)
    return response.json().get("access_token")

def get_song_details(spotify_url):
    token = get_spotify_token()
    headers = {"Authorization": f"Bearer {token}"}
    track_id = spotify_url.split("/")[-1].split("?")[0]
    api_url = f"https://api.spotify.com/v1/tracks/{track_id}"
    response = requests.get(api_url, headers=headers)

    if response.status_code != 200:
        return None, None

    data = response.json()
    song_name = data["name"]
    artist_name = data["artists"][0]["name"]
    return song_name, artist_name

def search_youtube(query):
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "format": "bestaudio/best",
        "noplaylist": True,
        "default_search": "ytsearch1",
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            result = ydl.extract_info(query, download=False)
            if "entries" in result:
                video = result["entries"][0]
            else:
                video = result
            return f"https://www.youtube.com/watch?v={video['id']}"
        except Exception as e:
            print(f"Error searching YouTube: {e}")
            return None

@app.route("/")
def home():
    return "Spotify to MP3 Downloader API"

@app.route("/download", methods=["POST"])
def download():
    data = request.get_json()
    spotify_url = data.get("spotify_url")

    if not spotify_url:
        return jsonify({"error": "No Spotify URL provided"}), 400

    song_name, artist_name = get_song_details(spotify_url)
    if not song_name or not artist_name:
        return jsonify({"error": "Failed to get song details"}), 400

    query = f"{song_name} {artist_name} audio"
    youtube_url = search_youtube(query)
    if not youtube_url:
        return jsonify({"error": "Failed to find song on YouTube"}), 400

    temp_id = str(uuid.uuid4())
    webm_file = f"{temp_id}.webm"
    mp3_file = f"{song_name} - {artist_name}.mp3"

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": webm_file,
        "cookiefile": "cookies.txt",
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    try:
        subprocess.run(
            ["ffmpeg", "-i", webm_file, "-vn", "-ab", "192k", "-ar", "44100", "-y", mp3_file],
            check=True
        )
        os.remove(webm_file)
    except Exception as e:
        return jsonify({"error": "ffmpeg conversion failed", "details": str(e)}), 500

    try:
        return send_file(mp3_file, as_attachment=True)
    finally:
        if os.path.exists(mp3_file):
            os.remove(mp3_file)

if __name__ == "__main__":
    app.run(debug=True)
