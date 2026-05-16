# Immigration Law Guidance — Mobile (MVP)

End-user **React Native** app built with **Expo** and **Expo Router**. This is separate from the Next.js web app in `../frontend/` (web/demo/admin).

## Stack

- React Native + Expo (~52)
- TypeScript
- Expo Router (file-based navigation)
- StyleSheet (blue / white / gray theme)
- **Mock data only** — no backend API calls, no local question history, no secrets in repo

## Structure

```
mobile/
├── app/              # Expo Router screens
├── src/
│   ├── components/   # Shared UI
│   ├── lib/          # mockData.ts
│   └── theme/        # colors, spacing, typography
```

## Screens

| Route | Purpose |
|-------|---------|
| `/` | Home — navigation + disclaimers |
| `/ask` | Question composer + mock answer sections |
| `/scenarios` | Scenario cards + detail modal |
| `/about` | Mission, limits, privacy, source-first approach |

## Commands

```bash
cd mobile
npm install
npm run type-check
npx expo start
```

Use the Expo Go app or a simulator from the CLI menu. Press `i` for iOS simulator or `a` for Android emulator when available.

## Branch

Develop mobile work on **`feature/mobile-foundation`**, not `feature/frontend-foundation`.

## Future work

- Connect to backend retrieval API when ready
- Persist nothing locally for user questions by default
- Admin/database tools remain on the web app
