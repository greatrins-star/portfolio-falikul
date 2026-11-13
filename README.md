# Falikul Isbah Portfolio

A responsive portfolio website with a Python standard-library backend and a persistent SQLite database for contact form submissions. No third-party packages are required.

## Run locally

1. Install Python 3.9 or newer.
2. From this folder, run `python server.py`.
3. Open [http://127.0.0.1:8000](http://127.0.0.1:8000).

The server creates `data/portfolio.db` and its `contact_messages` table on first startup. Messages submitted through the contact form are stored in that database. To choose another database file, set the `PORTFOLIO_DB` environment variable before starting the server.

The server listens on `0.0.0.0` by default. Set `HOST` and `PORT` environment variables when you need to change the bind address or port.

## Deploy on Railway

Railway supplies a `PORT` environment variable. The server uses that port and listens on `0.0.0.0` by default so Railway can route public requests to it. Redeploy after pushing this change.

SQLite files on a deployment may not survive redeploys unless they are stored on persistent storage. To preserve contact messages on Railway, attach a volume mounted at `/data` and set `PORTFOLIO_DB=/data/portfolio.db` in the service variables.

## API

- `GET /api/health` — server health check.
- `POST /api/contact` — save a JSON contact message with `name`, `email`, and `message` fields.
