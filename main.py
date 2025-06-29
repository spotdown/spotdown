from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import requests, yt_dlp, os, uuid, subprocess
from sclib import SoundcloudAPI

app = Flask(__name__); CORS(app)

@app.route('/')
def home():
    return "✅ Hybrid backend: JioSaavn → YouTube → SoundCloud"

@app.route('/download', methods=['POST'])
def download():
    webm, mp3 = None, None
    try:
        spotify_url = request.get_json().get("spotify_url","")
        if not spotify_url:
            return jsonify({"error": "Missing Spotify URL"}), 400

        info = requests.get(f"https://open.spotify.com/oembed?url={spotify_url}").json()
        title, artist = info.get("title","").strip(), info.get("author_name","Unknown").strip()
        query = f"{title} {artist}"
        mp3 = f"{uuid.uuid4()}.mp3"

        # 🔹 JioSaavn
        sr = requests.get(f"https://saavn.dev/api/search/songs?query={query}").json().get("data",{}).get("results",[])
        for s in sr:
            dr = requests.get(f"https://saavn.dev/api/songs?id={s['id']}").json().get("data",[])
            if dr:
                dl = dr[0].get("downloadUrl",{})
                url = dl.get("high") or dl.get("medium") or dl.get("low")
                if url:
                    with open(mp3,"wb") as f: f.write(requests.get(url).content)
                    return send_file(mp3, as_attachment=True)

        # 🔹 YouTube (via yt_dlp)
        webm = f"{uuid.uuid4()}.webm"
        opts = {"format":"bestaudio/best","noplaylist":True,"quiet":True,"outtmpl":webm}
        with yt_dlp.YoutubeDL(opts) as ydl:
            sr = ydl.extract_info(f"ytsearch10:{query}", download=False)
            safe = next((e["webpage_url"] for e in sr["entries"] 
                         if e.get("duration",0)<600
                         and all(k not in e.get("title","").lower() for k in ["live","reaction","official video"])
                         and "vevo" not in e.get("uploader","").lower()), None)
            if safe:
                ydl.download([safe])
                subprocess.run(["ffmpeg","-i",webm,"-vn","-ab","192k","-ar","44100","-y",mp3])
                return send_file(mp3, as_attachment=True)

        # 🔹 SoundCloud (via soundcloud-lib)
        api = SoundcloudAPI()
        track = api.resolve(f"https://soundcloud.com/search?q={query}")
        with open(mp3,"wb+") as f:
            track.write_mp3_to(f)
        return send_file(mp3, as_attachment=True)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        for f in [webm, mp3]:
            if f and os.path.exists(f):
                os.remove(f)

if __name__=="__main__":
    app.run(host="0.0.0.0", port=8080)
