import os
import requests
import json
from flask import Flask, redirect, request, session, url_for
from dotenv import load_dotenv
from urllib.parse import urlencode

# Carregar variáveis de ambiente
load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Garante sessões seguras

# --- SPOTIFY CONFIG ---
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
SPOTIFY_REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI')
SPOTIFY_SCOPE = 'playlist-read-private user-library-read'

# --- YOUTUBE CONFIG ---
YOUTUBE_CLIENT_ID = os.getenv('YOUTUBE_CLIENT_ID')
YOUTUBE_CLIENT_SECRET = os.getenv('YOUTUBE_CLIENT_SECRET')
YOUTUBE_REDIRECT_URI = os.getenv('YOUTUBE_REDIRECT_URI')
YOUTUBE_SCOPE = 'https://www.googleapis.com/auth/youtube'

# --- ROTAS ---

@app.route('/')
def index():
    return '''
        <h2>StreamSync</h2>
        <a href="/login/spotify">Conectar com Spotify</a><br>
        <a href="/login/youtube">Conectar com YouTube</a><br><br>
        <a href="/sync">Sincronizar Playlist</a>
    '''

# --- AUTENTICAÇÃO SPOTIFY ---

@app.route('/login/spotify')
def login_spotify():
    params = {
        'client_id': SPOTIFY_CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': SPOTIFY_REDIRECT_URI,
        'scope': SPOTIFY_SCOPE
    }
    return redirect(f"https://accounts.spotify.com/authorize?{urlencode(params)}")

@app.route('/callback/spotify')
def callback_spotify():
    code = request.args.get('code')
    response = requests.post("https://accounts.spotify.com/api/token", data={
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': SPOTIFY_REDIRECT_URI,
        'client_id': SPOTIFY_CLIENT_ID,
        'client_secret': SPOTIFY_CLIENT_SECRET
    })
    session['spotify_token'] = response.json()['access_token']
    return redirect(url_for('index'))

# --- AUTENTICAÇÃO YOUTUBE ---

@app.route('/login/youtube')
def login_youtube():
    params = {
        'client_id': YOUTUBE_CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': YOUTUBE_REDIRECT_URI,
        'scope': YOUTUBE_SCOPE,
        'access_type': 'offline',
        'prompt': 'consent'
    }
    return redirect(f"https://accounts.google.com/o/oauth2/auth?{urlencode(params)}")

@app.route('/callback/youtube')
def callback_youtube():
    code = request.args.get('code')
    response = requests.post("https://oauth2.googleapis.com/token", data={
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': YOUTUBE_REDIRECT_URI,
        'client_id': YOUTUBE_CLIENT_ID,
        'client_secret': YOUTUBE_CLIENT_SECRET
    })
    session['youtube_token'] = response.json()['access_token']
    return redirect(url_for('index'))

# --- SINC PLAYLIST SPOTIFY → YOUTUBE ---

@app.route('/sync')
def sync():
    if 'spotify_token' not in session or 'youtube_token' not in session:
        return 'Você precisa se autenticar no Spotify e YouTube primeiro.'

    # 1. PEGAR PLAYLIST DO SPOTIFY
    playlist_id = 'INSIRA_ID_DA_PLAYLIST_AQUI'  # ← Substitua aqui pelo ID desejado
    spotify_headers = {
        'Authorization': f"Bearer {session['spotify_token']}"
    }

    tracks_url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
    response = requests.get(tracks_url, headers=spotify_headers)
    items = response.json().get('items', [])

    # 2. BUSCAR CADA MÚSICA NO YOUTUBE
    video_ids = []
    for item in items:
        name = item['track']['name']
        artist = item['track']['artists'][0]['name']
        query = f"{name} {artist}"
        yt_search_url = f"https://www.googleapis.com/youtube/v3/search"
        yt_params = {
            'part': 'snippet',
            'q': query,
            'type': 'video',
            'key': os.getenv("YOUTUBE_API_KEY"),  # ← Use uma API Key do YouTube se preferir essa forma
            'maxResults': 1
        }
        yt_response = requests.get(yt_search_url, params=yt_params)
        results = yt_response.json().get('items', [])
        if results:
            video_id = results[0]['id']['videoId']
            video_ids.append(video_id)

    # 3. CRIAR PLAYLIST NO YOUTUBE
    youtube_token = session['youtube_token']
    headers = {
        'Authorization': f"Bearer {youtube_token}",
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }

    playlist_data = {
        'snippet': {
            'title': 'Playlist importada do Spotify',
            'description': 'Gerada automaticamente via StreamSync',
        },
        'status': {
            'privacyStatus': 'private'
        }
    }

    create_playlist = requests.post(
        'https://www.googleapis.com/youtube/v3/playlists?part=snippet,status',
        headers=headers,
        data=json.dumps(playlist_data)
    )
    playlist_id_yt = create_playlist.json()['id']

    # 4. ADICIONAR VÍDEOS
    for vid in video_ids:
        add_video_data = {
            'snippet': {
                'playlistId': playlist_id_yt,
                'resourceId': {
                    'kind': 'youtube#video',
                    'videoId': vid
                }
            }
        }
        requests.post(
            'https://www.googleapis.com/youtube/v3/playlistItems?part=snippet',
            headers=headers,
            data=json.dumps(add_video_data)
        )

    return f'Playlist criada com {len(video_ids)} vídeos no YouTube!'

# --- INICIAR SERVIDOR ---

if __name__ == '__main__':
    app.run(debug=True)
