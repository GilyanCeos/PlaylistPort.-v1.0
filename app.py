import os
import requests
import json
from flask import Flask, redirect, request, session, url_for, render_template # Adicione render_template aqui
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
SPOTIFY_SCOPE = 'playlist-read-private playlist-modify-private'

# ----- Configurações YouTube -----
YOUTUBE_CLIENT_ID = os.getenv('YOUTUBE_CLIENT_ID')
YOUTUBE_CLIENT_SECRET = os.getenv('YOUTUBE_CLIENT_SECRET')
YOUTUBE_REDIRECT_URI = os.getenv('YOUTUBE_REDIRECT_URI')
YOUTUBE_SCOPE = 'https://www.googleapis.com/auth/youtube'
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')

# ----- Rotas principais -----
@app.route('/')
def index():
    return render_template('index.html') # <--- MUDANÇA AQUI!

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
    if response.status_code == 200:
        session['spotify_token'] = response.json().get('access_token')
        return redirect(url_for('index', auth_status='success', service='spotify')) # Adicionado
    else:
        return redirect(url_for('index', auth_status='error', service='spotify')) # Adicionado

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
    if response.status_code == 200:
        session['youtube_token'] = response.json().get('access_token')
        return redirect(url_for('index', auth_status='success', service='youtube')) # Adicionado
    else:
        return redirect(url_for('index', auth_status='error', service='youtube')) # Adicionado

# ----- Sincronização -----
@app.route('/sync')
def sync():
    if 'spotify_token' not in session or 'youtube_token' not in session:
        return 'Por favor, autentique-se no Spotify e YouTube primeiro.'

    spotify_token = session['spotify_token']
    youtube_token = session['youtube_token']

    # Pegando tracks do Spotify (playlist fixa ou editável)
    # ATENÇÃO: 'collection/tracks' não é um ID de playlist válido para a API do Spotify.
    # Você precisará obter um ID de playlist real do usuário ou usar 'me/tracks' para músicas salvas.
    playlist_id = 'collection/tracks' # <--- ISSO PROVAVELMENTE CAUSARÁ ERRO NA API DO SPOTIFY
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

# ----- Sincronização YouTube → Spotify -----
@app.route('/reverse-sync')
def reverse_sync():
    if 'spotify_token' not in session or 'youtube_token' not in session:
        return 'Por favor, autentique-se no Spotify e YouTube primeiro.'

    playlist_id = request.args.get('playlistId')
    if not playlist_id:
        return 'Forneça o ID da playlist do YouTube como parâmetro ?playlistId='

    youtube_token = session['youtube_token']
    spotify_token = session['spotify_token']

    yt_headers = {
        'Authorization': f"Bearer {youtube_token}"  
    }
    yt_url = f"https://www.googleapis.com/youtube/v3/playlistItems"
    yt_params = {
        'part': 'snippet',
        'playlistId': playlist_id,
        'maxResults': 50
    }
    yt_response = requests.get(yt_url, headers=yt_headers, params=yt_params)
    items = yt_response.json().get('items', [])

    track_uris = []
    for item in items:
        title = item['snippet']['title']
        search_url = "https://api.spotify.com/v1/search"
        params = {
            'q': title,
            'type': 'track',
            'limit': 1
        }
        headers_spotify = { 'Authorization': f"Bearer {spotify_token}" }
        search_response = requests.get(search_url, headers=headers_spotify, params=params)
        results = search_response.json().get('tracks', {}).get('items', [])
        if results:
            track_uris.append(results[0]['uri'])

    user_profile = requests.get("https://api.spotify.com/v1/me", headers=headers_spotify)
    user_id = user_profile.json().get('id')
    create_url = f"https://api.spotify.com/v1/users/{user_id}/playlists"
    playlist_data = {
        'name': 'Playlist importada do YouTube',
        'description': 'Gerada pelo Playlist Port',
        'public': False
    }
    create_response = requests.post(create_url, headers=headers_spotify, data=json.dumps(playlist_data))
    playlist_id_spotify = create_response.json().get('id')

    add_url = f"https://api.spotify.com/v1/playlists/{playlist_id_spotify}/tracks"
    requests.post(add_url, headers=headers_spotify, data=json.dumps({ 'uris': track_uris }))

    return f'Playlist criada com {len(track_uris)} músicas no Spotify!'

if __name__ == '__main__':
    app.run(debug=True)
