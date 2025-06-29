from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import requests, os, uuid

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return "✅ Archive.org backend running!"

@app.route('/download', methods=['POST'])
def download():
    mp3_file = None
    try:
        data = request.get_json()
        spotify_url = data.get("spotify_url", "").strip()
        if not spotify_url:
            return jsonify({"error": "Missing Spotify URL"}), 400

        info = requests.get(f"https://open.spotify.com/oembed?url={spotify_url}")
        if info.status_code != 200:
            return jsonify({"error": "Could not fetch Spotify info"}), 400

        title = info.json().get("title", "").strip()
        artist = info.json().get("author_name", "").strip()
        query = f"{title} {artist}"

        search = requests.get(
            "https://archive.org/advancedsearch.php",
            params={
                "q": query,
                "fl[]": "identifier,format",
                "rows": 5,
                "output": "json"
            }
        )
        results = search.json().get("response", {}).get("docs", [])
        if not results:
            return jsonify({"error": "No audio found on archive.org"}), 404

        file_id, fmt = results[0]["identifier"], results[0]["format"][0]
        mp3_url = f"https://archive.org/download/{file_id}/{file_id}.{fmt.lower()}"
        mp3_file = f"{uuid.uuid4()}.{fmt.lower()}"

        dl = requests.get(mp3_url, stream=True)
        if dl.status_code != 200:
            return jsonify({"error": "Failed downloading archive.org audio"}), 500

        with open(mp3_file, "wb") as f:
            for chunk in dl.iter_content(1024 * 1024):
                f.write(chunk)

        return send_file(mp3_file, as_attachment=True)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if mp3_file and os.path.exists(mp3_file):
            os.remove(mp3_file)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
