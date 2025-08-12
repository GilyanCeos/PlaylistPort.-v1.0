# PlaylistPort

**PlaylistPort** é uma aplicação que permite sincronizar playlists do Spotify com o YouTube. Ideal para quem deseja fazer backup, migrar listas entre plataformas ou encontrar clipes de suas músicas favoritas de forma automatizada.

## Funcionalidades

- 🔐 Autenticação via Spotify e YouTube (OAuth 2.0)
- 📂 Leitura de playlists e músicas do Spotify
- 🔍 Busca automática dos vídeos no YouTube
- 📺 Criação de uma nova playlist no YouTube com os clipes encontrados
- ✅ Totalmente baseado em API oficial de ambas as plataformas

## Tecnologias Utilizadas

- Python 3
- Flask
- Requests
- YouTube Data API v3
- Spotify Web API
- python-dotenv

## Instalação e Execução

### 1. Clone o repositório

```bash
git clone https://github.com/GilyanCeos/PlaylistPort.-v1.0.git

cd PlaylistPort.-v1.0.git
```
### 2. Crie e ative um ambiente virtual

```bash
python -m venv venv

source venv/bin/activate    # Linux/Mac

venv\Scripts\activate       # Windows
```
### 3. Instale as dependências

```bash
pip install -r requirements.txt
```
### 4. Configure as credenciais

- Obtenha suas chaves de API do Spotify e do YouTube.

- Renomeie o arquivo `.env.example` para `.env` na raiz do projeto e preencha com suas chaves:

```env
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
SPOTIFY_REDIRECT_URI=http://127.0.0.1:5000/callback/spotify

YOUTUBE_CLIENT_ID=your_youtube_client_id
YOUTUBE_CLIENT_SECRET=your_youtube_client_secret
YOUTUBE_REDIRECT_URI=http://127.0.0.1:5000/callback/youtube
YOUTUBE_API_KEY=your_youtube_API_key
```

Essas chaves podem ser adquiridas gratuitamente nos links:

  - https://developer.spotify.com/
  - https://console.cloud.google.com/

⚠️Importante: não compartilhe esse arquivo. Ele está protegido no .gitignore.

### 5. Execute a aplicação

```bash
python app.py
```
- Acesse http://127.0.0.1:5000/ no navegador.


## Considerações Importantes

A API do YouTube Data v3 tem um limite de requisições diárias, que geralmente é de 10.000 unidades de cota por dia. Cada chamada para a API consome uma quantidade específica dessas unidades:

  - Busca por vídeo (/search): Consome 100 unidades por requisição.
  - Criação de playlist (/playlists): Consome 50 unidades por requisição.
  - Adição de item na playlist (/playlistItems): Consome 50 unidades por requisição.

Se você está sincronizando uma playlist com, por exemplo, 100 músicas, o cálculo de cota seria:

  ```bash
  100 (para busca) x 100 (músicas) = 10.000 unidades + 
  1 x 50 (criação da playlist) = 50 unidades + 
  100 x 50 (adição dos vídeos) = 5.000 unidades

Nesse cenário, você gastaria 15.050 unidades, excedendo o limite diário em uma única execução.
  ```

Dessa forma, o uso diário recomendado é a sincronização de 1 playlist com máximo de 50 músicas, para que tudo ocorra perfeitamente.

A cota é redefinida diariamente à meia-noite (fuso horário do Pacífico, ou 4h da manhã no horário de Brasília).


## Contribuições

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou pull requests.

## Licença

Este projeto está licenciado sob a [Creative Commons Attribution-NonCommercial 4.0 International](https://creativecommons.org/licenses/by-nc/4.0/deed.pt_BR). Consulte o arquivo [LICENSE](./license.md) para mais informações.

## Créditos

Spotify Web API Docs

YouTube Data API Docs
