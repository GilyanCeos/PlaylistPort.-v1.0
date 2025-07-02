### Security Policy – PlaylistPort.

## Suporte à Segurança

Este projeto ainda está em desenvolvimento ativo, mas valorizamos e levamos a segurança a sério.

## Relatar Vulnerabilidades

Se você encontrar alguma vulnerabilidade ou comportamento suspeito no `PlaylistPort.`, por favor, siga os passos abaixo:

* Envie um e-mail diretamente para: **[gilyan.dev@gmail.com](mailto:gilyan.dev@gmail.com)**
* Não abra um *issue* público para evitar exploração indevida
* Inclua detalhes técnicos e, se possível, um exemplo mínimo para reproduzir

## Escopo de Segurança

Este projeto utiliza autenticação OAuth 2.0 com as seguintes APIs:

* **Spotify Web API**
* **YouTube Data API v3**

Certifique-se de:

* Não expor seu arquivo `.env`
* Nunca fazer commit de `client_secret` ou `access_token`
* Proteger a chave `YOUTUBE_API_KEY` de uso público excessivo

## Atualizações

A segurança é revisada a cada novo recurso implementado. Para contribuir:

* Sempre valide os tokens antes de usar
* Adicione tratamento de erros para respostas 401/403
* Valide entradas do usuário antes de fazer requisições externas

## Dependências

* As dependências estão listadas em `requirements.txt`
* Use sempre ambientes isolados (`venv`)
* Mantenha as versões atualizadas com segurança (sem quebrar o app)

## Responsabilidade

Este projeto **não coleta nem armazena dados pessoais sensíveis**.
Todo o processo de autenticação é feito diretamente com as APIs oficiais do Spotify e YouTube, respeitando os fluxos OAuth 2.0.

🔒 Este app solicitará acesso apenas para ler e criar suas playlists. Nunca acessamos ou controlamos outras partes da sua conta.

---

## Licença e Uso Indevido

**O uso deste software para fins comerciais está expressamente proibido sem a devida autorização legal e contratual.**

A utilização do PlaylistPort para revenda, monetização direta, ou qualquer atividade que envolva exploração econômica sem consentimento do(s) autor(es) e o cumprimento dos termos das APIs envolvidas (Spotify e YouTube) pode configurar violação de direitos autorais, de marca e de políticas de uso.

Ao utilizar este projeto, você concorda em respeitar:

* Os **Termos de Uso da API do Spotify**
* Os **Termos de Serviço da YouTube Data API**
* A **Licença deste repositório** (consultar arquivo `LICENSE`)

---

## Obrigado!

Obrigado por contribuir para manter este projeto seguro.
