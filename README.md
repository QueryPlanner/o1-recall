# o1-recall
Name: “o1‑recall” is a nod to O(1) — constant‑time recall — aiming for near‑instant memory fetch from brain memory.

I have struggled to remember things. I keep forgetting.
- When friends ask “how much did you buy this for?” I can’t recall.
- When a familiar topic comes up, I know I read it but can’t retrieve it.
- My brain keeps statements but I forget the facts to back them.
- While solving problems, I can picture a tool/command I used before but can’t recall it at the right time.

This project is a personal experiment to offset forgetting using science‑based study protocols. The core idea: use testing as a study tool immediately after reading, then keep revisiting material in small, regular sessions.

## What this app does
- Generate questions from a link or PDF using Google GenAI
- Organize by Topic → Sub‑topic
- Practice MCQs with instant feedback and explanations
- Random mode for interleaved practice across topics
- Daily streak with a simple goal (answer N questions/day)

## Why this approach (principles we actually use)
- Offset forgetting: frequent self‑testing is the best way to retain material.
- Test soon after exposure: generate questions right after reading and practice immediately.
- Embrace errors: the app shows the correct answer and explanation to lock in learning.
- Interleaving: “Random Practice” mixes questions across topics to strengthen connections.
- Consistency: a daily streak nudges short, regular sessions.

> We deliberately keep the protocol lightweight and practical. Complex sleep/NSDR/meditation routines are valuable, but this MVP focuses on the testing behaviors that drive retention.

---

## Monorepo layout
```
o1-recall/
  backend/          # FastAPI + Neon (Postgres) + Google GenAI
  frontend/         # React (Vite + TS) Duolingo‑style UI
```

---

## Backend (FastAPI)

### Requirements
- Python 3.11+
- Neon Postgres database (connection string with `sslmode=require`)
- Google GenAI API key

### Environment
Create `o1-recall/backend/.env`:
```
DATABASE_URL=postgresql://USER:PASSWORD@HOST/DB_NAME?sslmode=require
GENAI_API_KEY=your_gemini_api_key
GENAI_MODEL=gemini-2.0-flash-001
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
DEFAULT_USER_ID=1
```

### Install & run (uv)
```
cd o1-recall/backend
uv venv .venv
source .venv/bin/activate
uv pip install -r requirements.txt
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
- Tables are auto‑created on startup from `app/sql/schema.sql`.
- Docs: http://localhost:8000/docs

### Key endpoints
- GET `/topics` → list topics
- GET `/topics/{topic_id}/sub_topics` → list sub‑topics
- GET `/sub_topics/{sub_topic_id}/questions?limit=5` → random unanswered (falls back to full set when exhausted)
- GET `/questions/random?limit=5` → interleaved practice across all topics
- POST `/answers` → log attempts `{ question_id, choice_id }` and return `{ is_correct, correct_choice_id }`
- GET `/streak` → `{ current_streak_days, today_answers_count, streak_goal }`
- POST `/generate/from-link` (form) → `url`, `size=small|large`, optional `topic`, `sub_topic`
- POST `/generate/from-pdf` (multipart) → `pdf`, `size=small|large`, optional `topic`, `sub_topic`

Notes
- Generation enforces exact requested counts (25 or 50) and unifies a single topic for the batch; sub‑topics may vary.
- Frontend grades instantly from payload; backend logging is async.

---

## Frontend (React + Vite)

### Requirements
- Node.js 18+

### Install & run
```
cd o1-recall/frontend
npm install
npm run dev
```
Open http://localhost:5173

### Configure API
`frontend/api.ts`:
```
const API_BASE_URL = 'http://localhost:8000';
```
Change if backend runs elsewhere.

### Using the app
1. Click “+ Create Questions”
   - From Link or PDF, choose size Small (25) or Large (50)
   - Optionally set Topic/Sub‑topic
2. Practice
   - Pick a Topic → Sub‑topic, or tap “Random Practice”
   - Answer 5 at a time; feedback is instant with explanations
3. Streak
   - Keep the daily count to maintain your streak

---

## Troubleshooting
- Link generation returns `bad_url_status`: the site likely blocks non‑browser clients. Save as PDF and use the PDF option.
- Blank screen in Random Practice: ensure backend is running and `/questions/random` returns results.
- Slow feedback: optimized already—grading is local; network logging is async.

## License
MIT.
