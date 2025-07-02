### Security Policy – Playlist Port

## Suporte à Segurança

Este projeto ainda está em desenvolvimento ativo, mas valorizamos e levamos a segurança a sério.

Se você encontrar alguma vulnerabilidade ou comportamento suspeito no `Playlist Port`, por favor, siga os passos abaixo.

## Relatar Vulnerabilidades

Para relatar uma falha de segurança:

- Envie um e-mail diretamente para: **gilyan.dev@gmail.com**
- Não abra um _issue_ público para evitar exploração indevida
- Inclua detalhes técnicos e, se possível, um exemplo mínimo para reproduzir

## Escopo de Segurança

Este projeto utiliza autenticação OAuth 2.0 com as seguintes APIs:

- **Spotify Web API**
- **YouTube Data API v3**

Certifique-se de:

- Não expor seu arquivo `.env`
- Nunca fazer commit de `client_secret` ou `access_token`
- Proteger a chave `YOUTUBE_API_KEY` de uso público excessivo

## Atualizações

A segurança é revisada a cada novo recurso implementado. Para contribuir:

- Sempre valide os tokens antes de usar
- Adicione tratamento de erros para respostas 401/403
- Valide entradas do usuário antes de fazer requisições externas

## Dependências

- As dependências estão listadas em `requirements.txt`
- Use sempre ambientes isolados (`venv`)
- Mantenha as versões atualizadas com segurança (sem quebrar o app)

## Responsabilidade

Este projeto **não coleta nem armazena dados pessoais sensíveis**.
Todo o processo de autenticação é feito diretamente com as APIs oficiais do Spotify e YouTube, respeitando os fluxos OAuth 2.0.

## Obrigado!

Obrigado por contribuir para manter este projeto seguro.
