from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import requests
import yt_dlp
import os
import uuid
import subprocess
from sclib import SoundcloudAPI

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return "✅ Hybrid MP3 backend: JioSaavn → YouTube → SoundCloud"

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
        query = f"{title} {artist}"
        mp3_file = f"{uuid.uuid4()}.mp3"

        # 🔹 JioSaavn logic (as before)
        search_res = requests.get(f"https://saavn.dev/api/search/songs?query={query}").json()
        if "data" in search_res and search_res["data"]["results"]:
            for s in search_res["data"]["results"]:
                dr = requests.get(f"https://saavn.dev/api/songs?id={s['id']}").json()
                if "data" in dr and dr["data"]:
                    dl = dr["data"][0].get("downloadUrl", {})
                    url = dl.get("high") or dl.get("medium") or dl.get("low")
                    if url:
                        mp3_content = requests.get(url).content
                        with open(mp3_file, "wb") as f:
                            f.write(mp3_content)
                        return send_file(mp3_file, as_attachment=True)

        # 🔹 YouTube fallback (as before)
        webm_file = f"{uuid.uuid4()}.webm"
        opts = {"format":"bestaudio/best","noplaylist":True,"quiet":True,"outtmpl":webm_file}
        with yt_dlp.YoutubeDL(opts) as ydl:
            sr = ydl.extract_info(f"ytsearch10:{query}", download=False)
            safe = next((e["webpage_url"] for e in sr["entries"] if
                         e.get("duration",0)<600 and
                         all(k not in e.get("title","").lower() for k in ["live","reaction","official video"]) and
                         "vevo" not in e.get("uploader","").lower()),
                        None)
            if safe:
                ydl.download([safe])
                subprocess.run(["ffmpeg","-i",webm_file,"-vn","-ab","192k","-ar","44100","-y",mp3_file])
                return send_file(mp3_file, as_attachment=True)

        # 🔹 SoundCloud fallback using soundcloud-lib
        api = SoundcloudAPI()
        track = api.resolve(f"https://soundcloud.com/search?q={query}")
        with open(mp3_file, "wb+") as f:
            track.write_mp3_to(f)
        return send_file(mp3_file, as_attachment=True)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        for fpath in [webm_file, mp3_file]:
            if fpath and os.path.exists(fpath):
                os.remove(fpath)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
