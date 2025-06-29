from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import requests, yt_dlp, os, uuid, subprocess
from sclib import SoundcloudAPI

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return "✅ Backend running: JioSaavn → YouTube → SoundCloud"

@app.route('/download', methods=['POST'])
def download():
    webm_file = None
    mp3_file = None
    try:
        data = request.get_json()
        spotify_url = data.get("spotify_url", "").strip()
        if not spotify_url:
            return jsonify({"error": "Missing Spotify URL"}), 400

        info = requests.get(f"https://open.spotify.com/oembed?url={spotify_url}").json()
        title = info.get("title", "").strip()
        artist = info.get("author_name", "Unknown").strip()
        query = f"{title} {artist}"
        mp3_file = f"{uuid.uuid4()}.mp3"

        # 🔹 1. JioSaavn
        saavn_search = requests.get(f"https://saavn.dev/api/search/songs?query={query}").json()
        results = saavn_search.get("data", {}).get("results", [])
        for song in results:
            song_id = song["id"]
            detail = requests.get(f"https://saavn.dev/api/songs?id={song_id}").json()
            if "data" in detail and detail["data"]:
                dl = detail["data"][0].get("downloadUrl", {})
                mp3_url = dl.get("high") or dl.get("medium") or dl.get("low")
                if mp3_url:
                    with open(mp3_file, "wb") as f:
                        f.write(requests.get(mp3_url).content)
                    return send_file(mp3_file, as_attachment=True)

        # 🔹 2. YouTube fallback
        webm_file = f"{uuid.uuid4()}.webm"
        ydl_opts = {
            "format": "bestaudio/best",
            "noplaylist": True,
            "quiet": True,
            "outtmpl": webm_file
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            results = ydl.extract_info(f"ytsearch10:{query}", download=False)
            for entry in results.get("entries", []):
                if (
                    entry.get("age_limit", 0) > 17 or
                    entry.get("duration", 0) > 600 or
                    any(k in entry.get("title", "").lower() for k in ["live", "reaction", "official video"]) or
                    "vevo" in entry.get("uploader", "").lower()
                ):
                    continue
                video_url = entry["webpage_url"]
                ydl.download([video_url])
                subprocess.run(["ffmpeg", "-i", webm_file, "-vn", "-ab", "192k", "-ar", "44100", "-y", mp3_file])
                return send_file(mp3_file, as_attachment=True)

        # 🔹 3. SoundCloud fallback
        api = SoundcloudAPI()
        track = api.resolve(f"https://soundcloud.com/search?q={query}")
        with open(mp3_file, "wb+") as f:
            track.write_mp3_to(f)
        return send_file(mp3_file, as_attachment=True)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        for f in [webm_file, mp3_file]:
            if f and os.path.exists(f):
                os.remove(f)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
