# Cloud Deployment (optional, free-tier)

The platform is designed to run **local-only via `docker-compose`** (see the
main [README](../README.md)) — that's the primary, always-supported path.
This guide is an optional add-on for putting a live demo URL online, at no
cost, using free tiers of two hosting providers. It doesn't replace or
change the local setup.

Two accounts are required — both free, no credit card needed for the tiers
used here. Claude/the assistant cannot create these for you; the steps
below are yours to run.

## What gets deployed where

| Piece | Provider | Why |
|---|---|---|
| Postgres database | [Neon](https://neon.tech) | Free tier has no expiry date (unlike Render's free Postgres, which auto-deletes after 30 days) |
| Backend (FastAPI, Docker) | [Render](https://render.com) | Free Web Service, deploys straight from the existing `backend/Dockerfile` |
| Frontend (Vue/Vite) | [Render](https://render.com) | Free Static Site — no sleep, no cold start |

[`render.yaml`](../render.yaml) at the repo root defines both Render
services as a **Blueprint**, so both deploy together from one click instead
of being configured by hand.

## 1. Create the database (Neon)

1. Sign up at [neon.tech](https://neon.tech) (free).
2. Create a project — any region. Neon creates a default database for you.
3. From the project dashboard, copy the **connection string**. It looks
   like:
   ```
   postgresql://<user>:<password>@<host>.neon.tech/<dbname>?sslmode=require
   ```
4. This app connects via SQLAlchemy's `psycopg2` driver, so add `+psycopg2`
   right after `postgresql`:
   ```
   postgresql+psycopg2://<user>:<password>@<host>.neon.tech/<dbname>?sslmode=require
   ```
   Keep this string handy for step 2.4 below.

## 2. Deploy both services (Render)

1. Sign up at [render.com](https://render.com) (free), then **New +** →
   **Blueprint**.
2. Connect your GitHub account and select the `BIP_MVP_Consolide` repo.
   Render detects `render.yaml` automatically and shows two services:
   `bip-mvp-backend` and `bip-mvp-frontend`.
3. Click **Apply** to create both.
4. Once `bip-mvp-backend` exists, open it → **Environment** → set
   `DATABASE_URL` to the connection string from step 1.4 (this is the one
   value the blueprint deliberately leaves blank, since it's a secret).
   `JWT_SECRET` is generated automatically by Render; everything else has a
   working default baked into `render.yaml`.
5. Trigger (or wait for) a deploy on both services. The backend's start
   command runs `alembic upgrade head` and the idempotent demo seed
   (`app.seed_demo`) automatically on every boot — first deploy will have a
   fully-seeded database with no extra steps.

## 3. Verify the URLs line up

Render names services `<name>.onrender.com`. `render.yaml` assumes:

- Backend: `https://bip-mvp-backend.onrender.com`
- Frontend: `https://bip-mvp-frontend.onrender.com`

If either name was already taken and Render assigned a different one,
update two places to match the **actual** URLs Render gives you, then
redeploy both services:

- Backend env var `CORS_ORIGINS` → must list the actual frontend URL
  (e.g. `["https://your-actual-frontend.onrender.com"]`), or the browser
  will block every API call with a CORS error.
- Frontend env var `VITE_API_BASE_URL` → must point at the actual backend
  URL plus `/api/v1` (e.g. `https://your-actual-backend.onrender.com/api/v1`).
  This one is baked in at **build time**, so the frontend needs a fresh
  build after changing it, not just a restart.

## 4. Try it

Open the frontend URL and sign in with the same demo credentials as local
(`investor@bip.demo` / `DemoPass123!`, etc. — see the main README).

## Free-tier tradeoffs

- **Backend cold starts.** Render's free Web Service spins down after ~15
  minutes idle; the next request wakes it up, taking 30–50 seconds. Fine
  for an occasional demo link, not for something expected to always be
  instantly responsive.
- **Database cold starts.** Neon's free compute auto-suspends after
  inactivity too, with a similar brief delay on the first query after a
  quiet period — usually much shorter than the backend's own wake-up.
- **No custom domain on the free tier** unless you add one yourself later.

None of this affects the local `docker-compose` setup, which has no sleep
behavior and remains the fastest way to run or demo the platform.
