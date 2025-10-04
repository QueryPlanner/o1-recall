# Recall - Quiz Frontend

Duolingo-style quiz application frontend built with React and TypeScript.

## Prerequisites

- Node.js 18+
- Backend API running at `http://localhost:8000`

## Setup

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Ensure the backend is running:
```bash
cd ../backend
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

3. Start the development server:
```bash
npm run dev
```

4. Open `http://localhost:5173` in your browser.

## Features

- 🔥 Daily streak tracking
- 📚 Topic and sub-topic organization
- ❓ Multiple-choice questions with explanations
- 🎯 Live feedback on answers
- 📊 Progress tracking
- 🎨 Duolingo-inspired UI with green theme

## Configuration

The API base URL is set in `api.ts`:
```typescript
const API_BASE_URL = 'http://localhost:8000';
```

Change this if your backend runs on a different port or host.

## Build for Production

```bash
npm run build
```

The built files will be in the `dist/` directory.

## Tech Stack

- React 19
- TypeScript
- Vite
- Tailwind CSS (via UnoCSS-like utility classes)
