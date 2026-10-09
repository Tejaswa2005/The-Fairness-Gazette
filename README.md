# THE FAIRNESS GAZETTE

THE FAIRNESS GAZETTE is a production-ready fairness audit platform that evaluates machine-learning models for bias and presents the result as a vintage newspaper front page. The backend performs the audit, stores verdict history, and exposes a FastAPI API. The frontend delivers the editorial experience, upload flow, and archive browsing.

![Screenshot placeholder](docs/screenshots/screenshot-placeholder.png)

## Tech Stack

- Backend: Python 3.11, FastAPI, SQLAlchemy, SQLite, pandas, scikit-learn, Fairlearn
- Frontend: React, TypeScript, Vite, Tailwind CSS, axios, Recharts
- Deployment: Docker, Docker Compose, Render, Railway, Vercel, Netlify

## How It Works

1. Upload a CSV, Excel, or JSON dataset from the newspaper-style frontend.
2. The backend validates and normalizes the file, then the user chooses a sensitive feature.
3. The fairness engine trains a LogisticRegression baseline and computes fairness metrics.
4. The verdict, evidence, and editorial note are saved to SQLite and returned to the UI.
5. The appeal flow applies Fairlearn mitigation and shows before/after results.

## Project Layout

```text
THE FAIRNESS GAZETTE/
├── Backend/
│   ├── app/
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   ├── public/sample-case.csv
│   ├── Dockerfile
│   ├── nginx.conf
│   └── .env.example
├── docker-compose.yml
└── README.md
```

## Local Setup

### Backend

```bash
cd Backend
py -3.11 -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Frontend

```bash
cd frontend
npm install
copy .env.example .env
npm run dev
```

The frontend points to `http://localhost:8000` by default. If you move the backend, update `VITE_API_BASE_URL` in `frontend/.env`.

## Run With Docker

```bash
docker compose up --build
```

- Backend: `http://localhost:8000`
- Frontend: `http://localhost:5173`

## Deployment

### Backend on Render or Railway

1. Point the service at the `Backend/` folder.
2. Use the environment variables from `Backend/.env.example`.
3. Start the app with `uvicorn app.main:app --host 0.0.0.0 --port 8000`.
4. Add the deployed frontend origin to `CORS_ORIGINS`.

### Frontend on Vercel or Netlify

1. Point the project at the `frontend/` folder.
2. Set `VITE_API_BASE_URL` to the live backend URL.
3. Build with `npm run build` and deploy the static output.

## Testing the API

1. Open `http://localhost:8000/docs`.
2. Use `POST /upload` to inspect a dataset.
3. Use `POST /audit` to create and save a verdict.
4. Use `POST /appeal` to compare mitigation before and after.
5. Use `GET /verdicts` and `GET /verdicts/{id}` to browse the archive.

## Sample Case

The frontend includes a `Try a Sample Case` button that loads `frontend/public/sample-case.csv`, detects the columns, and runs an instant audit.

## Screenshots

- Front-page masthead and verdict headline
- Evidence chart and ruling seal
- Archive and back-issue layout

## Notes

- Print/export uses the browser print dialog and the project print stylesheet, so the verdict can be saved as a clean PDF.
- SQLite is the default database, so no external database service is required for local development.