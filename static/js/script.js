// static/js/script.js

document.addEventListener('DOMContentLoaded', function() {
    const spotifyBtn = document.querySelector('.btn-spotify');
    const youtubeBtn = document.querySelector('.btn-youtube');
    const syncNowBtn = document.querySelector('.btn-sync-now');
    const feedbackMessageDiv = document.getElementById('feedback-message');

    function showFeedbackMessage(message, type) {
        feedbackMessageDiv.textContent = message;
        feedbackMessageDiv.className = `feedback-message ${type}`;
        feedbackMessageDiv.classList.remove('hidden');
        setTimeout(() => {
            feedbackMessageDiv.classList.add('hidden');
            feedbackMessageDiv.textContent = '';
        }, 5000);
    }

    if (spotifyBtn) {
        spotifyBtn.addEventListener('click', function() {
            window.location.href = '/login/spotify';
            showFeedbackMessage('Redirecionando para o Spotify...', 'success');
        });
    }

    if (youtubeBtn) {
        youtubeBtn.addEventListener('click', function() {
            window.location.href = '/login/youtube';
            showFeedbackMessage('Redirecionando para o YouTube...', 'success');
        });
    }

    if (syncNowBtn) {
        syncNowBtn.addEventListener('click', function() {
            // Obtém a playlist selecionada via botão ativo
            const selectedBtn = document.querySelector('.playlist-btn.selected');
            if (!selectedBtn) {
                showFeedbackMessage('Por favor, selecione uma playlist para sincronizar.', 'error');
                return;
            }
            const playlistId = selectedBtn.dataset.playlistId;
            window.location.href = `/sync?playlist_id=${playlistId}`;
            showFeedbackMessage('Iniciando sincronização...', 'success');
        });
    }

    // Função para carregar playlists Spotify via AJAX
    async function loadSpotifyPlaylists() {
        const playlistsContainer = document.getElementById('playlists-container');
        playlistsContainer.innerHTML = '<p>Carregando playlists...</p>';

        try {
            const response = await fetch('/spotify-playlists');
            if (!response.ok) {
                playlistsContainer.innerHTML = '<p>Erro ao carregar playlists.</p>';
                return;
            }
            const data = await response.json();

            if (data.error) {
                playlistsContainer.innerHTML = `<p>${data.error}</p>`;
                return;
            }

            const playlists = data.playlists;
            if (playlists.length === 0) {
                playlistsContainer.innerHTML = '<p>Nenhuma playlist encontrada.</p>';
                return;
            }

            playlistsContainer.innerHTML = '';

            playlists.forEach(pl => {
                const btn = document.createElement('button');
                btn.textContent = `${pl.name} (${pl.tracks_total} músicas)`;
                btn.className = 'btn playlist-btn';
                btn.dataset.playlistId = pl.id;

                btn.addEventListener('click', () => {
                    // Remove seleção anterior
                    document.querySelectorAll('.playlist-btn').forEach(b => b.classList.remove('selected'));
                    // Marca o atual como selecionado
                    btn.classList.add('selected');
                });

                playlistsContainer.appendChild(btn);
            });
        } catch (err) {
            playlistsContainer.innerHTML = '<p>Erro inesperado ao carregar playlists.</p>';
            console.error(err);
        }
    }

    // Ler parâmetros da URL para mostrar mensagens e estados dos botões
    const urlParams = new URLSearchParams(window.location.search);
    const authStatus = urlParams.get('auth_status');
    const authService = urlParams.get('service');

    if (authStatus && authService) {
        if (authStatus === 'success') {
            showFeedbackMessage(`Conectado ao ${authService.charAt(0).toUpperCase() + authService.slice(1)} com sucesso!`, 'success');
            if (authService === 'spotify' && spotifyBtn) {
                spotifyBtn.textContent = 'Spotify Conectado';
                spotifyBtn.classList.add('connected');
                spotifyBtn.disabled = true;
                loadSpotifyPlaylists(); // Carregar playlists após conexão
            } else if (authService === 'youtube' && youtubeBtn) {
                youtubeBtn.textContent = 'YouTube Conectado';
                youtubeBtn.classList.add('connected');
                youtubeBtn.disabled = true;
            }
        } else if (authStatus === 'error') {
            showFeedbackMessage(`Falha na conexão com ${authService.charAt(0).toUpperCase() + authService.slice(1)}. Tente novamente.`, 'error');
        }
        // Limpa parâmetros da URL
        history.replaceState({}, document.title, window.location.pathname);
    }
});
