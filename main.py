
import os
import threading
import uuid
import subprocess
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

COOKIES_FILE = "cookies.txt"

def download_and_convert(spotify_url, mp3_path, error_flag):
    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(DOWNLOAD_DIR, '%(id)s.%(ext)s'),
            'cookiefile': COOKIES_FILE,
            'quiet': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(spotify_url, download=True)
            title = info.get('title', 'Unknown Title')
            artist = info.get('artist') or info.get('uploader', 'Unknown Artist')
            filename = ydl.prepare_filename(info)
        
        mp3_file = os.path.join(DOWNLOAD_DIR, f"{title} - {artist}.mp3")
        subprocess.run([
            "ffmpeg", "-i", filename, "-vn",
            "-ab", "192k", "-ar", "44100", "-y", mp3_file
        ], check=True)
        
        os.rename(mp3_file, mp3_path)

    except Exception as e:
        error_flag.append(str(e))

@app.route("/download", methods=["POST"])
def download():
    data = request.get_json()
    spotify_url = data.get("spotify_url")

    if not spotify_url:
        return jsonify({"error": "spotify_url is required"}), 400

    unique_id = str(uuid.uuid4())
    mp3_path = os.path.join(DOWNLOAD_DIR, f"{unique_id}.mp3")
    error_flag = []
    thread = threading.Thread(target=download_and_convert, args=(spotify_url, mp3_path, error_flag))
    thread.start()
    thread.join(timeout=25)

    if thread.is_alive():
        return jsonify({"error": "Conversion timeout. Try again later."}), 500
    if error_flag:
        return jsonify({"error": error_flag[0]}), 500
    if not os.path.exists(mp3_path):
        return jsonify({"error": "MP3 not found after processing."}), 500

    return send_file(mp3_path, as_attachment=True)
