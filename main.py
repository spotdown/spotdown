from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import requests
import yt_dlp
import os
import uuid
import subprocess

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return "✅ Spotmod backend running!"

@app.route('/download', methods=['POST'])
def download():
    webm_file = None
    mp3_file = None
    try:
        data = request.get_json()
        spotify_url = data.get("spotify_url")

        if not spotify_url:
            return jsonify({"error": "Missing Spotify URL"}), 400

        # Fetch metadata
        res = requests.get(f"https://open.spotify.com/oembed?url={spotify_url}")
        if res.status_code != 200:
            return jsonify({"error": f"Spotify oEmbed failed: {res.status_code}"}), 400

        info = res.json()

        # Title is required
        title = info.get("title", "").strip()
        if not title:
            return jsonify({"error": "Could not extract song title from Spotify"}), 400

        # Artist is optional
        artist = info.get("author_name", "Unknown Artist").strip()

        # Prepare file names
        search_query = f"{title} {artist}"
        webm_file = f"{uuid.uuid4()}.webm"
        mp3_file = f"{title} - {artist}.mp3"

        # Download from YouTube
        ydl_opts = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "quiet": True,
    "outtmpl": webm_file
}

search_query = f"{title} {artist} audio lyrics"

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    search_result = ydl.extract_info(f"ytsearch10:{search_query}", download=False)
    safe_video = None

    for entry in search_result.get("entries", []):
        title_text = entry.get("title", "").lower()
        uploader = entry.get("uploader", "").lower()
        duration = entry.get("duration", 0)

        if (
            duration < 600 and
            "explicit" not in title_text and
            "vevo" not in uploader and
            "official" not in title_text
        ):
            safe_video = entry["webpage_url"]
            break

    if not safe_video:
        return jsonify({"error": "No clean YouTube video found"}), 404

    # ✅ Now download safe video
    ydl.download([safe_video])
        # Convert to MP3
        subprocess.run(["./ffmpeg", "-i", webm_file, "-vn", "-ab", "192k", "-ar", "44100", "-y", mp3_file])

        return send_file(mp3_file, as_attachment=True)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        try:
            if webm_file and os.path.exists(webm_file):
                os.remove(webm_file)
            if mp3_file and os.path.exists(mp3_file):
                os.remove(mp3_file)
        except:
            pass

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
