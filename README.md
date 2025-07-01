# repo-playlistport-v0

🌐 Tecnologias que vamos usar:
Python 3
Flask (para o servidor web)
Requests (para chamadas HTTP)
OAuth 2.0 (padrão de autenticação das APIs)

⚙️ Requisitos:
Conta de desenvolvedor:
Spotify Developer Dashboard
Google Cloud Console (YouTube API)

Crie dois apps para obter:
Client ID / Client Secret (Spotify)
Client ID / Client Secret (YouTube/Google OAuth)

BASH
pip install flask requests

🧪 Estrutura básica do app:
app.py – Backend Flask com autenticação Spotify + YouTube

✅ Resultado:
Você poderá:
Acessar http://localhost:5000
Fazer login com Spotify e YouTube
Armazenar os tokens de cada serviço na sessão
Usar esses tokens depois para ler playlists e criar no YouTube

🚀 Próximo passo:
Ler playlists do Spotify usando o token
Buscar vídeos equivalentes no YouTube
Criar uma nova playlist no YouTube com os resultados
