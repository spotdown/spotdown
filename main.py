from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import requests
import os
import uuid

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return "✅ JioSaavn MP3 backend running!"

@app.route('/download', methods=['POST'])
def download():
    mp3_file = None
    try:
        data = request.get_json()
        spotify_url = data.get("spotify_url")

        if not spotify_url:
            return jsonify({"error": "Missing Spotify URL"}), 400

        # Get metadata from Spotify oEmbed
        res = requests.get(f"https://open.spotify.com/oembed?url={spotify_url}")
        if res.status_code != 200:
            return jsonify({"error": "Spotify oEmbed failed"}), 400

        info = res.json()
        title = info.get("title", "").strip()
        artist = info.get("author_name", "Unknown Artist").strip()

        if not title:
            return jsonify({"error": "Missing title from Spotify"}), 400

        search_query = f"{title} {artist}"
        search_url = f"https://saavn.dev/api/search/songs?query={search_query}"
        search_res = requests.get(search_url).json()

        if "data" not in search_res or not search_res["data"]["results"]:
            return jsonify({"error": "No matching song found on JioSaavn"}), 404

        mp3_url = None
        for song in search_res["data"]["results"]:
            song_id = song["id"]
            detail_url = f"https://saavn.dev/api/songs?id={song_id}"
            detail_res = requests.get(detail_url).json()

            if (
                "data" in detail_res and detail_res["data"] and
                detail_res["data"][0]["downloadUrl"]["high"]
            ):
                mp3_url = detail_res["data"][0]["downloadUrl"]["high"]
                break  # found working MP3, stop loop

        if not mp3_url:
            return jsonify({"error": "No playable MP3 found for any search result"}), 404

        mp3_file = f"{uuid.uuid4()}.mp3"
        mp3_content = requests.get(mp3_url).content
        with open(mp3_file, "wb") as f:
            f.write(mp3_content)

        return send_file(mp3_file, as_attachment=True)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if mp3_file and os.path.exists(mp3_file):
            os.remove(mp3_file)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
