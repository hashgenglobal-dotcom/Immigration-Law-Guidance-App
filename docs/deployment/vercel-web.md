# Vercel — web app (`web/`)

Production URL: https://immigrationlawguidanceapp.vercel.app/

## Project settings (required)

In the Vercel project linked to this repo:

| Setting | Value |
|---------|--------|
| **Production branch** | `main` |
| **Root Directory** | `web` **or** leave empty and use repo-root `vercel.json` |
| **Framework Preset** | Vite |
| **Build Command** | `npm run build` (if root is `web`) |
| **Output Directory** | `dist` (if root is `web`) |

Environment:

| Variable | Example |
|----------|---------|
| `VITE_API_BASE_URL` | `https://your-render-backend.onrender.com` |

## Verify a deploy picked up your commit

1. Vercel → **Deployments** → latest should match GitHub `main` SHA (e.g. `077519a`).
2. Open the site → View Source → CSS filename should change after each build (not stay on an old `index-Cv_pdvdn.css`).
3. In DevTools → Network → open the `.css` file → `:root` should include `--bg: #f4f1ea` and `--navy: #1f2839`.

## If Git pushes do not redeploy

1. **Deployments** → **Redeploy** → check **Use existing Build Cache** = **off**.
2. Confirm the Git integration is connected to `hashgenglobal-dotcom/Immigration-Law-Guidance-App`.
3. If Root Directory was `frontend`, change it to `web` (`frontend/` is not on `main`).

## Local preview (same as Vercel build)

```bash
cd web
npm ci
npm run build
npm run preview
```
