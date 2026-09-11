# Grokbot

A lightweight [Grok](https://x.ai)-powered chatbot with a clean web UI. It talks to
xAI's Grok API when an `XAI_API_KEY` is configured, and falls back to a deterministic
**local mock** so you can develop and demo it end-to-end without any secrets.

## Features

- Express backend with a small JSON API (`/api/chat`, `/api/health`).
- Modern, responsive chat UI (vanilla JS, no build step).
- xAI Grok integration with a zero-config local mock fallback.
- Unit + HTTP integration tests via the built-in Node test runner.
- ESLint (flat config) for linting.

## Requirements

- Node.js >= 20 (developed on Node 22).

## Getting started

```bash
npm ci          # install dependencies
npm run dev     # start the dev server with auto-reload on http://localhost:3000
```

Then open http://localhost:3000 and start chatting.

Without an API key the app runs in **mock mode** (the header badge shows "Local mock mode").
To talk to the real Grok model, set an xAI API key:

```bash
export XAI_API_KEY="xai-..."   # get one from https://console.x.ai
npm run dev
```

### Optional configuration

| Variable       | Default                                   | Description                     |
| -------------- | ----------------------------------------- | ------------------------------- |
| `PORT`         | `3000`                                    | Port the server listens on.     |
| `XAI_API_KEY`  | _(unset)_                                 | Enables the real Grok API.      |
| `XAI_MODEL`    | `grok-2-latest`                           | Model name to request.          |
| `XAI_API_URL`  | `https://api.x.ai/v1/chat/completions`    | Override the API endpoint.      |

## Scripts

| Command        | Description                              |
| -------------- | ---------------------------------------- |
| `npm run dev`  | Start the server with file watching.     |
| `npm start`    | Start the server.                        |
| `npm test`     | Run the test suite.                      |
| `npm run lint` | Lint the codebase.                       |

## API

`POST /api/chat` — body `{ "message": "your text" }` → `{ "reply": "...", "source": "grok" | "mock" }`

`GET /api/health` — `{ "status": "ok", "mode": "grok" | "mock" }`

## Project layout

```
src/
  server.js        Express app + routes
  grok.js          Grok client and mock fallback
  public/          Static chat UI (HTML/CSS/JS)
test/              Node test-runner unit + integration tests
```
