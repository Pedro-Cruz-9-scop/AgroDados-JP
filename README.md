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

## Testes
```powershell
py manage.py test
py manage.py collectstatic --noinput
```

O arquivo `.gitignore` exclui ambientes virtuais, segredos, banco SQLite, arquivos enviados e arquivos estáticos compilados. O `.env.example` documenta as variáveis esperadas; configure-as no ambiente local ou no gerenciador de segredos do serviço de hospedagem, sem enviar um `.env` real ao GitHub.

O workflow do GitHub Actions executa testes, checagem de migrações, coleta de arquivos estáticos e a verificação de produção ao enviar alterações ou abrir um pull request. Antes do primeiro commit, confira `git status` e confirme que `db.sqlite3`, `.venv/`, `venv/`, `.env` e `media/` não estão na lista.

## Publicação no GitHub e Render
Este projeto é uma aplicação Django; **GitHub Pages não executa Python, banco de dados ou autenticação**. Usar Pages causa o erro 404 ou deixa a aplicação sem funcionamento. Use o GitHub para armazenar o código e um serviço de hospedagem Python para executar o site.

O arquivo `render.yaml` prepara a implantação no Render como Blueprint. Envie o repositório ao GitHub, crie um Blueprint no Render e conecte esse repositório. O Render instalará as dependências, coletará os arquivos estáticos, aplicará as migrações ao iniciar e gerará uma chave secreta para o serviço. Depois da primeira implantação, crie o primeiro usuário pelo Shell do serviço com `python manage.py createsuperuser`.

O Blueprint usa SQLite e um disco persistente para manter o banco e os documentos enviados após reinicializações e novas implantações. O disco persistente exige um serviço pago no Render e limita o aplicativo a uma única instância; confira os preços antes de confirmar a implantação. O banco publicado começa vazio: os dados do `db.sqlite3` local não são enviados ao GitHub nem copiados automaticamente para a hospedagem. O Blueprint define a versão de Python em `.python-version`.

## Produção
Antes de hospedar o sistema, configure HTTPS e estas variáveis no ambiente de produção:
```powershell
$env:DJANGO_DEBUG="0"
$env:DJANGO_SECRET_KEY="uma-chave-forte-e-exclusiva"
$env:DJANGO_ALLOWED_HOSTS="seu-dominio.com"
py manage.py check --deploy
py manage.py collectstatic --noinput
```

O SQLite incluído é apropriado para desenvolvimento e uma instância única. No Render, o Blueprint monta um disco persistente em `/var/data`, separando banco e documentos dos arquivos temporários da aplicação. Para escalar para várias instâncias, migre para um banco gerenciado e armazenamento compartilhado de documentos.

## Indicadores
O painel e os relatórios usam os registros cadastrados na conta. Não há estimativas de produtividade sem dados de produção informados.
