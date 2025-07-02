from flask import Flask, redirect, request, session, url_for
import requests
import os
import json

app = Flask(__name__)
app.secret_key = 'uma-chave-secreta-aqui'

# ===== CONFIGURAÇÕES DE API ===== #
SPOTIFY_CLIENT_ID = 'SUA_SPOTIFY_CLIENT_ID'
SPOTIFY_CLIENT_SECRET = 'SUA_SPOTIFY_CLIENT_SECRET'
SPOTIFY_REDIRECT_URI = 'http://localhost:5000/callback/spotify'

YOUTUBE_CLIENT_ID = 'SUA_YOUTUBE_CLIENT_ID'
YOUTUBE_CLIENT_SECRET = 'SUA_YOUTUBE_CLIENT_SECRET'
YOUTUBE_REDIRECT_URI = 'http://localhost:5000/callback/youtube'

# ================================ #

@app.route('/')
def home():
    return '''
        <h1>StreamSync</h1>
        <a href="/login/spotify">Login com Spotify</a><br>
        <a href="/login/youtube">Login com YouTube</a>
    '''

# === LOGIN SPOTIFY === #
@app.route('/login/spotify')
def login_spotify():
    scope = 'playlist-read-private user-library-read'
    auth_url = f"https://accounts.spotify.com/authorize?response_type=code&client_id={SPOTIFY_CLIENT_ID}&scope={scope}&redirect_uri={SPOTIFY_REDIRECT_URI}"
    return redirect(auth_url)

@app.route('/callback/spotify')
def callback_spotify():
    code = request.args.get('code')
    token_url = 'https://accounts.spotify.com/api/token'
    response = requests.post(token_url, data={
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': SPOTIFY_REDIRECT_URI,
        'client_id': SPOTIFY_CLIENT_ID,
        'client_secret': SPOTIFY_CLIENT_SECRET
    })

    tokens = response.json()
    session['spotify_token'] = tokens
    return '<h2>Spotify autenticado com sucesso!</h2><a href="/">Voltar</a>'

# === LOGIN YOUTUBE === #
@app.route('/login/youtube')
def login_youtube():
    scope = 'https://www.googleapis.com/auth/youtube.force-ssl'
    auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={YOUTUBE_CLIENT_ID}&response_type=code"
        f"&redirect_uri={YOUTUBE_REDIRECT_URI}"
        f"&scope={scope}&access_type=offline&prompt=consent"
    )
    return redirect(auth_url)

@app.route('/callback/youtube')
def callback_youtube():
    code = request.args.get('code')
    token_url = 'https://oauth2.googleapis.com/token'
    response = requests.post(token_url, data={
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': YOUTUBE_REDIRECT_URI,
        'client_id': YOUTUBE_CLIENT_ID,
        'client_secret': YOUTUBE_CLIENT_SECRET
    })

    tokens = response.json()
    session['youtube_token'] = tokens
    return '<h2>YouTube autenticado com sucesso!</h2><a href="/">Voltar</a>'

if __name__ == '__main__':
    app.run(debug=True)

    # === ROTA PARA LISTAR PLAYLISTS DO USUÁRIO === #
@app.route('/spotify/playlists')
def spotify_playlists():
    if 'spotify_token' not in session:
        return redirect('/login/spotify')

    access_token = session['spotify_token']['access_token']
    headers = {
        'Authorization': f'Bearer {access_token}'
    }

    response = requests.get('https://api.spotify.com/v1/me/playlists', headers=headers)

    if response.status_code != 200:
        return f"<p>Erro ao acessar Spotify API: {response.text}</p>"

    playlists = response.json().get('items', [])

    html = '<h2>Suas playlists no Spotify:</h2><ul>'
    for p in playlists:
        html += f"<li><strong>{p['name']}</strong> ({p['tracks']['total']} músicas)</li>"
    html += '</ul><a href="/">Voltar</a>'

    return html

@app.route('/spotify/playlist/<playlist_id>')
def spotify_playlist_tracks(playlist_id):
    if 'spotify_token' not in session:
        return redirect('/login/spotify')

    access_token = session['spotify_token']['access_token']
    headers = {
        'Authorization': f'Bearer {access_token}'
    }

    tracks_url = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks'
    response = requests.get(tracks_url, headers=headers)

    if response.status_code != 200:
        return f"<p>Erro ao acessar músicas da playlist: {response.text}</p>"

    tracks_data = response.json()
    html = '<h2>Músicas da Playlist:</h2><ul>'

    for item in tracks_data['items']:
        track = item['track']
        name = track['name']
        artists = ', '.join([a['name'] for a in track['artists']])
        html += f"<li>{name} - {artists}</li>"

    html += '</ul><a href="/spotify/playlists">Voltar</a>'
    return html

@app.route('/spotify/playlist/<playlist_id>/youtube')
def spotify_to_youtube(playlist_id):
    if 'spotify_token' not in session or 'youtube_token' not in session:
        return '<p>Você precisa estar logado no Spotify e no YouTube.</p><a href="/">Voltar</a>'

    spotify_token = session['spotify_token']['access_token']
    youtube_token = session['youtube_token']['access_token']

    # Obter faixas da playlist do Spotify
    headers_spotify = {'Authorization': f'Bearer {spotify_token}'}
    response = requests.get(
        f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks',
        headers=headers_spotify
    )

    if response.status_code != 200:
        return f"<p>Erro ao acessar músicas da playlist: {response.text}</p>"

    tracks_data = response.json()

    html = '<h2>Resultados da busca no YouTube:</h2><ul>'
    for item in tracks_data['items']:
        track = item['track']
        if not track: continue

        name = track['name']
        artists = ', '.join([a['name'] for a in track['artists']])
        query = f"{name} {artists}"

        # Buscar no YouTube
        headers_youtube = {'Authorization': f'Bearer {youtube_token}'}
        params = {
            'part': 'snippet',
            'q': query,
            'maxResults': 1,
            'type': 'video'
        }

        yt_response = requests.get('https://www.googleapis.com/youtube/v3/search',
                                   headers=headers_youtube, params=params)

        if yt_response.status_code != 200:
            html += f"<li>{query} - <em>Erro na busca</em></li>"
            continue

        yt_data = yt_response.json()
        if yt_data['items']:
            video_id = yt_data['items'][0]['id']['videoId']
            video_title = yt_data['items'][0]['snippet']['title']
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            html += f"<li>{query} → <a href='{video_url}' target='_blank'>{video_title}</a></li>"
        else:
            html += f"<li>{query} - <em>Não encontrado</em></li>"

    html += '</ul><a href="/">Voltar</a>'
    return html

def create_youtube_playlist(youtube_token, title, description="Importado do Spotify"):
    headers = {
        'Authorization': f'Bearer {youtube_token}',
        'Content-Type': 'application/json'
    }

    body = {
        'snippet': {
            'title': title,
            'description': description
        },
        'status': {
            'privacyStatus': 'private'  # pode ser 'public' ou 'unlisted'
        }
    }

    response = requests.post(
        'https://www.googleapis.com/youtube/v3/playlists?part=snippet,status',
        headers=headers,
        data=json.dumps(body)
    )

    if response.status_code == 200:
        playlist_id = response.json()['id']
        return playlist_id
    else:
        print(response.text)
        return None

        def add_video_to_playlist(youtube_token, playlist_id, video_id):
    headers = {
        'Authorization': f'Bearer {youtube_token}',
        'Content-Type': 'application/json'
    }

    body = {
        'snippet': {
            'playlistId': playlist_id,
            'resourceId': {
                'kind': 'youtube#video',
                'videoId': video_id
            }
        }
    }

    response = requests.post(
        'https://www.googleapis.com/youtube/v3/playlistItems?part=snippet',
        headers=headers,
        data=json.dumps(body)
    )

    return response.status_code == 200

@app.route('/spotify/playlist/<playlist_id>/sync')
def sync_playlist_to_youtube(playlist_id):
    if 'spotify_token' not in session or 'youtube_token' not in session:
        return '<p>Você precisa estar logado no Spotify e no YouTube.</p><a href="/">Voltar</a>'

    spotify_token = session['spotify_token']['access_token']
    youtube_token = session['youtube_token']['access_token']

    # Obter detalhes da playlist original
    headers_spotify = {'Authorization': f'Bearer {spotify_token}'}
    playlist_info = requests.get(f'https://api.spotify.com/v1/playlists/{playlist_id}', headers=headers_spotify)
    playlist_data = playlist_info.json()
    playlist_name = playlist_data['name']

    # Criar a nova playlist no YouTube
    new_playlist_id = create_youtube_playlist(youtube_token, playlist_name)
    if not new_playlist_id:
        return '<p>Erro ao criar playlist no YouTube.</p>'

    # Obter faixas do Spotify
    tracks_resp = requests.get(
        f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks',
        headers=headers_spotify
    )
    tracks = tracks_resp.json()['items']

    html = f"<h2>Playlist '{playlist_name}' criada no YouTube</h2><ul>"

    for item in tracks:
        track = item['track']
        if not track: continue

        name = track['name']
        artists = ', '.join([a['name'] for a in track['artists']])
        query = f"{name} {artists}"

        # Buscar no YouTube
        headers_youtube = {'Authorization': f'Bearer {youtube_token}'}
        search = requests.get('https://www.googleapis.com/youtube/v3/search', headers=headers_youtube, params={
            'part': 'snippet',
            'q': query,
            'maxResults': 1,
            'type': 'video'
        })

        yt_data = search.json()
        if yt_data.get('items'):
            video_id = yt_data['items'][0]['id']['videoId']
            video_title = yt_data['items'][0]['snippet']['title']
            added = add_video_to_playlist(youtube_token, new_playlist_id, video_id)
            status = '✅' if added else '❌ erro ao adicionar'
            html += f"<li>{query} → {video_title} {status}</li>"
        else:
            html += f"<li>{query} - ❌ não encontrado</li>"

    html += '</ul><a href="/">Voltar</a>'
    return html