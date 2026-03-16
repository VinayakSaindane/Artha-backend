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


lsof -ti :8000 | xargs kill -9

cd /Users/vinayaksaindane/Desktop/fintech-artha/ai-service
source ../.venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8010