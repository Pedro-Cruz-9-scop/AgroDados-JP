# AgroDados — protótipo Django

Sistema demonstrativo de histórico agrícola, desenvolvido com Django, HTML, CSS e JavaScript puro. Não exige Node.js.

## Requisitos
- Python 3.10+
- Internet apenas para instalar o Django (se ainda não estiver instalado)

## Executar no Windows / VS Code
1. Extraia o ZIP e abra a pasta `agrodados_django` no VS Code.
2. Abra o terminal nessa pasta.
3. Crie e ative um ambiente virtual:
   ```powershell
   py -m venv .venv
   .venv\Scripts\activate
   ```
4. Instale as dependências:
   ```powershell
   py -m pip install -r requirements.txt
   ```
5. Crie as tabelas do banco:
   ```powershell
   py manage.py migrate
   ```
6. (Opcional) Crie um administrador para o `/admin/`:
   ```powershell
   py manage.py createsuperuser
   ```
7. Inicie o servidor:
   ```powershell
   py manage.py runserver
   ```
8. Acesse `http://127.0.0.1:8000/` e crie uma conta pela tela de cadastro.

Se `py` não funcionar, use `python` no lugar. Não é necessário instalar Node.js.

## Funcionalidades atuais
- Login, cadastro e logout via POST com proteção CSRF.
- Cadastro de propriedades e insumos.
- Cadastro de talhões vinculados às propriedades, com validação da área total e nomes únicos por propriedade.
- Registro e consulta de atividades agrícolas.
- Relatórios com filtros por propriedade e período, indicadores por tipo de atividade e exportação CSV no navegador.
- Registros vinculados ao usuário conectado para evitar exibição cruzada entre contas.
- Interface responsiva e páginas de demonstração.

## Limitações conhecidas
- O mapa de talhões é apenas ilustrativo e não usa geolocalização; o cadastro e as áreas dos talhões são persistidos no banco.
- O gráfico de produtividade da página inicial contém dados ilustrativos, não indicadores calculados a partir de colheitas reais.
- Não existe integração com a Receita Federal, mapas georreferenciados, pagamentos ou recomendações agronômicas.
- O estoque de insumos não é abatido automaticamente quando uma atividade é registrada.
- Este projeto é um protótipo para desenvolvimento local, não uma instalação pronta para produção.

## Antes de publicar na internet
Configure uma `DJANGO_SECRET_KEY` forte via variável de ambiente, `DJANGO_DEBUG=0`, `DJANGO_ALLOWED_HOSTS`, HTTPS, backups, política de privacidade e revisão de permissões. Faça testes de segurança e migrações antes de armazenar dados reais.
