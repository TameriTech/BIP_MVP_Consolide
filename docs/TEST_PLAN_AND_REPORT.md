# Test Plan & Report

Covers cahier des charges §29 ("Plan de tests et rapport de tests"). Kept as
one document since the report is a direct, current run of the plan below —
splitting them would just invite the two to drift apart.

## 1. Test plan

### Strategy

The doc's own priority order (Annexe B: exactitude financière → sécurité →
traçabilité → fiabilité du moteur d'ordres → UX) drives where test effort is
concentrated. Financial correctness gets the deepest coverage; UI polish gets
none automated (see §4, Known gaps).

### Layers

| Layer | Location | What it covers |
|---|---|---|
| Unit | `backend/tests/unit/` | OMS state machine, RBAC role-check, JWT/password hashing, market-data parsing — pure logic, no DB/HTTP |
| API | `backend/tests/api/` | Every router: auth (incl. password reset), KYC, market, orders, portfolio, ledger, back-office admin |
| Financial invariants | `backend/tests/financial_invariants/` | The properties that actually matter for a "real" platform: no double-spend/double-sell under concurrency, all-or-nothing execution atomicity, ledger↔position↔cash reconciliation |
| Integration | `backend/tests/integration/` | Reserved for cross-service flows; currently empty — see §4 |

### What the financial-invariant suite specifically proves

- **`test_concurrency.py`** — fires several concurrent buy (or sell) orders
  against the same account/position from separate DB connections/threads and
  asserts exactly as many execute as the account could actually afford —
  direct proof the `SELECT ... FOR UPDATE` locking design in
  [`engine/reservation.py`](../backend/app/engine/reservation.py) serializes
  correctly rather than racing.
- **`test_execution_atomicity.py`** — injects a failure partway through
  `execution_engine.fill()` (after the first ledger write, before the second)
  and asserts *everything* from that order attempt rolls back: cash, position,
  reservation, and the ledger entry that had already been written. Also
  statically asserts `ledger_writer` exposes no update/delete function at all.
- **`test_ledger_reconciliation.py`** — after a sequence of trades, asserts
  `sum(ledger entries) == account.cash_balance`, each entry's `balance_after`
  is a true running snapshot, and the full
  order → reservation → execution → ledger → position chain is
  reconstructable by foreign key alone.

### Out of scope for automated testing (manual/visual only)

- Frontend UI (no Vitest/Cypress/Playwright suite in this repo — see §4).
- Load testing beyond the concurrency tests above (§29 asks for "tests de
  charge adaptés au MVP" — the concurrency suite is the adapted version: it
  proves correctness under concurrent load, not throughput/latency SLAs,
  which don't apply to a non-production simulation prototype).

## 2. Test report

**Last run:** 2026-08-19, against `368c9320a690` (head), inside the project's
own `docker compose` stack.

### Backend — `docker compose exec api pytest`

```
76 passed, 0 failed in ~52s
(financial_invariants subset alone: 7 passed in ~6s — included in the 76)
```

Breakdown by file:

| File | Tests | Focus |
|---|---|---|
| `unit/test_oms.py` | 12 | Every allowed/disallowed order-status transition |
| `unit/test_rbac.py` | 2 | Role-gate accepts/rejects |
| `unit/test_security.py` | 5 | Password hash roundtrip, JWT roundtrip, tampered/garbage token rejection |
| `unit/test_market_data_service.py` | 6 | yfinance parsing/fallback behavior |
| `api/test_auth.py` | 11 | Register/login/refresh/change-password + **forgot/reset-password** (new) |
| `api/test_kyc.py` | 4 | Draft → submit → validate/reject, account activation side-effect |
| `api/test_market.py` | 7 | Instrument listing/filtering, quote history |
| `api/test_orders.py` | 12 | Submit/cancel, every pre-trade rejection reason |
| `api/test_portfolio_and_ledger.py` | 4 | Portfolio computation, ledger scoping to own account |
| `api/test_backoffice_admin.py` | 6 | Every back-office endpoint's role gate, KYC review, account status |
| `financial_invariants/test_concurrency.py` | 2 | No double-spend, no double-sell |
| `financial_invariants/test_execution_atomicity.py` | 2 | All-or-nothing execution, append-only contract |
| `financial_invariants/test_ledger_reconciliation.py` | 3 | Ledger/position/cash reconciliation, full traceability |
| **Total** | **76** | |

### Frontend — `npx vue-tsc -b --noEmit`

```
Exit code 0 — no type errors.
```

There is no unit/component test suite for the frontend (Vitest is not
installed). Verification is currently: strict TypeScript compilation +
manual walkthrough of the demo paths in README's "Demo walkthrough" section.

## 3. Known gaps

- **No frontend automated tests.** Everything under `frontend/src/` is
  verified by typechecking + manual QA, not by an automated suite. Adding
  Vitest component tests for the order ticket and the KYC form would be the
  highest-value next addition.
- **`backend/tests/integration/` is empty.** Reserved for future multi-service
  flows (e.g. end-to-end HTTP-driven scenarios spanning register → KYC →
  order → ledger in one test); currently that flow is only covered
  piecemeal, one router at a time.
