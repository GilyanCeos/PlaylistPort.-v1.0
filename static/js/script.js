// static/js/script.js

document.addEventListener('DOMContentLoaded', function() {
    // Seleciona os botões de autenticação
    const spotifyBtn = document.querySelector('.btn-spotify');
    const youtubeBtn = document.querySelector('.btn-youtube');
    const syncNowBtn = document.querySelector('.btn-sync-now');
    const feedbackMessageDiv = document.getElementById('feedback-message');

    /**
     * Exibe uma mensagem de feedback na tela.
     * @param {string} message - A mensagem a ser exibida.
     * @param {string} type - O tipo da mensagem ('success' ou 'error').
     */
    function showFeedbackMessage(message, type) {
        feedbackMessageDiv.textContent = message;
        feedbackMessageDiv.className = `feedback-message ${type}`; // Adiciona a classe de tipo
        feedbackMessageDiv.classList.remove('hidden'); // Remove a classe 'hidden' para mostrar
        // Opcional: Ocultar a mensagem após alguns segundos
        setTimeout(() => {
            feedbackMessageDiv.classList.add('hidden');
            feedbackMessageDiv.textContent = ''; // Limpa o texto
        }, 5000); // Mensagem some após 5 segundos
    }

    // Adiciona event listener para o botão Spotify
    if (spotifyBtn) {
        spotifyBtn.addEventListener('click', function() {
            // Redireciona para a rota de login do Spotify no Flask
            window.location.href = '/login/spotify';
            // Opcional: Mostrar uma mensagem enquanto redireciona
            showFeedbackMessage('Redirecionando para o Spotify...', 'success');
        });
    }

    // Adiciona event listener para o botão YouTube
    if (youtubeBtn) {
        youtubeBtn.addEventListener('click', function() {
            // Redireciona para a rota de login do YouTube no Flask
            window.location.href = '/login/youtube';
            // Opcional: Mostrar uma mensagem enquanto redireciona
            showFeedbackMessage('Redirecionando para o YouTube...', 'success');
        });
    }

    // Adiciona event listener para o botão Sync-Now
    if (syncNowBtn) {
        syncNowBtn.addEventListener('click', function() {
            // Redireciona para a rota de sincronização no Flask
            window.location.href = '/sync';
            // Opcional: Mostrar uma mensagem enquanto inicia a sincronização
            showFeedbackMessage('Iniciando sincronização...', 'success');
        });
    }

    // --- Lógica para verificar o status de autenticação (simulação) ---
    // Em uma aplicação real, você passaria o status de autenticação do Flask para o HTML
    // e o JavaScript leria isso. Por enquanto, vamos simular.

    // Exemplo de como você pode verificar o URL para mensagens de sucesso/erro após o callback
    const urlParams = new URLSearchParams(window.location.search);
    const authStatus = urlParams.get('auth_status'); // Ex: ?auth_status=spotify_success
    const authService = urlParams.get('service'); // Ex: ?service=spotify

    if (authStatus && authService) {
        if (authStatus === 'success') {
            showFeedbackMessage(`Conectado ao ${authService.charAt(0).toUpperCase() + authService.slice(1)} com sucesso!`, 'success');
            // Atualiza o estado visual do botão após sucesso
            if (authService === 'spotify' && spotifyBtn) {
                spotifyBtn.textContent = 'Spotify Conectado';
                spotifyBtn.classList.add('connected');
                spotifyBtn.disabled = true; // Desabilita o botão
            } else if (authService === 'youtube' && youtubeBtn) {
                youtubeBtn.textContent = 'YouTube Conectado';
                youtubeBtn.classList.add('connected');
                youtubeBtn.disabled = true; // Desabilita o botão
            }
        } else if (authStatus === 'error') {
            showFeedbackMessage(`Falha na conexão com ${authService.charAt(0).toUpperCase() + authService.slice(1)}. Tente novamente.`, 'error');
        }
        // Limpa os parâmetros da URL para que a mensagem não reapareça ao recarregar
        history.replaceState({}, document.title, window.location.pathname);
    }
});
