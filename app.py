import os
import requests
import json
from flask import Flask, redirect, request, session, url_for, render_template
from dotenv import load_dotenv
from urllib.parse import urlencode

# Carregar variáveis de ambiente do .env
load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Configurações Spotify
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
SPOTIFY_REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI')
SPOTIFY_SCOPE = 'playlist-read-private playlist-modify-private'
SPOTIFY_API_BASE_URL = 'https://api.spotify.com/v1'

# Configurações YouTube
YOUTUBE_CLIENT_ID = os.getenv('YOUTUBE_CLIENT_ID')
YOUTUBE_CLIENT_SECRET = os.getenv('YOUTUBE_CLIENT_SECRET')
YOUTUBE_REDIRECT_URI = os.getenv('YOUTUBE_REDIRECT_URI')
YOUTUBE_SCOPE = 'https://www.googleapis.com/auth/youtube'
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
YOUTUBE_API_BASE_URL = 'https://www.googleapis.com/youtube/v3'

# Rotas principais
@app.route('/')
def index():
    return render_template('index.html')

# Autenticação Spotify
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
        return redirect(url_for('index', auth_status='success', service='spotify'))
    else:
        return redirect(url_for('index', auth_status='error', service='spotify'))

# Autenticação YouTube
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
        tokens_data = response.json()

        session['youtube_token'] = tokens_data.get('access_token')
        session['youtube_refresh_token'] = tokens_data.get('refresh_token')
        
        return redirect(url_for('index', auth_status='success', service='youtube'))
    else:
        return redirect(url_for('index', auth_status='error', service='youtube'))
    
    # Função para renovar o token de acesso do YouTube
def refresh_youtube_token():
    token_url = "https://oauth2.googleapis.com/token"
    refresh_token = session.get('youtube_refresh_token')

    # Verifica se o refresh token existe
    if not refresh_token:
        print("Refresh token não encontrado na sessão.")
        return False
    
    response = requests.post(token_url, data={
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': YOUTUBE_CLIENT_ID,
        'client_secret': YOUTUBE_CLIENT_SECRET
    })

    if response.status_code == 200:
        new_token_data = response.json()
        session['youtube_token'] = new_token_data.get('access_token')
        print("Token do YouTube renovado com sucesso.")
        return True
    else:
        print(f"Erro ao renovar token: {response.status_code} - {response.text}")
        return False

# Obter playlists do Spotify (JSON)
@app.route('/spotify-playlists')
def spotify_playlists():
    if 'spotify_token' not in session:
        return {'error': 'Usuário não autenticado no Spotify'}, 401

    spotify_token = session['spotify_token']
    headers = {'Authorization': f'Bearer {spotify_token}'}

    playlists = []
    url = f'{SPOTIFY_API_BASE_URL}/me/playlists'

    while url:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return {'error': f"Erro ao obter playlists: {response.status_code}"}, 400

        data = response.json()
        playlists.extend(data.get('items', []))
        url = data.get('next')  # Paginação

    simple_playlists = [{
        'id': pl['id'],
        'name': pl['name'],
        'tracks_total': pl['tracks']['total']
    } for pl in playlists]

    return {'playlists': simple_playlists}

# Sincronização Spotify -> YouTube
@app.route('/sync')
def sync():
    if 'spotify_token' not in session or 'youtube_token' not in session:
        message= f'Por favor, autentique-se no Spotify e YouTube primeiro.'
        return render_template('not_in_session.html', message=message)

    spotify_token = session['spotify_token']
    youtube_token = session['youtube_token']

    playlist_id = request.args.get('playlist_id')
    if not playlist_id:
        return 'Forneça o ID da playlist do Spotify via parâmetro ?playlist_id='

    headers_spotify = {'Authorization': f"Bearer {spotify_token}"}
    
    # 1. Obter dados da playlist para pegar o nome da playlist Spotify
    playlist_info_url = f"{SPOTIFY_API_BASE_URL}/playlists/{playlist_id}"
    playlist_response = requests.get(playlist_info_url, headers=headers_spotify)
    if playlist_response.status_code != 200:
        return f"Erro ao obter informações da playlist Spotify: {playlist_response.status_code}"
    playlist_data = playlist_response.json()
    playlist_name = playlist_data.get('name', 'Playlist importada do Spotify')

    # 2. Obter faixas da playlist com paginação
    tracks_url = f"{SPOTIFY_API_BASE_URL}/playlists/{playlist_id}/tracks"
    items = []
    while tracks_url:
        response = requests.get(tracks_url, headers=headers_spotify)
        if response.status_code != 200:
            return f"Erro ao obter faixas da playlist Spotify: {response.status_code}"
        data = response.json()
        items.extend(data.get('items', []))
        tracks_url = data.get('next')

    print(f"Número de faixas obtidas do Spotify: {len(items)}")

    # 3. Criar playlist no YouTube com o mesmo nome
    yt_headers = {
        'Authorization': f"Bearer {youtube_token}",
        'Content-Type': 'application/json'
    }
    playlist_data_yt = {
        'snippet': {
            'title': playlist_name,
            'description': 'Gerada automaticamente pelo PlaylistPort.'
        },
        'status': {
            'privacyStatus': 'private'
        }
    }
    yt_create = requests.post(
        f'{YOUTUBE_API_BASE_URL}/playlists?part=snippet,status',
        headers=yt_headers,
        data=json.dumps(playlist_data_yt)
    )

     # Lógica de renovação do token na criação da playlist
    if yt_create.status_code == 401:
        if refresh_youtube_token():
            yt_headers['Authorization'] = f"Bearer {session.get('youtube_token')}"
            yt_create = requests.post(
                f'{YOUTUBE_API_BASE_URL}/playlists?part=snippet,status',
                headers=yt_headers,
                data=json.dumps(playlist_data_yt)
            )
    if yt_create.status_code != 200:
        return f"Erro ao criar playlist no YouTube: {yt_create.status_code} - {yt_create.text}"
    playlist_id_yt = yt_create.json().get('id')

    # 4. Buscar vídeos no YouTube para cada música e adicionar à playlist criada
    videos_adicionados = 0
    falhas_adicao = 0

    for item in items:
        track = item['track']
        query = f"{track['name']} {track['artists'][0]['name']}"
        yt_search_url = f"{YOUTUBE_API_BASE_URL}/search"
        yt_params = {
            'part': 'snippet',
            'q': query,
            'type': 'video',
            'maxResults': 1,
            'key': YOUTUBE_API_KEY
        }
        yt_response = requests.get(yt_search_url, params=yt_params)
        
        video_id = None
        if yt_response.status_code == 200:
            results = yt_response.json().get('items', [])
            if results and 'videoId' in results[0]['id']:
                video_id = results[0]['id']['videoId']

        print(f"Busca para '{query}': video_id = {video_id}")
            
        if not video_id:
            print(f"Vídeo não encontrado para a query: {query}")
            continue

        insert_data = {
            'snippet': {
                'playlistId': playlist_id_yt,
                'resourceId': {
                    'kind': 'youtube#video',
                    'videoId': video_id
                }
            }
        }
        
        add_response = requests.post(
            f'{YOUTUBE_API_BASE_URL}/playlistItems?part=snippet',
            headers=yt_headers,
            json=insert_data
        )

        if add_response.status_code == 401:
            if refresh_youtube_token():
                # Atualiza o cabeçalho com o novo token
                yt_headers['Authorization'] = f"Bearer {session.get('youtube_token')}"
                # Tenta novamente
                add_response = requests.post(
                    f'{YOUTUBE_API_BASE_URL}/playlistItems?part=snippet',
                    headers=yt_headers,
                    json=insert_data
                )

        if add_response.status_code != 401:
            videos_adicionados += 1
            print(f"Vídeo {video_id} adicionado com sucesso.")
        else:
            falhas_adicao += 1
            print(f"Erro ao adicionar vídeo {video_id}: {add_response.status_code} - {add_response.text}")

    message = f'Playlist "{playlist_name}" criada no YouTube com {videos_adicionados} de {len(items)} vídeos! ({falhas_adicao} falhas)'
    return render_template('sync_result.html', message=message)

# Sincronização YouTube -> Spotify --EM DESENVOLVIMENTO--
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
    yt_url = f"{YOUTUBE_API_BASE_URL}/playlistItems"
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
        search_url = f"{SPOTIFY_API_BASE_URL}/search"
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

    user_profile = requests.get(f"{SPOTIFY_API_BASE_URL}/me", headers=headers_spotify)
    user_id = user_profile.json().get('id')
    create_url = f"{SPOTIFY_API_BASE_URL}/users/{user_id}/playlists"
    playlist_data = {
        'name': 'Playlist importada do YouTube',
        'description': 'Gerada pelo PlaylistPort.',
        'public': False
    }
    create_response = requests.post(create_url, headers=headers_spotify, data=json.dumps(playlist_data))
    playlist_id_spotify = create_response.json().get('id')

    add_url = f"{SPOTIFY_API_BASE_URL}/playlists/{playlist_id_spotify}/tracks"
    requests.post(add_url, headers=headers_spotify, data=json.dumps({ 'uris': track_uris }))

    return f'Playlist criada com {len(track_uris)} músicas no Spotify!'

if __name__ == '__main__':
    app.run(debug=True)