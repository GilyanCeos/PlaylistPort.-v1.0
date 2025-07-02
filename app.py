import os
import requests
import json
from flask import Flask, redirect, request, session, url_for
from dotenv import load_dotenv
from urllib.parse import urlencode

# Carregar variáveis de ambiente do .env
load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

# ----- Configurações Spotify -----
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
SPOTIFY_REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI')
SPOTIFY_SCOPE = 'playlist-read-private user-library-read'

# ----- Configurações YouTube -----
YOUTUBE_CLIENT_ID = os.getenv('YOUTUBE_CLIENT_ID')
YOUTUBE_CLIENT_SECRET = os.getenv('YOUTUBE_CLIENT_SECRET')
YOUTUBE_REDIRECT_URI = os.getenv('YOUTUBE_REDIRECT_URI')
YOUTUBE_SCOPE = 'https://www.googleapis.com/auth/youtube'
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')

# ----- Rotas principais -----
@app.route('/')
def index():
    return '''
        <h1>Playlist Port</h1>
        <p>Sincronize suas playlists entre plataformas</p>
        <a href="/login/spotify">Conectar com Spotify</a><br>
        <a href="/login/youtube">Conectar com YouTube</a><br><br>
        <a href="/sync">Sincronizar Playlist</a>
    '''

# ----- Autenticação Spotify -----
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
    token_url = "https://accounts.spotify.com/api/token"
    response = requests.post(token_url, data={
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': SPOTIFY_REDIRECT_URI,
        'client_id': SPOTIFY_CLIENT_ID,
        'client_secret': SPOTIFY_CLIENT_SECRET
    })
    session['spotify_token'] = response.json().get('access_token')
    return redirect(url_for('index'))

# ----- Autenticação YouTube -----
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
    token_url = "https://oauth2.googleapis.com/token"
    response = requests.post(token_url, data={
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': YOUTUBE_REDIRECT_URI,
        'client_id': YOUTUBE_CLIENT_ID,
        'client_secret': YOUTUBE_CLIENT_SECRET
    })
    session['youtube_token'] = response.json().get('access_token')
    return redirect(url_for('index'))

# ----- Sincronização -----
@app.route('/sync')
def sync():
    if 'spotify_token' not in session or 'youtube_token' not in session:
        return 'Por favor, autentique-se no Spotify e YouTube primeiro.'

    spotify_token = session['spotify_token']
    youtube_token = session['youtube_token']

    # Pegando tracks do Spotify (playlist fixa ou editável)
    playlist_id = 'collection/tracks'
    headers_spotify = { 'Authorization': f"Bearer {spotify_token}" }
    tracks_url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
    response = requests.get(tracks_url, headers=headers_spotify)
    items = response.json().get('items', [])

    # Buscar músicas no YouTube
    video_ids = []
    for item in items:
        track = item['track']
        query = f"{track['name']} {track['artists'][0]['name']}"
        yt_search_url = "https://www.googleapis.com/youtube/v3/search"
        yt_params = {
            'part': 'snippet',
            'q': query,
            'type': 'video',
            'maxResults': 1,
            'key': YOUTUBE_API_KEY
        }
        yt_response = requests.get(yt_search_url, params=yt_params)
        results = yt_response.json().get('items', [])
        if results:
            video_ids.append(results[0]['id']['videoId'])

    # Criar playlist no YouTube
    yt_headers = {
        'Authorization': f"Bearer {youtube_token}",
        'Content-Type': 'application/json'
    }
    playlist_data = {
        'snippet': {
            'title': 'Playlist importada do Spotify',
            'description': 'Gerada automaticamente pelo Playlist Port'
        },
        'status': {
            'privacyStatus': 'private'
        }
    }
    yt_create = requests.post(
        'https://www.googleapis.com/youtube/v3/playlists?part=snippet,status',
        headers=yt_headers,
        data=json.dumps(playlist_data)
    )
    playlist_id_yt = yt_create.json().get('id')

    # Adicionar vídeos à playlist do YouTube
    for vid in video_ids:
        insert_data = {
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
            headers=yt_headers,
            data=json.dumps(insert_data)
        )

    return f'Playlist criada com {len(video_ids)} vídeos no YouTube!'

if __name__ == '__main__':
    app.run(debug=True)
