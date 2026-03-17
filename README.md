# ARTH - AI-Powered Financial Co-pilot (Node.js/Express Version) ₳

ARTH is a comprehensive fintech ecosystem designed to empower Indian users with AI-driven financial intelligence.

---

## 🚀 The Core "ARTH" Suite

### 1. ARTH SHIELD (Agreement Analyzer)
*   Scans PDF/TXT agreements for hidden risks using an internal FastAPI AI service.
*   **New**: Multer-powered file upload support.

### 2. ARTH SCORE (Loan Predictor)
*   Predicts loan approval probability based on income and credit data.

### 3. ARTH PULSE (Debt Trap Predictor)
*   Forecasts debt trap risk with an AI "Prescription" action plan.

### 4. ARTH GOALS (Retirement Planner)
*   Dynamic wealth projection and long-term investment strategy.

### 5. ARTH INTELLIGENCE PLATFORM (New)
*   Financial Risk Radar
*   Scam Loan App Detector
*   Financial Simulation Engine
*   What-If Scenario Engine (5-year projection)
*   Emergency Financial Detector
*   Cultural Spending Intelligence
*   WhatsApp Expense Parser
*   Financial Habit Score (0-850)

---

## ⚙️ Backend Architecture (Express & MongoDB)

### Tech Stack
- **Framework**: Node.js & Express.js.
- **Database**: MongoDB Atlas (NoSQL) with Mongoose ODM.
- **AI Intelligence**: Python FastAPI microservice (`ai-service/`) with scikit-learn models and rule-based logic.
- **File Handling**: Multer (for agreement uploads).
- **Format Parsing**: PDF-Parse (to extract text from financial PDFs).
- **Security**: JWT & Bcrypt.js.

### Directory Structure
- `src/models/`: Mongoose schemas for Users, Expenses, Agreements, Goals.
- `src/routes/`: Express routers for modular API endpoints.
- `src/services/aiService.js`: Integration logic for the Python AI microservice.
- `ai-service/`: Independent Python service for agreement analysis, festival prediction, debt pulse, advisor, and loan prediction.
- `ai-service/ai_services/`: Modular financial intelligence engines (`risk_radar.py`, `scam_detector.py`, `financial_simulator.py`, `scenario_engine.py`, `emergency_detector.py`, `festival_intelligence.py`, `whatsapp_parser.py`, `habit_score_engine.py`).
- `src/middleware/auth.js`: JWT verification middleware.
- `src/index.js`: Main entry point.

### New API Surface

Express routes (`/api/ai/*`, authenticated):
- `POST /api/ai/risk-radar`
- `POST /api/ai/loan-scam-check`
- `POST /api/ai/simulation`
- `POST /api/ai/what-if`
- `POST /api/ai/emergency-detector`
- `POST /api/ai/festival-intelligence`
- `POST /api/ai/whatsapp-expense`
- `GET /api/ai/habit-score`

FastAPI routes (`/ai/*`, x-api-key protected):
- `POST /ai/risk-radar`
- `POST /ai/loan-scam-check`
- `POST /ai/simulation`
- `POST /ai/what-if`
- `POST /ai/emergency-detector`
- `POST /ai/festival-intelligence`
- `POST /ai/whatsapp-expense`
- `GET /ai/habit-score?user_id=<mongo-user-id>`

---

## ☁️ Deploy Live On Render (Recommended)

This repo now includes a Render Blueprint file: `render.yaml`.

### What To Consider Before Going Live

1. Service split
   - Deploy **2 web services**: Node API (`artha-backend-api`) and Python AI service (`artha-ai-service`).

2. Internal auth between services
   - Use the same `AI_SERVICE_API_KEY` value in both services.

3. Correct service URL wiring
   - Set Node's `PYTHON_AI_URL` to your live Python service URL:
     - Example: `https://artha-ai-service.onrender.com`

4. Database reliability
   - Use MongoDB Atlas (or another managed MongoDB).
   - Add Render egress IPs to Atlas network access, or allow `0.0.0.0/0` only if you understand the security tradeoff.

5. Cold starts and timeouts (especially on free plans)
   - AI endpoints may be slower after inactivity.
   - Consider paid plan for lower latency and more stable uptime.

6. Secrets and environment variables
   - Never hardcode secrets in code.
   - Configure all secrets in Render dashboard environment settings.

7. CORS and frontend URL
   - Restrict CORS in production to your frontend domain(s) instead of wildcard (`*`) when you are ready to harden security.

### Render Deployment Steps

1. Push this repo to GitHub.

2. In Render, click **New +** -> **Blueprint**.

3. Connect the GitHub repo and select this project.
   - Render will detect `render.yaml` and propose creating both services.

4. Set required env vars in Render before first deploy:
   - For `artha-ai-service`:
     - `MONGODB_URI`
     - `AI_SERVICE_API_KEY`
     - Optional: `NEWS_API_KEY`, `ALPHA_VANTAGE_API_KEY`
   - For `artha-backend-api`:
     - `MONGODB_URI`
     - `JWT_SECRET`
     - `AI_SERVICE_API_KEY` (must match AI service)
     - `PYTHON_AI_URL` (Python service live URL)

5. Deploy services.

6. Verify health checks:
   - Node API: `GET /`
   - Python AI: `GET /health`

7. Test AI path end-to-end:
   - Call a Node AI route such as `POST /api/ai/risk-radar`.
   - Confirm it returns real AI output (not fallback mock data).

### Post-Deploy Quick Validation

1. Node service root responds with status 200.
2. Python service `/health` returns `status: ok` or `status: degraded` with JSON.
3. Node logs do not show repeated `Python service fallback` warnings.
4. JWT auth-protected routes work with your frontend token.
5. MongoDB reads/writes work from both services.

---

## 🛠️ Setup & Installation

### Backend `.env`
Create `fintech-artha/.env`:

```env
PORT=8000
NODE_ENV=production
MONGODB_URI=mongodb+srv://<username>:<password>@<cluster>/<db>?appName=<app>
JWT_SECRET=your_jwt_secret
PYTHON_AI_URL=http://localhost:8010
AI_SERVICE_API_KEY=your_shared_internal_key
```

### Optional AI Service `.env`
Create `fintech-artha/ai-service/.env` only if you want separate service config:

```env
ENVIRONMENT=production
MONGODB_URI=mongodb+srv://<username>:<password>@<cluster>/<db>?appName=<app>
MONGO_DB_NAME=artha
MONGO_TLS_MODE=auto
AI_SERVICE_API_KEY=your_shared_internal_key
CACHE_TTL_SECONDS=300
MAX_UPLOAD_MB=5
```

### Install Once

1. Node backend
   ```bash
   cd /Users/vinayaksaindane/Desktop/fintech-artha
   npm install
   ```

2. Python AI service
   ```bash
   cd /Users/vinayaksaindane/Desktop/fintech-artha/ai-service
   python3 -m pip install -r requirements.txt
   ```

### Start Again

1. Start Node backend
   ```bash
   cd /Users/vinayaksaindane/Desktop/fintech-artha
   node src/index.js
   ```

2. Start Python AI service
   ```bash
   cd /Users/vinayaksaindane/Desktop/fintech-artha/ai-service
   PYTHONPATH=$PWD uvicorn app.main:app --host 0.0.0.0 --port 8010
   ```

### Quick Checks

1. Node backend
   ```bash
   curl http://localhost:8000/
   ```

2. Python AI service
   ```bash
   curl http://localhost:8010/
   ```

3. AI auth test
   ```bash
   curl -X POST http://localhost:8010/ai/debt-pulse \
     -H 'Content-Type: application/json' \
     -H 'x-api-key: your_shared_internal_key' \
     -d '{"income":50000,"total_emis":10000,"monthly_expenses":30000,"trend":"STABLE"}'
   ```

### Troubleshooting

1. `secretOrPrivateKey must have a value`
   `JWT_SECRET` is missing or backend was started without the backend `.env`.

2. `401 Unauthorized` from Python AI routes
   `AI_SERVICE_API_KEY` does not match between backend and AI service.

3. Frontend shows static AI results
   Node backend is falling back because Python AI service is down or rejecting requests.

4. `ModuleNotFoundError: No module named 'app'`
   Start uvicorn with `PYTHONPATH=$PWD` from the `ai-service` directory.

5. `SSL: CERTIFICATE_VERIFY_FAILED` when Python AI service connects to MongoDB Atlas
   Install the AI service requirements so `certifi` is available, then restart the service. The AI service now uses the `certifi` CA bundle automatically for Atlas-style URIs. If you need to force it explicitly, set `MONGO_TLS_MODE=enabled`.

---
*Developed with Node.js expertise for ARTH.*