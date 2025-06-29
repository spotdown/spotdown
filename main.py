from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import requests, os, uuid
from sclib import SoundcloudAPI, Track

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return "✅ SoundCloud-only backend is running!"

@app.route('/download', methods=['POST'])
def download():
    mp3_file = None
    try:
        data = request.get_json()
        spotify_url = data.get("spotify_url", "").strip()
        if not spotify_url:
            return jsonify({"error": "Missing Spotify URL"}), 400

        # Step 1: Extract title + artist from Spotify oEmbed
        info = requests.get(f"https://open.spotify.com/oembed?url={spotify_url}").json()
        title = info.get("title", "").strip()
        artist = info.get("author_name", "Unknown").strip()
        query = f"{title} {artist}"

        # Step 2: Search SoundCloud HTML
        search_url = f"https://soundcloud.com/search/sounds?q={query}"
        search_html = requests.get(search_url).text

        # Step 3: Extract first valid permalink
        try:
            permalink = search_html.split('"permalink_url":"')[1].split('"')[0]
            permalink = permalink.replace("\\u002F", "/")
            if not permalink.startswith("http"):
                permalink = f"https://{permalink}"
        except Exception:
            return jsonify({"error": "No SoundCloud track found"}), 404

        # Step 4: Resolve track + download
        api = SoundcloudAPI()
        track: Track = api.resolve(permalink)

        mp3_file = f"{uuid.uuid4()}.mp3"
        with open(mp3_file, "wb+") as f:
            track.write_mp3_to(f)

        return send_file(mp3_file, as_attachment=True)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if mp3_file and os.path.exists(mp3_file):
            os.remove(mp3_file)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
