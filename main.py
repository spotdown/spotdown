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

        # Get song title from Spotify oEmbed
        info = requests.get(f"https://open.spotify.com/oembed?url={spotify_url}").json()
        title = info.get("title", "").strip()
        artist = info.get("author_name", "Unknown").strip()
        query = f"{title} {artist}"

        # SoundCloud search
        search_url = f"https://soundcloud.com/search?q={query}"
        api = SoundcloudAPI()
        track: Track = api.resolve(search_url)
        if not track:
            return jsonify({"error": "No SoundCloud match found"}), 404

        # Download MP3
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
