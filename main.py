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
    return "✅ Spotmod backend running (Safe YouTube version)"

@app.route('/download', methods=['POST'])
def download():
    webm_file = None
    mp3_file = None
    try:
        data = request.get_json()
        spotify_url = data.get("spotify_url")

        if not spotify_url:
            return jsonify({"error": "Missing Spotify URL"}), 400

        res = requests.get(f"https://open.spotify.com/oembed?url={spotify_url}")
        if res.status_code != 200:
            return jsonify({"error": f"Spotify oEmbed failed: {res.status_code}"}), 400

        info = res.json()
        title = info.get("title", "").strip()
        artist = info.get("author_name", "Unknown Artist").strip()
        search_query = f"{title} {artist}"
        webm_file = f"{uuid.uuid4()}.webm"
        mp3_file = f"{title} - {artist}.mp3"

        ydl_opts = {
            "format": "bestaudio/best",
            "noplaylist": True,
            "outtmpl": webm_file,
            "quiet": True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            results = ydl.extract_info(f"ytsearch10:{search_query}", download=False)
            for entry in results.get("entries", []):
                if entry.get("age_limit", 0) > 17:
                    continue
                if entry.get("is_live"):
                    continue
                if entry.get("duration", 0) > 600:
                    continue
                if "official" in entry.get("title", "").lower():
                    continue
                try:
                    ydl.download([entry["webpage_url"]])
                    break
                except Exception as e:
                    continue
            else:
                return jsonify({"error": "No playable YouTube video found"}), 404

        subprocess.run(["ffmpeg", "-i", webm_file, "-vn", "-ab", "192k", "-ar", "44100", "-y", mp3_file])
        return send_file(mp3_file, as_attachment=True)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        for file in [webm_file, mp3_file]:
            if file and os.path.exists(file):
                os.remove(file)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
