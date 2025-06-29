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
    return "✅ Hybrid MP3 backend running (JioSaavn + YouTube fallback)!"

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
        info = res.json()
        title = info.get("title", "").strip()
        artist = info.get("author_name", "Unknown Artist").strip()
        search_query = f"{title} {artist}"
        mp3_file = f"{title} - {artist}.mp3"

        # Try JioSaavn
        search_url = f"https://saavn.dev/api/search/songs?query={search_query}"
        search_res = requests.get(search_url).json()

        mp3_url = None
        if "data" in search_res and search_res["data"]["results"]:
            for song in search_res["data"]["results"]:
                song_id = song["id"]
                detail_url = f"https://saavn.dev/api/songs?id={song_id}"
                detail_res = requests.get(detail_url).json()

                if "data" not in detail_res or not detail_res["data"]:
                    continue

                download = detail_res["data"][0].get("downloadUrl", {})
                mp3_url = download.get("high") or download.get("medium") or download.get("low")

                if mp3_url:
                    mp3_file = f"{uuid.uuid4()}.mp3"
                    mp3_content = requests.get(mp3_url).content
                    with open(mp3_file, "wb") as f:
                        f.write(mp3_content)
                    return send_file(mp3_file, as_attachment=True)

        # Fallback to YouTube
        webm_file = f"{uuid.uuid4()}.webm"
        ydl_opts = {
            "format": "bestaudio/best",
            "noplaylist": True,
            "quiet": True,
            "outtmpl": webm_file
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            search_result = ydl.extract_info(f"ytsearch10:{search_query}", download=False)
            safe_video = None
            for entry in search_result.get("entries", []):
                title_text = entry.get("title", "").lower()
                uploader = entry.get("uploader", "").lower()
                duration = entry.get("duration", 0)

                if (
                    duration < 600 and
                    "live" not in title_text and
                    "reaction" not in title_text and
                    "vevo" not in uploader and
                    "official video" not in title_text
                ):
                    safe_video = entry["webpage_url"]
                    break

            if not safe_video:
                return jsonify({"error": "No safe YouTube result found"}), 404

            ydl.download([safe_video])

        subprocess.run(["ffmpeg", "-i", webm_file, "-vn", "-ab", "192k", "-ar", "44100", "-y", mp3_file])
        return send_file(mp3_file, as_attachment=True)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        for f in [webm_file, mp3_file]:
            if f and os.path.exists(f):
                os.remove(f)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
