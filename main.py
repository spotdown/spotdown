
import os
import subprocess
import uuid
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import requests
import yt_dlp

app = Flask(__name__)
CORS(app)

SPOTIFY_CLIENT_ID = "ad0720ec13024b85b3843b39cf06ee16"
SPOTIFY_CLIENT_SECRET = "f1469bb0f25d40959b903dd5618ea179"

auth_response = requests.post(
    'https://accounts.spotify.com/api/token',
    data={'grant_type': 'client_credentials'},
    auth=(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)
)
if auth_response.status_code == 200:
    access_token = auth_response.json().get('access_token')
else:
    access_token = None

@app.route('/')
def home():
    return 'Spotify Downloader Backend Running'

@app.route('/download', methods=['POST'])
def download():
    if request.method != 'POST':
        return jsonify({'error': 'Method not allowed'}), 405

    data = request.get_json()
    spotify_url = data.get('spotify_url')
    if not spotify_url or 'track' not in spotify_url:
        return jsonify({'error': 'Invalid Spotify URL'}), 400

    if not access_token:
        return jsonify({'error': 'Failed to get Spotify token'}), 500

    track_id = spotify_url.split("/")[-1].split("?")[0]
    headers = {'Authorization': f'Bearer {access_token}'}
    spotify_response = requests.get(f'https://api.spotify.com/v1/tracks/{track_id}', headers=headers)
    if spotify_response.status_code != 200:
        return jsonify({'error': 'Failed to get track info'}), 500

    track_info = spotify_response.json()
    song_name = track_info['name']
    artist_name = track_info['artists'][0]['name']
    search_query = f"{song_name} {artist_name} audio"

    download_id = str(uuid.uuid4())
    webm_file = f"{download_id}.webm"
    mp3_file = f"{song_name} - {artist_name}.mp3"

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': webm_file,
        'noplaylist': True,
        'quiet': True,
        'cookies': 'cookies.txt',
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            search_result = ydl.extract_info(f"ytsearch:{search_query}", download=True)['entries'][0]
        except Exception as e:
            return jsonify({'error': 'Failed to find song on YouTube', 'details': str(e)}), 500

    try:
        subprocess.run(["ffmpeg", "-i", webm_file, "-vn", "-ab", "192k", "-ar", "44100", "-y", mp3_file], check=True)
    except Exception as e:
        return jsonify({'error': 'Failed to convert to MP3', 'details': str(e)}), 500

    return send_file(mp3_file, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
