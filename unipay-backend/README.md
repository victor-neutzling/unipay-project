# UniPay backend

Express API using MySQL and parameterized raw SQL queries (`mysql2`). The frontend lives in the sibling `unipay-frontend` folder; the root `docker-compose.yml` runs the web app, API, and database together.

## Run the full stack

From the project root, run:

```sh
docker compose up --build
```

Open [http://localhost:8080](http://localhost:8080). The API health endpoint is [http://localhost:3001/health](http://localhost:3001/health). Compose initializes the `uniPay` database and its catalog rows on the first startup, and stores database files in the named `unipay_mysql_data` volume.

The default credentials and JWT secret in Compose are only for a local demo. From the project root, copy `unipay-backend/.env.example` to `.env` and replace the values before sharing the environment or exposing its ports:

```sh
cp unipay-backend/.env.example .env
```

To stop the containers while keeping account data, run `docker compose down`. To erase the database volume and all demo accounts, run `docker compose down -v`.

## API

- `POST /api/auth/register` — name, email, CPF and password; creates an email-based PIX key.
- `POST /api/auth/login` — returns an eight-hour bearer token and account summary.
- `GET /api/account` — signed-in account and current balance.
- `GET /api/account/transactions` — signed-in account statement.
- `GET /api/pix/lookup?key=...` — resolve a PIX recipient key.
- `GET /api/pix/recent` — recent PIX recipients.
- `POST /api/pix/transfers` — atomically debit/credit both accounts and write both statement entries.

Account and PIX routes require `Authorization: Bearer <token>`. Passwords are hashed with bcrypt. Database operations use bound `?` parameters; no ORM is used.

## Database notes

The schema follows the supplied tables. It widens `usuario.senha` to hold a bcrypt hash, requires and uniquely indexes email and CPF, and makes the account's email PIX key unique. PIX transfers are recorded as an outgoing entry for the sender and an incoming entry for the recipient inside one MySQL transaction.

MySQL loads the schema from `database.sql` and the initial data from `db/init/02-seed.sql` only when it initializes an empty data volume. The API also applies compatibility changes for the counterparty CPF and name columns at startup. After changing the initialization schema, use a fresh local volume (`docker compose down -v`) to replay it; this erases local demo data.
