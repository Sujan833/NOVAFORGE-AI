# NovaForge AI (NOVAFORGE-AI)

Automatic website builder with AI. Generates HTML/CSS/JS (and optional Flask backend + SQLite database) from a natural-language description, lets you iterate using a Copilot-style modifier, and can push/deploy generated projects.

## Project structure

- `frontend/` – NovaForge web UI (static single-page app)
- `backend/` – Flask API for generation, project storage, GitHub push, Render deploy
  - `server2.py` – main backend entry point
  - `server3.py` – alternative backend entry point
  - `generation_pipeline.py` – generation pipeline helpers

Generated projects are stored under:
- `backend/generated_projects/<project-name>/frontend/*`
- `backend/generated_projects/<project-name>/backend/*` (optional)

## Prerequisites

- Python 3.10+ (recommended)
- Git
- (Optional) a Google Gemini API key if you want AI-based generation
  - Environment variable: `GEMINI_API_KEY`
- (Optional) Render API key if you want one-click deploy
  - Environment variable (or provide via UI): `RENDER_API_KEY`
- (Optional) GitHub token if you want “Push to GitHub”

## 1) Install backend dependencies

Go to the `backend/` directory and install Python deps from `requirments.txt`:

```bat
###  COMMANDS   ####
cd backend
py -m venv venv
venv\Scripts\activate
pip install -r requirments.txt
python server.py
open index.html in live server seperately......
```

## 2) Configure environment variables

Create/update backend env file:

- `backend/.env`

Example:

```env
GEMINI_API_KEY=your_gemini_api_key
RENDER_API_KEY=your_render_api_key
GITHUB_TOKEN=your_github_token_optional
```

> If `GEMINI_API_KEY` is missing, `server2.py` will raise an error at startup.

## 3) Start the backend API

From repo root:

```bat
py backend\server2.py
```

Expected:
- Backend listens on **http://localhost:5000**

## 4) Open the frontend (NovaForge UI)

Serve `frontend/` in a browser.

Common options:

### Option A: Use VSCode Live Server
Open `frontend/index.html` with Live Server.

### Option B: Simple Python server
From repo root:

```bat
py -m http.server 5500
```

Then open:
- http://localhost:5500/frontend/index.html

> The UI is designed to call the backend at `http://localhost:5000` (and uses a special-case when running at port `5500`).

## Using the app

1. In the UI, fill:
   - **Project Name**
   - **Detailed Description**
   - **Project Type** (e.g., static, landing, fullstack)
   - Optional feature checkboxes (Database, Authentication, Admin Dashboard, Contact Form, File Upload)
2. Click **✨ Generate Website**.
3. Use **Preview** tab to see the generated site.
4. Use **🤖 Copilot** / **Add feature** to request targeted code changes.
5. Use **Download Project**, **Push to GitHub**, and **Deploy** buttons.

## Useful API endpoints (backend)

Backend is Flask and returns JSON.

- `POST /api/generate`
- `GET /api/projects`
- `GET /api/projects/<project_name>`
- `POST /api/add-feature`
- `POST /api/copilot-modify`
- `POST /api/push-github`
- `POST /api/deploy`
- `GET /api/deploy-status?service_id=...&deploy_id=...`

## Notes / gotchas

- `backend/requirments.txt` (note the spelling) is the Python dependency file.
- Generated projects embed API base URLs like `http://localhost:5001/api` depending on the generated project type; start of the *generated* backend is only needed when the generated project type includes backend/database features.
- Render deploy currently prefers **static** deployment mode.

