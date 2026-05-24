# Immigration Law Guidance — Web App

A desktop-friendly web interface for easier testing and demo sharing, built with React + TypeScript + Vite.

## Getting started

```bash
cd web
npm install
npm run dev
```

The app opens at **http://localhost:5173** by default.

## Environment

Copy `.env.example` to `.env.local` and update values as needed:

```bash
cp .env.example .env.local
```

| Variable | Default | Description |
|---|---|---|
| `VITE_API_BASE_URL` | `http://localhost:8000` | Backend API base URL |

The backend does not need to be running to start the web app. API calls will fail gracefully until it is available.

## Scripts

| Command | Description |
|---|---|
| `npm run dev` | Start dev server (hot reload) |
| `npm run build` | Type-check and build for production |
| `npm run preview` | Preview the production build locally |
| `npm run type-check` | Run TypeScript type-check only |

## Tech stack

- **React 18** — UI
- **TypeScript** — type safety
- **Vite** — build tool and dev server
- **React Router v6** — client-side routing
- **CSS Modules** — scoped component styles

## Layout

The app uses a three-panel dashboard layout:

```
┌──────────────┬─────────────────────────────┬───────────────┐
│  Sidebar     │  Main panel                 │  Sources      │
│  (240 px)    │  (flex)                     │  (280 px)     │
│              │                             │               │
│  App name    │  Chat messages / content    │  Citations /  │
│  Navigation  │                             │  references   │
│  History     │  Input area                 │               │
└──────────────┴─────────────────────────────┴───────────────┘
```

## Disclaimer

This app provides legal information and guidance, not legal advice. For personal legal decisions, consult a qualified attorney.
