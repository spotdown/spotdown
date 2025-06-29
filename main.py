@app.route('/download', methods=['POST'])
def download():
    webm_file = None
    mp3_file = None
    try:
        data = request.get_json()
        spotify_url = data.get("spotify_url")

        if not spotify_url:
            return jsonify({"error": "Missing Spotify URL"}), 400

        # Fetch Spotify metadata
        res = requests.get(f"https://open.spotify.com/oembed?url={spotify_url}")
        info = res.json()
        title = info.get("title", "").strip()
        artist = info.get("author_name", "Unknown Artist").strip()
        search_query = f"{title} {artist} audio lyrics"

        webm_file = f"{uuid.uuid4()}.webm"
        mp3_file = f"{title} - {artist}.mp3"

        ydl_opts = {
            "format": "bestaudio/best",
            "noplaylist": True,
            "quiet": True,
            "outtmpl": webm_file
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            search_result = ydl.extract_info(f"ytsearch10:{search_query}", download=False)
            safe_video = None

            for entry in search_result.get("entries", []):
                title_text = entry.get("title", "").lower()
                uploader = entry.get("uploader", "").lower()
                duration = entry.get("duration", 0)

                if (
                    duration < 600 and
                    "explicit" not in title_text and
                    "vevo" not in uploader and
                    "official" not in title_text
                ):
                    safe_video = entry["webpage_url"]
                    break

            if not safe_video:
                return jsonify({"error": "No clean YouTube video found"}), 404

            ydl.download([safe_video])

        subprocess.run(["ffmpeg", "-i", webm_file, "-vn", "-ab", "192k", "-ar", "44100", "-y", mp3_file])

        return send_file(mp3_file, as_attachment=True)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        for f in [webm_file, mp3_file]:
            if f and os.path.exists(f):
                os.remove(f)
