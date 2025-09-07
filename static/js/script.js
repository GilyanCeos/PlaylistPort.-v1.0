// static/js/script.js

class SpotifyYouTubeSync {
    constructor() {
        this.elements = this.initializeElements();
        this.accordionHandlers = new Map(); // Evita múltiplos event listeners
        this.init();
    }

    initializeElements() {
        return {
            spotifyBtn: document.querySelector('.btn-spotify'),
            youtubeBtn: document.querySelector('.btn-youtube'),
            syncNowBtn: document.querySelector('.btn-sync-now'),
            feedbackMessageDiv: document.getElementById('feedback-message'),
            playlistsContainer: document.getElementById('playlists-container'),
            likedSongsContainer: document.getElementById('liked-songs-container'),
            albumsContainer: document.getElementById('albums-container'),
            artistsContainer: document.getElementById('artists-container')
        };
    }

    init() {
        this.bindEvents();
        this.initializeAllAccordions();
        this.handleURLParams();
    }

    bindEvents() {
        const { spotifyBtn, youtubeBtn, syncNowBtn } = this.elements;

        if (spotifyBtn) {
            spotifyBtn.addEventListener('click', () => this.handleSpotifyAuth());
        }

        if (youtubeBtn) {
            youtubeBtn.addEventListener('click', () => this.handleYouTubeAuth());
        }

        if (syncNowBtn) {
            syncNowBtn.addEventListener('click', () => this.handleSync());
        }
    }

    showFeedbackMessage(message, type) {
        const { feedbackMessageDiv } = this.elements;
        if (!feedbackMessageDiv) return;

        feedbackMessageDiv.textContent = message;
        feedbackMessageDiv.className = `feedback-message ${type}`;
        feedbackMessageDiv.classList.remove('hidden');
        
        setTimeout(() => {
            feedbackMessageDiv.classList.add('hidden');
            feedbackMessageDiv.textContent = '';
        }, 5000);
    }

    handleSpotifyAuth() {
        this.showFeedbackMessage('Redirecionando para o Spotify...', 'success');
        window.location.href = '/login/spotify';
    }

    handleYouTubeAuth() {
        this.showFeedbackMessage('Redirecionando para o YouTube...', 'success');
        window.location.href = '/login/youtube';
    }

    handleSync() {
        // Verifica se há algum item selecionado em qualquer seção
        const selectedBtn = document.querySelector('.playlist-btn.selected, .song-btn.selected, .album-btn.selected, .artist-btn.selected');
        if (!selectedBtn) {
            this.showFeedbackMessage('Por favor, selecione um item para sincronizar.', 'error');
            return;
        }
        
        // Determina o tipo e ID baseado na classe do botão
        let syncData = {};
        if (selectedBtn.classList.contains('playlist-btn')) {
            syncData.type = 'playlist';
            syncData.id = selectedBtn.dataset.playlistId;
        } else if (selectedBtn.classList.contains('song-btn')) {
            syncData.type = 'liked_songs';
            syncData.id = selectedBtn.dataset.trackId;
        } else if (selectedBtn.classList.contains('album-btn')) {
            syncData.type = 'album';
            syncData.id = selectedBtn.dataset.albumId;
        } else if (selectedBtn.classList.contains('artist-btn')) {
            syncData.type = 'artist';
            syncData.id = selectedBtn.dataset.artistId;
        }
        
        this.showFeedbackMessage('Iniciando sincronização...', 'success');
        window.location.href = `/sync?type=${syncData.type}&id=${syncData.id}`;
    }

    // Método genérico para fazer requisições
    async fetchData(endpoint, errorMessage) {
        try {
            const response = await fetch(endpoint);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error(`Erro ao buscar ${endpoint}:`, error);
            throw new Error(errorMessage);
        }
    }

    // Método genérico para renderizar botões
    renderButtons(container, items, buttonClass, getButtonText, getDatasetKey) {
        if (!container) return;

        container.innerHTML = '';
        
        if (!items || items.length === 0) {
            container.innerHTML = '<p style="text-align: center; padding: 20px; color: #888;">Nenhum item encontrado</p>';
            return;
        }
        
        items.forEach(item => {
            const btn = document.createElement('button');
            btn.textContent = getButtonText(item);
            btn.className = `btn ${buttonClass}`;
            btn.dataset[getDatasetKey()] = item.id;

            btn.addEventListener('click', () => {
                // Remove seleção de TODOS os tipos de botões
                document.querySelectorAll('.playlist-btn, .song-btn, .album-btn, .artist-btn')
                    .forEach(b => b.classList.remove('selected'));
                btn.classList.add('selected');
            });

            container.appendChild(btn);
        });
    }

    // Método genérico para carregar dados do Spotify
    async loadSpotifyData(endpoint, containerId, buttonClass, getButtonText, getDatasetKey, emptyMessage) {
        const container = document.getElementById(containerId);
        if (!container) return;

        container.innerHTML = '<p style="text-align: center; padding: 20px;">Carregando...</p>';

        try {
            const data = await this.fetchData(endpoint, `Erro ao carregar dados de ${endpoint}`);
            
            if (data.error) {
                container.innerHTML = `<p style="text-align: center; padding: 20px; color: #ff6b6b;">${data.error}</p>`;
                return;
            }

            // Determina a propriedade dos dados baseada no endpoint
            const dataKey = this.getDataKey(endpoint);
            const items = data[dataKey] || [];
            
            if (items.length === 0) {
                container.innerHTML = `<p style="text-align: center; padding: 20px; color: #888;">${emptyMessage}</p>`;
                return;
            }

            this.renderButtons(container, items, buttonClass, getButtonText, getDatasetKey);

        } catch (error) {
            container.innerHTML = `<p style="text-align: center; padding: 20px; color: #ff6b6b;">Erro ao carregar dados.</p>`;
        }
    }

    getDataKey(endpoint) {
        const keyMap = {
            '/spotify-playlists': 'playlists',
            '/spotify-liked-songs': 'liked_songs',
            '/spotify-albums': 'albums',
            '/spotify-artists': 'artists'
        };
        return keyMap[endpoint] || 'data';
    }

    // Métodos específicos para cada tipo de conteúdo
    async loadSpotifyPlaylists() {
        await this.loadSpotifyData(
            '/spotify-playlists',
            'playlists-container',
            'playlist-btn',
            (playlist) => `${playlist.name} (${playlist.tracks_total || 0} músicas)`,
            () => 'playlistId',
            'Nenhuma playlist encontrada.'
        );
    }

    async loadSpotifyLikedSongs() {
        await this.loadSpotifyData(
            '/spotify-liked-songs',
            'liked-songs-container',
            'song-btn',
            (song) => `${song.name} - ${song.artist}`,
            () => 'trackId',
            'Nenhuma música curtida encontrada.'
        );
    }

    async loadSavedAlbums() {
        await this.loadSpotifyData(
            '/spotify-albums',
            'albums-container',
            'album-btn',
            (album) => `${album.name} - ${album.artist}`,
            () => 'albumId',
            'Nenhum álbum salvo encontrado.'
        );
    }

    async loadFollowedArtists() {
        await this.loadSpotifyData(
            '/spotify-artists',
            'artists-container',
            'artist-btn',
            (artist) => `${artist.name}${artist.followers ? ` (${artist.followers} seguidores)` : ''}`,
            () => 'artistId',
            'Nenhum artista seguido encontrado.'
        );
    }

    // Gerenciamento universal do accordion
    initializeAllAccordions() {
        const accordionHeaders = document.querySelectorAll('.accordion-header');
        
        accordionHeaders.forEach(header => {
            // Evita adicionar múltiplos listeners ao mesmo elemento
            if (!this.accordionHandlers.has(header)) {
                const toggleFunction = () => this.toggleSpecificAccordion(header);
                header.addEventListener('click', toggleFunction);
                this.accordionHandlers.set(header, toggleFunction);
            }
        });
    }

    toggleSpecificAccordion(headerElement) {
        const accordionContainer = headerElement.closest('.playlist-accordion');
        if (accordionContainer) {
            accordionContainer.classList.toggle('open');
            
            // Adiciona animação suave ao ícone (se houver)
            const icon = headerElement.querySelector('.accordion-icon');
            if (icon) {
                icon.style.transform = accordionContainer.classList.contains('open') 
                    ? 'rotate(180deg)' 
                    : 'rotate(0deg)';
            }
        }
    }

    // Carrega todos os dados do Spotify
    async loadAllSpotifyData() {
        const loadingTasks = [
            this.loadSpotifyPlaylists(),
            this.loadSpotifyLikedSongs(),
            this.loadSavedAlbums(),
            this.loadFollowedArtists()
        ];

        try {
            await Promise.allSettled(loadingTasks);
        } catch (error) {
            console.error('Erro ao carregar dados do Spotify:', error);
            this.showFeedbackMessage('Erro ao carregar dados do Spotify', 'error');
        }
    }

    updateButtonState(button, service, isConnected) {
        if (!button) return;

        if (isConnected) {
            const serviceName = service.charAt(0).toUpperCase() + service.slice(1);
            button.textContent = `${serviceName} Conectado`;
            button.classList.add('connected');
            button.disabled = true;
        }
    }

    handleURLParams() {
        const urlParams = new URLSearchParams(window.location.search);
        const authStatus = urlParams.get('auth_status');
        const authService = urlParams.get('service');

        if (authStatus && authService) {
            const serviceName = authService.charAt(0).toUpperCase() + authService.slice(1);
            
            if (authStatus === 'success') {
                this.showFeedbackMessage(`Conectado ao ${serviceName} com sucesso!`, 'success');
                
                if (authService === 'spotify') {
                    this.updateButtonState(this.elements.spotifyBtn, authService, true);
                    this.loadAllSpotifyData();
                } else if (authService === 'youtube') {
                    this.updateButtonState(this.elements.youtubeBtn, authService, true);
                }
            } else if (authStatus === 'error') {
                this.showFeedbackMessage(`Falha na conexão com ${serviceName}. Tente novamente.`, 'error');
            }
            
            // Limpa parâmetros da URL
            history.replaceState({}, document.title, window.location.pathname);
        }
    }
}

// Inicialização quando o DOM estiver carregado
document.addEventListener('DOMContentLoaded', () => {
    new SpotifyYouTubeSync();
});