# User Guide — Investor

For the person using BIP to simulate an investment journey. Covers the full
parcours from cahier des charges §8. Everything here is virtual — no real
money is ever collected or moved, and no real order is ever sent to a market.

## 1. Create an account

Go to **Register**, enter your name, email, and a password (min. 8
characters). You're signed in immediately and redirected to the KYC form —
your account exists but is in **pending** status until KYC is validated.

## 2. Complete identity verification (KYC)

This is a *simulated* KYC — it demonstrates the parcours, not a real
regulatory check (§10). Fill in your legal name, date of birth, country, and
an ID document type/number, then **Submit**. Status moves to
**submitted, awaiting review**.

A back-office operator (or admin) then validates or rejects your file from
their **KYC Queue**. If rejected, you'll see the reason and can edit and
resubmit. If validated, your account **activates automatically** and is
credited with the platform's starting simulated cash balance — same
transaction, so you can never end up "active but unfunded."

## 3. Browse the market

**Market** lists every tradable instrument (symbol, company, sector, last
price, status). Click one to see its price history chart and open an order
ticket. Prices come from real market data (yfinance) ingested into the
platform's own quote history — or a plausible fallback if that feed is
unreachable, so the demo never depends on live internet access.

## 4. Place an order

From an instrument's page:

1. Choose **Buy** or **Sell**.
2. Choose **Market** (executes at the last known price) or **Limit** (executes
   only if that price is at least as good as your limit).
3. Enter quantity (and limit price, if applicable).
4. Review the estimate box — gross amount, commission, total — then **Confirm**.

Before anything executes, the platform runs pre-trade checks (§16): your
account must be active, KYC validated, the instrument tradable, and you must
have enough available cash (buy) or shares (sell) — "available" meaning not
already held by another pending order's reservation (§17). If a check fails,
the order is rejected with the specific reason shown to you.

This MVP executes synchronously — there's no order book or waiting; you'll
see the result (executed or rejected) immediately.

## 5. Track your orders

**Order History** lists every order you've placed with its status
(submitted → reserved → executed/cancelled/rejected). Open one for full
detail: the linked execution(s) and every ledger entry it produced, so you
can see the complete chain from order to cash movement.

A **reserved** order (limit order not yet filled) can be cancelled — its
hold on your cash or shares is released immediately.

## 6. Portfolio and ledger

- **Portfolio** — your open positions (quantity, average cost, last price,
  market value), cash available vs. reserved, and unrealized P&L. Always
  computed live from your positions and cash — never a stale cached number.
- **Ledger** — the immutable, chronological record of every cash movement on
  your account (initial credit, trades, fees), each with a running balance.
  Filterable by entry type.

## 7. Account settings

From **Account Settings** you can change your password (requires your
current password). If you've forgotten it, use **Forgot password?** on the
login page — this MVP has no outbound email integration, so the reset link
is shown to you directly instead of emailed (clearly labeled as a
demo-only simplification); in a production deployment it would be emailed.
