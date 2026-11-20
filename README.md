# UniPay

Protótipo de internet banking com frontend React, API Express e banco MySQL. O projeto pode ser iniciado com Docker Compose, sem instalar Node.js no computador.

## Requisitos

- Docker Desktop com Docker Compose v2;
- Google Chrome instalado, se for executar os testes Selenium;
- Python 3.10 ou superior, se for executar os testes Selenium.

## Iniciar o projeto

Abra esta pasta no terminal — a pasta que contém `docker-compose.yml` — e execute:

```sh
docker compose up --build -d
```

Na primeira execução, o Docker cria o MySQL, instala as dependências do frontend e inicia os serviços. Depois, acesse:

- Aplicação: [http://localhost:8080](http://localhost:8080)
- API: [http://localhost:3001](http://localhost:3001)
- Verificação da API e do banco: [http://localhost:3001/health](http://localhost:3001/health)

Para acompanhar os serviços e os logs:

```sh
docker compose ps
docker compose logs -f
```

Para encerrar os serviços sem apagar os dados do banco:

```sh
docker compose down
```

O banco fica salvo no volume `unipay_mysql_data`. Os arquivos de inicialização são `unipay-backend/database.sql` (estrutura das tabelas) e `unipay-backend/db/init/02-seed.sql` (contas e dados iniciais). O MySQL executa esses arquivos somente quando o volume é criado pela primeira vez.

> **Atenção:** `docker compose down -v` apaga o volume do MySQL e todos os dados locais. Use esse comando somente se quiser recriar um banco de teste descartável.

## Contas de teste

Em um banco criado do zero, as contas abaixo são inseridas pelo seed:

| Uso | E-mail / chave Pix | Senha | CPF |
|---|---|---|---|
| Conta remetente | `teste@email.com` | `teste@123` | `123.456.789-09` |
| Destinatário dos testes de Pix | `destino@email.com` | `destino@123` | `168.995.350-09` |

O destinatário já tem uma chave Pix igual ao e-mail. Os testes de Pix usam essa conta fixa, sem cadastrar um destinatário novo a cada execução.

## Executar os testes Selenium

Inicie o Docker Compose antes de rodar os testes, pois os scripts acessam `http://localhost:8080`. O Chrome abre em modo visível. O Selenium Manager tenta obter o driver compatível com o Chrome automaticamente; na primeira execução, o computador pode precisar de acesso à internet.

No Windows PowerShell:

```powershell
cd unipay-frontend/teste
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
cd ..\..
.\unipay-frontend\teste\.venv\Scripts\python.exe -m pytest -s -vv
```

No macOS ou Linux:

```sh
cd unipay-frontend/teste
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cd ../..
python -m pytest -s -vv
```

O `pytest.ini` na raiz configura a descoberta dos 11 arquivos numerados em `unipay-frontend/teste/pages/login-page/`. Para executar um caso isolado, use o caminho a partir da raiz, por exemplo:

```sh
python -m pytest -s -vv unipay-frontend/teste/pages/login-page/10detalhes_transacao_pix.py
```

As evidências de tela são salvas em `unipay-frontend/teste/screenshots/`, em uma pasta para cada teste.

### Dados alterados pelos testes

- `2register.py` cria uma conta nova para testar o cadastro;
- `5extrato_transacoes.py` faz um depósito de R$ 1,00 se o extrato estiver vazio;
- `9confirmar_pix.py`, `10detalhes_transacao_pix.py` e `11atualizacao_conta_pix.py` enviam Pix de R$ 10,00 para `destino@email.com`;
- os testes de Pix fazem um depósito de R$ 50,00 se a conta remetente estiver com saldo de R$ 10,00 ou menos.

Essas operações ficam no banco local persistente e podem alterar o saldo e o extrato entre execuções.

## Estrutura principal

```text
unipay-backend/       API Express, esquema e seed do MySQL
unipay-frontend/      aplicação React e testes Selenium
docker-compose.yml    inicialização dos serviços
pytest.ini            descoberta dos testes Python
```
