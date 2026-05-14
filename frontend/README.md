# Immigration Law Guidance App - Frontend

**Next.js + React + TypeScript + Tailwind CSS**

## Quick Start

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm run start

# Run linter
npm run lint

# Type check
npm run type-check
```

## Project Structure

```
frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx          # Root layout with Header/Footer
│   │   ├── page.tsx            # Home page
│   │   ├── globals.css         # Global styles (Tailwind)
│   │   ├── ask/
│   │   │   └── page.tsx        # Ask Question page
│   │   ├── scenarios/
│   │   │   └── page.tsx        # Scenario Guides page
│   │   └── about/
│   │       └── page.tsx        # About page
│   ├── components/
│   │   ├── Header.tsx          # Navigation header
│   │   ├── Footer.tsx          # Disclaimer footer
│   │   └── SourcesCitations.tsx # Reusable sources component
│   └── lib/
│       └── mockData.ts         # Mock data for UI testing
├── package.json
├── tsconfig.json
├── tailwind.config.js
├── next.config.js
└── README.md
```

## Pages

### 1. Home Page (`/`)
- Hero section with app name and disclaimer
- Two CTAs: "Ask a Question" and "Browse Common Scenarios"
- Features section explaining how it works
- Preview of common scenarios

### 2. Ask Question Page (`/ask`)
- Textarea for immigration questions
- Language dropdown (placeholder for future i18n)
- Privacy note about data handling
- Mock answer display with all required sections:
  - Short Answer
  - Simple Explanation
  - Possible Risks
  - What To Do Next
  - Official Sources
  - Legal Disclaimer

### 3. Scenario Guides Page (`/scenarios`)
- Cards for 6 common scenarios with risk levels
- Modal popup with scenario details (placeholder content)
- Risk level indicators (high/medium/low)

### 4. About Page (`/about`)
- Mission statement
- What the app does/doesn't do
- Legal disclaimer
- Privacy & data security info
- Technology stack

## Components

### Header
- Navigation: Home, Ask, Scenarios, About
- Responsive design (mobile menu placeholder)
- Primary color scheme (blue)

### Footer
- Legal disclaimer
- Emergency notice
- Copyright info

### SourcesCitations
- Reusable component for displaying official sources
- Shows citation, title, and source URL
- Type labels (Regulation, Statute, Case Law, Agency Guidance)

## Mock Data

All data is currently mocked in `src/lib/mockData.ts`:
- `mockScenarios`: 6 common immigration scenarios
- `mockAnswer`: Placeholder answer structure

## Backend Integration TODOs

Marked in code with `TODO:` comments:

1. **Ask Question Page** (`src/app/ask/page.tsx`):
   - Replace mock `setTimeout` with actual API call
   - POST to `/api/answer` with `{ question, language }`
   - Handle loading states and errors
   - Process real API response

2. **Environment Variables** (`next.config.js`):
   - Add `API_BASE_URL` when backend is ready
   - Configure CORS if needed

## Important Rules (Followed)

✅ No OpenAI or public AI API calls  
✅ No localStorage for user questions  
✅ No authentication (yet)  
✅ No backend integration (yet)  
✅ No final legal content  
✅ Mock data only for UI testing  
✅ Comments where API integration will happen  

## Next Steps (After Backend Ready)

1. Set up API proxy or configure CORS
2. Replace mock data with real API calls
3. Add error handling and loading states
4. Implement language selection (i18n)
5. Add question history (opt-in, privacy-safe)
6. Implement mobile menu toggle
7. Add analytics (privacy-respecting)

## Tech Stack

- **Framework:** Next.js 15.2 (App Router)
- **React:** 19.0
- **TypeScript:** 5.8
- **Styling:** Tailwind CSS 4.1
- **Font:** Inter (Google Fonts)
