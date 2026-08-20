# Admin / Back-Office Guide

For **admin**, **backoffice_operator**, and **super_admin** users. Covers the
back-office scope from cahier des charges §22. All back-office endpoints are
role-gated server-side ([`routers/backoffice.py`](../backend/app/routers/backoffice.py))
— the roles below aren't just a UI convention.

| Role | Can do |
|---|---|
| `backoffice_operator` | Review KYC, manage instruments, view users/accounts/orders/ledger/audit log |
| `admin` | Everything `backoffice_operator` can, same permission set in this MVP |
| `super_admin` | Everything above, **plus** change user roles and edit platform settings |

(RBAC is intentionally 4 fixed roles with no fine-grained permission matrix —
see README's "Known simplifications.")

## KYC Queue

Lists submitted KYC files awaiting review. Open one to see the submitted
details, then **Validate** or **Reject** (with a reason, shown to the
investor). Validating a KYC file **atomically** activates the account and
credits the initial simulated cash balance in the same transaction — there's
no window where an account is active but unfunded, or validated but not yet
active.

## Users

Read-only list of every user and their role. Role changes
(`PATCH /backoffice/users/{id}/role`) are **super-admin only**.

## Accounts

List and filter accounts by status. **Suspend** an account to immediately
block it from placing new orders — pre-trade checks reject with an explicit
"account is not active" reason. **Reactivate** to restore it.

## Instruments

Manage the tradable-instrument referential (§11): add a new instrument,
edit its name/sector, or **toggle tradability** (a halted instrument is
rejected by pre-trade checks with an explicit reason, per §16). **Force a
market refresh** to pull the latest prices from the yfinance feed on demand
rather than waiting for the periodic background refresh.

## Orders, Executions, Ledger

Read-only oversight across **every** account — not scoped to your own, unlike
the investor-facing views. Filterable by status/account/date/entry type.
Useful for demonstrating end-to-end traceability of any transaction during a
walkthrough.

## Audit Log

Every sensitive action recorded platform-wide: order execution/rejection,
KYC review, account status change, role change, settings change. Each entry
carries the actor, their role, the action, the affected entity, and a
timestamp — filterable by actor/entity type/action. This is the audit trail
referenced by §23/§24 ("traçabilité des actions sensibles").

## Settings

Platform-wide simulation parameters (e.g. the trading fee rate in basis
points) stored as key/value pairs. **Editing a setting is super-admin only.**
Changes here affect all *subsequent* orders — already-executed trades keep
the fee rate they were charged at.
