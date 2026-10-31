# AgroDados — Gestão e rastreabilidade rural

## Requisitos
- Python 3.10 a 3.14 (faixa testada no GitHub Actions)
- SQLite (já incluído no Python)
- Não precisa instalar Node.js

## Executar localmente no Windows / PowerShell
```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
$env:DJANGO_DEBUG="1"
py manage.py migrate
py manage.py createsuperuser
py manage.py runserver
```

Abra http://127.0.0.1:8000/ e crie sua conta. O banco SQLite local é criado automaticamente pelas migrações.
Para testes isolados, `DJANGO_DATABASE_PATH` pode apontar para outro arquivo SQLite.

## Mapa
O mapa usa Leaflet, imagens de satélite da Esri, mapa de ruas do OpenStreetMap e geocodificação do OpenStreetMap. O controle de camadas dentro do mapa permite alternar entre satélite e ruas. Precisa de conexão com a internet, mas não exige chave de API. É possível buscar locais, desenhar limites, calcular a área aproximada e salvar ou excluir talhões associados às propriedades da conta.

## Configuração
Defina estas variáveis no ambiente antes de iniciar o Django. Em PowerShell:
```powershell
$env:DJANGO_DEBUG="1"
$env:DJANGO_SECRET_KEY="chave-local-de-desenvolvimento"
$env:DJANGO_ALLOWED_HOSTS="127.0.0.1,localhost"
py manage.py runserver
```

Para produção, configure `DJANGO_DEBUG=0`, gere uma chave secreta exclusiva com `py -c "import secrets; print(secrets.token_urlsafe(50))"` e informe o resultado em `DJANGO_SECRET_KEY`; configure também os domínios em `DJANGO_ALLOWED_HOSTS`. Nunca publique segredos, o banco de dados local ou arquivos enviados por usuários.

## Privacidade e acesso administrativo
Cada usuário conectado vê e altera somente os registros da própria conta. Visitantes sem login não acessam as telas privadas nem os documentos enviados. O administrador pode consultar os usuários, e-mails, propriedades, talhões, insumos, atividades e documentos de todas as contas pelo painel `/admin/`; crie a conta administrativa com `py manage.py createsuperuser`.

As senhas nunca são exibidas: o Django armazena hashes de senha, não a senha original. O administrador pode redefinir uma senha pelo painel, mas não consegue recuperar a senha atual. O histórico disponível para consulta inclui as atividades agrícolas cadastradas no sistema.

## Testes
```powershell
py manage.py test
py manage.py collectstatic --noinput
```

O arquivo `.gitignore` exclui ambientes virtuais, segredos, banco SQLite, arquivos enviados e arquivos estáticos compilados. O `.env.example` documenta as variáveis esperadas; configure-as no ambiente local ou no gerenciador de segredos do serviço de hospedagem, sem enviar um `.env` real ao GitHub.

O workflow do GitHub Actions executa testes, checagem de migrações, coleta de arquivos estáticos e a verificação de produção ao enviar alterações ou abrir um pull request. Antes do primeiro commit, confira `git status` e confirme que `db.sqlite3`, `.venv/`, `venv/`, `.env` e `media/` não estão na lista.

## Colocar no ar rápido (modo de teste)
Para ver o site funcionando sem Neon nem R2, crie um *Web Service* no Render a partir do repositório e defina:

- Build Command: `pip install -r requirements.txt && python manage.py collectstatic --noinput`
- Start Command: `python manage.py migrate --noinput && python -m gunicorn agrodados.wsgi:application --workers 1 --threads 4 --timeout 120`
- Variáveis: `DJANGO_DEBUG=0`, `DJANGO_SECRET_KEY` (valor aleatório longo), `DJANGO_ALLOWED_HOSTS=.onrender.com` e `ALLOW_EPHEMERAL_STORAGE=1`.

Neste modo o banco SQLite e os arquivos ficam no disco temporário: **contas, registros, fotos e documentos são perdidos a cada reinício ou novo deploy**. Use só para testar. Para uso real, siga a seção abaixo.

## Publicação gratuita no GitHub e Render
Este projeto é uma aplicação Django; **GitHub Pages não executa Python, banco de dados ou autenticação**. Use o GitHub para armazenar o código e o Render para executar o site. O arquivo `render.yaml` configura um serviço Web gratuito, sem disco persistente.

O armazenamento local do Render é temporário: o serviço pode dormir por inatividade e os arquivos locais podem desaparecer ao reiniciar ou publicar uma nova versão. Por isso, a implantação exige um PostgreSQL externo e armazenamento de documentos externo. Sem eles, a aplicação recusa iniciar no Render em vez de aparentar que salvou dados que seriam perdidos.

### Serviços externos necessários
1. Crie um banco PostgreSQL no [Neon](https://neon.tech/), copie a connection string e configure-a como `DATABASE_URL` nas variáveis do serviço Render. Use a URL de conexão com SSL (`sslmode=require`). O Django continua usando SQLite localmente quando `DATABASE_URL` não está definida.
2. Crie um bucket privado no [Cloudflare R2](https://www.cloudflare.com/developer-platform/products/r2/), crie uma chave de acesso com permissão de leitura e gravação nesse bucket e configure no Render:
   - `R2_BUCKET_NAME`: nome do bucket;
   - `R2_ENDPOINT_URL`: `https://<ACCOUNT_ID>.r2.cloudflarestorage.com`;
   - `R2_ACCESS_KEY_ID` e `R2_SECRET_ACCESS_KEY`: credenciais da chave.
   Os documentos continuam privados e são servidos pela rota autenticada do sistema.
3. Envie o repositório ao GitHub, crie um Blueprint no Render e conecte o repositório. Preencha as variáveis secretas solicitadas antes do primeiro deploy. O Render instala as dependências, coleta os arquivos estáticos, aplica as migrações e gera `DJANGO_SECRET_KEY`.
4. Após a implantação, crie o primeiro usuário pelo Shell do serviço: `python manage.py createsuperuser`.

O plano gratuito tem limites, pode suspender o serviço e não oferece garantias de disponibilidade; os limites e condições dos provedores podem mudar. Verifique as condições atuais do [Render](https://render.com/pricing), [Neon](https://neon.tech/pricing) e [Cloudflare R2](https://developers.cloudflare.com/r2/pricing/) antes de publicar. O banco publicado começa vazio: o `db.sqlite3` local não é enviado nem copiado automaticamente. A versão de Python está em `.python-version`.

Não publique segredos, o banco de dados local ou arquivos enviados. Configure as variáveis secretas somente no painel do Render, nunca no `render.yaml` ou em um commit.

## Produção
Antes de hospedar o sistema, configure HTTPS e estas variáveis no ambiente de produção:
```powershell
$env:DJANGO_DEBUG="0"
$env:DJANGO_SECRET_KEY="uma-chave-forte-e-exclusiva"
$env:DJANGO_ALLOWED_HOSTS="seu-dominio.com"
py manage.py check --deploy
py manage.py collectstatic --noinput
```

O SQLite e o armazenamento de arquivos local são usados apenas no desenvolvimento. No Render, a aplicação usa PostgreSQL e R2; não adicione um disco persistente pago se a intenção for permanecer no plano gratuito.

## Indicadores
O painel e os relatórios usam os registros cadastrados na conta. Não há estimativas de produtividade sem dados de produção informados.

## Licença
Distribuído sob a licença MIT. Veja o arquivo `LICENSE`.
