import os
import requests
import json
from flask import Flask, redirect, request, session, url_for, render_template, jsonify
from dotenv import load_dotenv
from urllib.parse import urlencode
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass

# Carregar variáveis de ambiente
load_dotenv()

# Data Classes para estruturar dados
@dataclass
class SpotifyTrack:
    id: str
    name: str
    artist: str

@dataclass
class SpotifyPlaylist:
    id: str
    name: str
    tracks_total: int

@dataclass
class SpotifyAlbum:
    id: str
    name: str
    artist: str

@dataclass
class SpotifyArtist:
    id: str
    name: str
    genres: List[str]
    followers: int

@dataclass
class AuthConfig:
    client_id: str
    client_secret: str
    redirect_uri: str
    scope: str

@dataclass
class SyncResult:
    success: bool
    playlist_name: str
    videos_added: int
    total_tracks: int
    failures: int
    message: str

# Interface para serviços de autenticação
class AuthenticationService(ABC):
    @abstractmethod
    def get_authorization_url(self) -> str:
        pass
    
    @abstractmethod
    def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def refresh_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        pass

# Interface para serviços de música
class MusicService(ABC):
    @abstractmethod
    def get_playlists(self, token: str) -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod
    def get_playlist_tracks(self, token: str, playlist_id: str) -> List[Dict[str, Any]]:
        pass

# Implementação do serviço Spotify
class SpotifyService(AuthenticationService, MusicService):
    def __init__(self, config: AuthConfig):
        self.config = config
        self.api_base_url = 'https://api.spotify.com/v1'
        self.auth_base_url = 'https://accounts.spotify.com'
    
    def get_authorization_url(self) -> str:
        params = {
            'client_id': self.config.client_id,
            'response_type': 'code',
            'redirect_uri': self.config.redirect_uri,
            'scope': self.config.scope
        }
        return f"{self.auth_base_url}/authorize?{urlencode(params)}"
    
    def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        response = requests.post(f"{self.auth_base_url}/api/token", data={
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': self.config.redirect_uri,
            'client_id': self.config.client_id,
            'client_secret': self.config.client_secret
        })
        return response.json() if response.status_code == 200 else {}
    
    def refresh_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        # Spotify não necessita refresh token no fluxo atual
        return None
    
    def _make_request(self, token: str, endpoint: str, params: Dict = None) -> Optional[Dict]:
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.get(f"{self.api_base_url}/{endpoint}", headers=headers, params=params)
        return response.json() if response.status_code == 200 else None
    
    def _paginate_request(self, token: str, initial_url: str) -> List[Dict]:
        headers = {'Authorization': f'Bearer {token}'}
        items = []
        url = initial_url
        
        while url:
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                break
            data = response.json()
            items.extend(data.get('items', []))
            url = data.get('next')
        
        return items
    
    def get_playlists(self, token: str) -> List[SpotifyPlaylist]:
        url = f'{self.api_base_url}/me/playlists?limit=50'
        playlists = self._paginate_request(token, url)
        
        return [SpotifyPlaylist(
            id=pl['id'],
            name=pl['name'],
            tracks_total=pl['tracks']['total']
        ) for pl in playlists]
    
    def get_playlist_tracks(self, token: str, playlist_id: str) -> List[SpotifyTrack]:
        url = f'{self.api_base_url}/playlists/{playlist_id}/tracks'
        tracks = self._paginate_request(token, url)
        
        return [SpotifyTrack(
            id=item['track']['id'],
            name=item['track']['name'],
            artist=item['track']['artists'][0]['name']
        ) for item in tracks if item.get('track')]
    
    def get_liked_songs(self, token: str) -> List[SpotifyTrack]:
        url = f'{self.api_base_url}/me/tracks?limit=50'
        tracks = self._paginate_request(token, url)
        
        return [SpotifyTrack(
            id=item['track']['id'],
            name=item['track']['name'],
            artist=item['track']['artists'][0]['name']
        ) for item in tracks if item.get('track')]
    
    def get_saved_albums(self, token: str) -> List[SpotifyAlbum]:
        url = f'{self.api_base_url}/me/albums?limit=50'
        albums = self._paginate_request(token, url)
        
        return [SpotifyAlbum(
            id=item['album']['id'],
            name=item['album']['name'],
            artist=item['album']['artists'][0]['name']
        ) for item in albums if item.get('album')]
    
    def get_followed_artists(self, token: str) -> List[SpotifyArtist]:
        url = f'{self.api_base_url}/me/following?type=artist&limit=50'
        headers = {'Authorization': f'Bearer {token}'}
        artists = []
        
        while url:
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                break
            data = response.json()
            data_artists = data.get('artists', {})
            artists.extend(data_artists.get('items', []))
            url = data_artists.get('next')
        
        return [SpotifyArtist(
            id=artist.get('id'),
            name=artist.get('name'),
            genres=artist.get('genres', []),
            followers=artist.get('followers', {}).get('total', 0)
        ) for artist in artists if artist]
    
    def get_playlist_info(self, token: str, playlist_id: str) -> Optional[Dict]:
        return self._make_request(token, f'playlists/{playlist_id}')

# Implementação do serviço YouTube
class YouTubeService(AuthenticationService):
    def __init__(self, config: AuthConfig, api_key: str):
        self.config = config
        self.api_key = api_key
        self.api_base_url = 'https://www.googleapis.com/youtube/v3'
        self.auth_base_url = 'https://accounts.google.com/o/oauth2'
    
    def get_authorization_url(self) -> str:
        params = {
            'client_id': self.config.client_id,
            'response_type': 'code',
            'redirect_uri': self.config.redirect_uri,
            'scope': self.config.scope,
            'access_type': 'offline',
            'prompt': 'consent'
        }
        return f"{self.auth_base_url}/auth?{urlencode(params)}"
    
    def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        response = requests.post('https://oauth2.googleapis.com/token', data={
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': self.config.redirect_uri,
            'client_id': self.config.client_id,
            'client_secret': self.config.client_secret
        })
        return response.json() if response.status_code == 200 else {}
    
    def refresh_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        response = requests.post('https://oauth2.googleapis.com/token', data={
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'client_id': self.config.client_id,
            'client_secret': self.config.client_secret
        })
        return response.json() if response.status_code == 200 else None
    
    def search_video(self, query: str) -> Optional[str]:
        params = {
            'part': 'snippet',
            'q': query,
            'type': 'video',
            'maxResults': 1,
            'key': self.api_key
        }
        response = requests.get(f"{self.api_base_url}/search", params=params)
        
        if response.status_code == 200:
            results = response.json().get('items', [])
            if results and 'videoId' in results[0]['id']:
                return results[0]['id']['videoId']
        return None
    
    def create_playlist(self, token: str, name: str, description: str = '') -> Optional[str]:
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        data = {
            'snippet': {
                'title': name,
                'description': description
            },
            'status': {
                'privacyStatus': 'private'
            }
        }
        response = requests.post(
            f'{self.api_base_url}/playlists?part=snippet,status',
            headers=headers,
            json=data
        )
        return response.json().get('id') if response.status_code == 200 else None
    
    def add_video_to_playlist(self, token: str, playlist_id: str, video_id: str) -> bool:
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        data = {
            'snippet': {
                'playlistId': playlist_id,
                'resourceId': {
                    'kind': 'youtube#video',
                    'videoId': video_id
                }
            }
        }
        response = requests.post(
            f'{self.api_base_url}/playlistItems?part=snippet',
            headers=headers,
            json=data
        )
        return response.status_code == 200

# Serviço de sincronização
class SyncService:
    def __init__(self, spotify_service: SpotifyService, youtube_service: YouTubeService):
        self.spotify = spotify_service
        self.youtube = youtube_service
    
    def sync_playlist_to_youtube(self, spotify_token: str, youtube_token: str, playlist_id: str) -> SyncResult:
        # 1. Obter informações da playlist
        playlist_info = self.spotify.get_playlist_info(spotify_token, playlist_id)
        if not playlist_info:
            return SyncResult(False, '', 0, 0, 0, 'Erro ao obter informações da playlist')
        
        playlist_name = playlist_info.get('name', 'Playlist importada do Spotify')
        
        # 2. Obter tracks da playlist
        tracks = self.spotify.get_playlist_tracks(spotify_token, playlist_id)
        if not tracks:
            return SyncResult(False, playlist_name, 0, 0, 0, 'Nenhuma música encontrada na playlist')
        
        # 3. Criar playlist no YouTube
        yt_playlist_id = self.youtube.create_playlist(
            youtube_token, 
            playlist_name, 
            'Gerada automaticamente pelo PlaylistPort.'
        )
        if not yt_playlist_id:
            return SyncResult(False, playlist_name, 0, len(tracks), 0, 'Erro ao criar playlist no YouTube')
        
        # 4. Adicionar vídeos
        videos_added = 0
        failures = 0
        
        for track in tracks:
            query = f"{track.name} {track.artist}"
            video_id = self.youtube.search_video(query)
            
            if video_id:
                if self.youtube.add_video_to_playlist(youtube_token, yt_playlist_id, video_id):
                    videos_added += 1
                else:
                    failures += 1
            else:
                failures += 1
        
        message = f'Playlist "{playlist_name}" criada no YouTube com {videos_added} de {len(tracks)} vídeos! ({failures} falhas)'
        return SyncResult(True, playlist_name, videos_added, len(tracks), failures, message)

# Gerenciador de sessão
class SessionManager:
    @staticmethod
    def get_spotify_token() -> Optional[str]:
        return session.get('spotify_token')
    
    @staticmethod
    def set_spotify_token(token: str):
        session['spotify_token'] = token
    
    @staticmethod
    def get_youtube_tokens() -> Dict[str, Optional[str]]:
        return {
            'access_token': session.get('youtube_token'),
            'refresh_token': session.get('youtube_refresh_token')
        }
    
    @staticmethod
    def set_youtube_tokens(access_token: str, refresh_token: str = None):
        session['youtube_token'] = access_token
        if refresh_token:
            session['youtube_refresh_token'] = refresh_token
    
    @staticmethod
    def is_authenticated() -> Dict[str, bool]:
        return {
            'spotify': 'spotify_token' in session,
            'youtube': 'youtube_token' in session
        }

# Configuração da aplicação
def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = os.urandom(24)
    
    # Configurações dos serviços
    spotify_config = AuthConfig(
        client_id=os.getenv('SPOTIFY_CLIENT_ID'),
        client_secret=os.getenv('SPOTIFY_CLIENT_SECRET'),
        redirect_uri=os.getenv('SPOTIFY_REDIRECT_URI'),
        scope='playlist-read-private playlist-modify-private user-library-read user-follow-read'
    )
    
    youtube_config = AuthConfig(
        client_id=os.getenv('YOUTUBE_CLIENT_ID'),
        client_secret=os.getenv('YOUTUBE_CLIENT_SECRET'),
        redirect_uri=os.getenv('YOUTUBE_REDIRECT_URI'),
        scope='https://www.googleapis.com/auth/youtube'
    )
    
    # Inicialização dos serviços
    spotify_service = SpotifyService(spotify_config)
    youtube_service = YouTubeService(youtube_config, os.getenv('YOUTUBE_API_KEY'))
    sync_service = SyncService(spotify_service, youtube_service)
    
    # Rotas
    @app.route('/')
    def index():
        return render_template('index.html')
    
    # Autenticação Spotify
    @app.route('/login/spotify')
    def login_spotify():
        return redirect(spotify_service.get_authorization_url())
    
    @app.route('/callback/spotify')
    def callback_spotify():
        code = request.args.get('code')
        if not code:
            return redirect(url_for('index', auth_status='error', service='spotify'))
        
        token_data = spotify_service.exchange_code_for_token(code)
        if token_data.get('access_token'):
            SessionManager.set_spotify_token(token_data['access_token'])
            return redirect(url_for('index', auth_status='success', service='spotify'))
        return redirect(url_for('index', auth_status='error', service='spotify'))
    
    # Autenticação YouTube
    @app.route('/login/youtube')
    def login_youtube():
        return redirect(youtube_service.get_authorization_url())
    
    @app.route('/callback/youtube')
    def callback_youtube():
        code = request.args.get('code')
        if not code:
            return redirect(url_for('index', auth_status='error', service='youtube'))
        
        token_data = youtube_service.exchange_code_for_token(code)
        if token_data.get('access_token'):
            SessionManager.set_youtube_tokens(
                token_data['access_token'],
                token_data.get('refresh_token')
            )
            return redirect(url_for('index', auth_status='success', service='youtube'))
        return redirect(url_for('index', auth_status='error', service='youtube'))
    
    # APIs do Spotify
    @app.route('/spotify-playlists')
    def spotify_playlists():
        token = SessionManager.get_spotify_token()
        if not token:
            return jsonify({'error': 'Usuário não autenticado no Spotify'}), 401
        
        playlists = spotify_service.get_playlists(token)
        return jsonify({'playlists': [
            {'id': pl.id, 'name': pl.name, 'tracks_total': pl.tracks_total}
            for pl in playlists
        ]})
    
    @app.route('/spotify-liked-songs')
    def spotify_liked_songs():
        token = SessionManager.get_spotify_token()
        if not token:
            return jsonify({'error': 'Usuário não autenticado no Spotify'}), 401
        
        songs = spotify_service.get_liked_songs(token)
        return jsonify({'liked_songs': [
            {'id': song.id, 'name': song.name, 'artist': song.artist}
            for song in songs
        ]})
    
    @app.route('/spotify-albums')
    def spotify_albums():
        token = SessionManager.get_spotify_token()
        if not token:
            return jsonify({'error': 'Usuário não autenticado no Spotify'}), 401
        
        albums = spotify_service.get_saved_albums(token)
        return jsonify({'albums': [
            {'id': album.id, 'name': album.name, 'artist': album.artist}
            for album in albums
        ]})
    
    @app.route('/spotify-artists')
    def spotify_artists():
        token = SessionManager.get_spotify_token()
        if not token:
            return jsonify({'error': 'Usuário não autenticado no Spotify'}), 401
        
        artists = spotify_service.get_followed_artists(token)
        return jsonify({'artists': [
            {
                'id': artist.id,
                'name': artist.name,
                'genres': artist.genres,
                'followers': artist.followers
            }
            for artist in artists
        ]})
    
    # Sincronização
    @app.route('/sync')
    def sync():
        auth_status = SessionManager.is_authenticated()
        if not all(auth_status.values()):
            return render_template('not_in_session.html', 
                                 message='Por favor, autentique-se no Spotify e YouTube primeiro.')
        
        playlist_id = request.args.get('playlist_id') or request.args.get('id')
        sync_type = request.args.get('type', 'playlist')
        
        if not playlist_id:
            return render_template('sync_result.html', 
                                 message='Forneça o ID do item para sincronizar')
        
        # Por enquanto, apenas playlists são suportadas
        if sync_type != 'playlist':
            return render_template('sync_result.html', 
                                 message='Apenas sincronização de playlists é suportada no momento')
        
        spotify_token = SessionManager.get_spotify_token()
        youtube_token = SessionManager.get_youtube_tokens()['access_token']
        
        result = sync_service.sync_playlist_to_youtube(spotify_token, youtube_token, playlist_id)
        return render_template('sync_result.html', message=result.message)
    
    return app

# Execução da aplicação
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)