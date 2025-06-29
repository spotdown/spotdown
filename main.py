from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import requests, uuid, os

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return "✅ Audius-only backend is running!"

@app.route('/download', methods=['POST'])
def download():
    mp3_file = None
    try:
        data = request.get_json()
        spotify_url = data.get("spotify_url", "").strip()
        if not spotify_url:
            return jsonify({"error": "Missing Spotify URL"}), 400

        # 1. Get title/artist from Spotify
        info = requests.get(f"https://open.spotify.com/oembed?url={spotify_url}").json()
        title = info.get("title", "").strip()
        artist = info.get("author_name", "Unknown").strip()
        query = f"{title} {artist}"

        # 2. Search Audius
        search = requests.get(f"https://discoveryprovider.audius.co/v1/tracks/search", params={"query": query, "app_name": "spotmod"}).json()
        results = search.get("data", [])

        if not results:
            return jsonify({"error": "No Audius track found"}), 404

        # 3. Get streaming URL
        stream_url = results[0].get("stream_url")
        if not stream_url:
            return jsonify({"error": "No streaming URL in track"}), 500

        # 4. Download MP3 and return
        mp3_file = f"{uuid.uuid4()}.mp3"
        content = requests.get(stream_url, headers={"Accept": "*/*"}).content
        with open(mp3_file, "wb") as f:
            f.write(content)

        return send_file(mp3_file, as_attachment=True)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if mp3_file and os.path.exists(mp3_file):
            os.remove(mp3_file)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
