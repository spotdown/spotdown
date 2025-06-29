import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from yt_dlp import YoutubeDL
from mutagen.easyid3 import EasyID3
from mutagen.id3 import APIC, ID3
import requests
from dotenv import load_dotenv

load_dotenv()

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=os.getenv("SPOTIFY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIFY_CLIENT_SECRET")
))


def search_youtube(query: str) -> str:
    with YoutubeDL({'quiet': True}) as ydl:
        result = ydl.extract_info(f"ytsearch:{query}", download=False)['entries'][0]
        return result['webpage_url']


def download_audio(url: str, output_path: str) -> str:
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_path,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
        }]
    }
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return output_path.replace('.%(ext)s', '.mp3')


def tag_mp3(mp3_path: str, title: str, artist: str, album: str, cover_url: str):
    audio = EasyID3(mp3_path)
    audio['title'] = title
    audio['artist'] = artist
    audio['album'] = album
    audio.save()

    id3 = ID3(mp3_path)
    cover_data = requests.get(cover_url).content
    id3.add(APIC(encoding=3, mime='image/jpeg', type=3, desc='Cover', data=cover_data))
    id3.save()


def process_spotify_url(spotify_url: str) -> str:
    track_id = spotify_url.split("/")[-1].split("?")[0]
    track = sp.track(track_id)

    title = track['name']
    artist = track['artists'][0]['name']
    album = track['album']['name']
    cover_url = track['album']['images'][0]['url']

    query = f"{title} {artist}"
    youtube_url = search_youtube(query)

    os.makedirs("downloads", exist_ok=True)
    output_template = f"downloads/{title}_{artist}.%(ext)s"
    mp3_path = download_audio(youtube_url, output_template)
    tag_mp3(mp3_path, title, artist, album, cover_url)

    return mp3_path
