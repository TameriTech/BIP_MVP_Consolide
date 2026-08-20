# BIP — Simulated Investment Platform (MVP)

A simulated investment platform: signup → simulated KYC → virtual cash wallet →
browse a demo market → place orders → simulated execution → portfolio, ledger,
and history. **No real money is ever collected or moved, no real orders are
ever executed.** See `BIP_Cahier_des_charges_MVP_Consolide.pdf` for the full
spec this MVP implements.

## Stack

- **Backend**: Python 3.12, FastAPI, SQLAlchemy, PostgreSQL, Alembic. Auto API
  docs at `/docs`.
- **Frontend**: Vue 3 (Composition API), Vite, Pinia, PrimeVue.
- **Market data**: `yfinance` for ~18 well-known tickers, ingested into the
  platform's own `Quote` table. Falls back to seeded plausible prices if
  yfinance is unreachable — the app never depends on live internet access.
- **Deployment**: local-only via `docker-compose`. No cloud hosting.

## Quickstart

Requires Docker. The host machine's own Node/npm are **not** used — the
frontend dev server also runs inside its own container, avoiding any local
Node version issues.

```bash
cp .env.example .env
docker compose up -d
```

This starts three containers:

| Service    | URL                          |
|------------|-------------------------------|
| Postgres   | `localhost:5435`              |
| Backend    | `http://localhost:8010` (docs at `/docs`) |
| Frontend   | `http://localhost:5173`       |

First boot needs the database schema and seed data:

```bash
docker compose exec api alembic upgrade head
docker compose exec api python -m app.seed_demo
```

`seed_demo` runs the base seed (4 demo users across every role, 18 demo
instruments) and additionally KYC-validates and funds the `investor@bip.demo`
account with a small starting portfolio (a few executed buy/sell orders), so
the primary demo path never depends on a live action during a pitch.

Open `http://localhost:5173` and log in with any of:

| Email                     | Password        | Role                 |
|----------------------------|-----------------|----------------------|
| `investor@bip.demo`        | `DemoPass123!`  | Investor (pre-funded, KYC-validated) |
| `admin@bip.demo`           | `DemoPass123!`  | Admin                |
| `backoffice@bip.demo`      | `DemoPass123!`  | Back-office operator |
| `superadmin@bip.demo`      | `DemoPass123!`  | Super-admin          |

## Demo walkthrough

**Investor path** (as `investor@bip.demo`, already funded/validated):
1. Dashboard → cash + portfolio value at a glance.
2. Market → browse instruments, open one (e.g. AAPL) → price history chart.
3. Place a buy or sell order → confirm dialog → executes instantly (this MVP
   simulates execution synchronously — no order book, no waiting).
4. Order detail page → shows the full chain: order → execution → linked
   ledger entries, with running balances.
5. Portfolio / Ledger pages → live-computed from positions + ledger, never a
   stale cached number.

**Fresh signup path** (register a new account):
1. Register → redirected straight into the KYC form.
2. Fill it in, submit → status becomes "submitted, awaiting review".
3. Log in as `backoffice@bip.demo` (or `admin`/`super_admin`) → **Back-office
   → KYC Queue** → Validate → the account activates and is credited
   automatically.
4. Log back in as the investor → account is now active and funded.

**Back-office path** (as `backoffice@bip.demo` / `admin@bip.demo` /
`superadmin@bip.demo`):
- **KYC Queue** — validate/reject pending submissions.
- **Users** — view all users; role changes are super-admin only.
- **Accounts** — suspend/reactivate an account (a suspended account can't
  place new orders — pre-trade checks reject them with an explicit reason).
- **Instruments** — toggle tradability, add new instruments, force a market
  price refresh.
- **Orders / Ledger / Audit Log** — full read-only oversight across every
  account.
- **Settings** — super-admin-only platform configuration (e.g. fee rate).

## Running the backend test suite

```bash
docker compose exec api pytest
```

`tests/financial_invariants/` is the most important directory — it covers
concurrency (no double-spend/double-sell), atomicity (a mid-execution failure
rolls back everything), and ledger/position reconciliation. These tests use a
separate `bip_test` database so they never touch the dev/demo data above.

## Project structure

```
backend/app/
  core/     config, security (JWT/bcrypt), auth deps, error types
  models/   SQLAlchemy models — one file per entity
  schemas/  Pydantic request/response models
  routers/  HTTP layer only, no business logic
  services/ orchestration layer
  engine/   the financial core: pretrade checks, reservation locking,
            OMS state machine, execution — pure, no HTTP/FastAPI imports
  workers/  yfinance ingestion (startup backfill + periodic refresh)
backend/tests/
  financial_invariants/  concurrency, atomicity, reconciliation
  api/, unit/             everything else

frontend/src/
  api/      one module per backend domain
  stores/   Pinia state
  router/   role-based route guards
  layouts/  AppShell (nav + role-aware menu)
  views/    auth/, onboarding/, market/, orders/, portfolio/, ledger/,
            backoffice/
```

## Known simplifications (by design, for a 2-week MVP)

- Order execution is synchronous (submit = execute in one request) — no
  order book, no partial fills. Still models a proper OMS state machine and
  full order→reservation→execution→ledger→position traceability.
- Single currency (USD), matching the yfinance-sourced tickers used for the
  demo market. Purely a display/config choice to change later.
- RBAC is 4 fixed roles enforced by route/endpoint guards — no fine-grained
  permission matrix.
- Password reset works end-to-end (`/auth/forgot-password` →
  `/auth/reset-password`, single-use tokens, 30-minute expiry) but there is no
  outbound email integration — the reset token is returned directly in the
  API/UI instead of emailed, the same "simulated, not real infra" approach
  used for KYC.

## Documentation

Beyond this README, [`docs/`](docs/) has the deliverables listed in the
cahier des charges (§33): [data model](docs/DATA_MODEL.md),
[user guide](docs/USER_GUIDE.md), [admin/back-office guide](docs/ADMIN_GUIDE.md),
and [test plan & report](docs/TEST_PLAN_AND_REPORT.md). Full API reference is
the live OpenAPI docs at `/docs` (see Quickstart) rather than a static copy,
so it never drifts from the actual code.
