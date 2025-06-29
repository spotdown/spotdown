from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import yt_dlp
import requests
import os
import subprocess

# ==== Spotify API Credentials ====
SPOTIFY_CLIENT_ID = "ad0720ec13024b85b3843b39cf06ee16"
SPOTIFY_CLIENT_SECRET = "f1469bb0f25d40959b903dd5618ea179"

# ==== Flask Setup ====
app = Flask(__name__)
CORS(app)

# ==== Spotify Access Token ====
def get_spotify_token():
    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": f"Basic {requests.auth._basic_auth_str(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)}",
    }
    data = {"grant_type": "client_credentials"}
    res = requests.post(url, headers=headers, data=data)
    if res.status_code == 200:
        return res.json()["access_token"]
    return None

# ==== Get Track Info ====
def get_track_info(spotify_url):
    token = get_spotify_token()
    if not token:
        return None, None

    track_id = spotify_url.split("/")[-1].split("?")[0]
    url = f"https://api.spotify.com/v1/tracks/{track_id}"
    headers = {"Authorization": f"Bearer {token}"}
    res = requests.get(url, headers=headers)
    
    if res.status_code == 200:
        data = res.json()
        song_name = data["name"]
        artist_name = data["artists"][0]["name"]
        return song_name, artist_name
    return None, None

# ==== YouTube Search ====
def search_youtube(query):
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "format": "bestaudio/best",
        "noplaylist": True,
        "default_search": "ytsearch5",
        "cookiefile": "cookies.txt",  # Must be in same directory
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            result = ydl.extract_info(query, download=False)
            if "entries" in result and len(result["entries"]) > 0:
                video = result["entries"][0]
                return f"https://www.youtube.com/watch?v={video['id']}"
        except Exception as e:
            print("YouTube Search Error:", str(e))
    return None

# ==== MP3 Downloader ====
def download_mp3(youtube_url, song_name, artist_name):
    filename = f"{song_name} - {artist_name}".replace("/", "_")
    webm_file = f"{filename}.webm"
    mp3_file = f"{filename}.mp3"

    # Download audio
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": webm_file,
        "quiet": True,
        "cookiefile": "cookies.txt",  # Must be valid Netscape format
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])
    except Exception as e:
        return None, str(e)

    # Convert to MP3
    try:
        subprocess.run([
            "ffmpeg", "-i", webm_file,
            "-vn", "-ab", "192k", "-ar", "44100", "-y", mp3_file
        ], check=True)
        os.remove(webm_file)
        return mp3_file, None
    except subprocess.CalledProcessError as e:
        return None, "FFmpeg conversion error"

# ==== Root ====
@app.route("/")
def home():
    return "SpotTool API is live"

# ==== Download Endpoint ====
@app.route("/download", methods=["POST"])
def download():
    data = request.get_json()
    spotify_url = data.get("spotify_url")

    if not spotify_url:
        return jsonify({"error": "Missing Spotify URL"}), 400

    song_name, artist_name = get_track_info(spotify_url)
    if not song_name:
        return jsonify({"error": "Failed to get track info"}), 500

    query = f"{song_name} {artist_name} audio"
    youtube_url = search_youtube(query)
    if not youtube_url:
        return jsonify({"error": "Failed to find song on YouTube"}), 500

    mp3_file, error = download_mp3(youtube_url, song_name, artist_name)
    if error:
        return jsonify({"error": error}), 500

    return send_file(mp3_file, as_attachment=True)

# ==== Start App ====
if __name__ == "__main__":
    app.run(debug=True)
