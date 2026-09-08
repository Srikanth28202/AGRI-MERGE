# AgriSarathi AI — Agent Handbook (Session Bootstrap)

> **READ THIS FILE FIRST in every new session.** It contains everything needed to resume work without re-analyzing the codebase: how to run, repo map, verified facts, critical gotchas, audit gaps, and the prioritized improvement roadmap.

---

## 1. Project Identity

- **Name:** AgriSarathi AI (frontend package: `agrisarathi-frontend`)
- **What:** Intelligent crop recommendation + price prediction system for Indian farmers.
- **Features:** soil/crop recommendation, fertilizer guidance, growth guidance, WPI price prediction with SHAP explainability, price trend charts, profit calculator, multilingual chatbot, 10-language UI.
- **Context:** Final-year engineering project. Being prepared for presentation/evaluation. The user wants improvements that score well with evaluators (academic rigor, novelty, engineering professionalism).
- **Dev language/OS:** Python + React on **Windows / PowerShell 5.1**. Repo root: `E:\AGRI MERGE` (path has a space — always quote paths).
- **Not a git repo** (no `.git`); `.gitignore` exists anyway.

---

## 2. Quick Start (How to Run)

### Backend (FastAPI, port **8081**)
```powershell
# PowerShell, from the backend directory
& "backend\venv\Scripts\python.exe" -m uvicorn app.main:app --reload --port 8081
# OR from backend/ dir:
venv\Scripts\python.exe -m uvicorn app.main:app --reload
```
- Imports are `app.main`, `app.chatbot` → **must run from `backend\`**, not repo root.
- Server binds `0.0.0.0:8081` (see main.py:2276).
- CORS allows `http://localhost:5173`, `:3000`, `:3001` (main.py:1536–1538).

### Frontend (Vite, port **3000**)
```powershell
cd frontend
npm install
npm run dev        # http://localhost:3000  (NOTE: vite.config.js sets port 3000, NOT 5173)
npm run build      # production build (verified: OK, ~7.9s, 2742 modules)
```
- `frontend/src/api.js` → axios baseURL `http://127.0.0.1:8081`.

### Proven verification (used every session)
```powershell
# 1) Backend smoke: /predict with the saved payload (from repo root)
& "backend\venv\Scripts\python.exe" -c "import sys; sys.path.insert(0,'backend'); from fastapi.testclient import TestClient; from app.main import app; c=TestClient(app); import json; p=json.load(open('test_payload.json')); r=c.post('/predict', json=p); print(r.status_code); d=r.json(); print('price_history' in d, len(d.get('top_5_crops',[])))"

# 2) Price history endpoint
#    GET /price-history?crop=paddy  -> 200, 81 points
#    GET /price-history?crop=zzz    -> 404

# 3) Frontend build
cd frontend; npm run build
```
- `test_payload.json` (repo root) = verified payload: **KARNATAKA / BANGALORE RUR / MAY 2026** → 200 OK with `xai_breakdown`, `price_shap`, `price_history` on all 5 rows; recommended rice → paddy proxy price history.

---

## 3. Repo Map (verified via filesystem)

```
E:\AGRI MERGE\
├── AGENT_HANDBOOK.md          ← this file
├── README.md
├── REPORT.md                  ← project report (376 lines) — has STALE tech-stack table, no SDG section yet
├── Enhancment.txt             ← user notes
├── test_payload.json          ← verified /predict payload
├── .gitignore                 ← ignores node_modules, dist, __pycache__, .env, logs
│
├── backend\
│   ├── app\
│   │   ├── main.py            ← ~2370 lines, monolithic FastAPI app (ALL core logic)
│   │   ├── chatbot.py         ← 304 lines (was 281 — env loader added), separate chatbot router (/chat, /chat/status)
│   │   └── alerts.py          ← NEW ~590 lines — Farmer Message Alert System (standalone router /alerts/*)
│   ├── config\                ← EMPTY
│   ├── data\
│   │   ├── crops\             (crop dataset; model trained from these)
│   │   ├── prices\            ← 23 WPI CSVs (Arhar, Bajra, Barley, Copra, Cotton, Gram,
│   │   │                        Groundnut, Jowar, Jute, Maize, Masoor, Moong, Niger, Paddy,
│   │   │                        Ragi, Rape, Safflower, Sesamum, Soyabean, Sugarcane, Sunflower,
│   │   │                        Urad, Wheat) — source of get_price_history
│   │   └── rainfall\          (rainfall_normal.csv)
│   ├── models\
│   │   ├── crop\net.py        ← PyTorch net definition (Net_64_128_64)
│   │   └── price\             ← EMPTY (price models are trained IN-MEMORY at startup)
│   ├── services\price_service.py
│   ├── venv\                  ← local, non-portable
│   ├── requirements.txt       ← NOT pinned (ranges only), intentionally omits shap
│   └── err.log / out.log (+2..4)  ← startup logs from past runs
│
└── frontend\
    ├── package.json           ← React 18, Vite 5.4.21, Tailwind 3.4.1, recharts 2.12,
    │                            i18next 26, react-i18next 17, framer-motion 11, lucide-react,
    │                            axios, clsx, tailwind-merge, **react-router-dom 7.18**.
    │                            NO test framework installed.
    ├── vite.config.js         ← port 3000, CORS, /api proxy → 127.0.0.1:8081
    └── src\
        ├── main.jsx
        ├── App.jsx            ← BrowserRouter shell + layout (bg, Navbar, Routes, Footer).
        │                        Holds predict state (locations/results/error/loading) in App,
        │                        passes to PredictPage. NO dark-mode FAB; controls live in Navbar.
        ├── App.jsx.bak        ← STALE backup (old hardcoded axios baseURL) — delete candidate
        ├── api.js             ← axios, baseURL http://127.0.0.1:8081
        ├── i18n.js            ← react-i18next, all 10 locales registered in resources
        ├── index.css
        ├── pages\             ← ROUTER PAGES (added this session)
        │   ├── HomePage.jsx       `/`           Hero + Features (+ hash scroll for #features)
        │   ├── PredictPage.jsx    `/predict`    form ONLY (max-w-3xl centered)
        │   ├── ResultsPage.jsx    `/results`    dedicated results page (max-w-4xl, all panels)
        │   └── ChatPage.jsx       `/chat`       full-page chat (Chatbot fullPage variant)
        ├── components\        ← Chatbot, CropComparison, Features, Footer, Hero,
        │                        LanguageSwitcher, Navbar, PredictionForm, PriceChart,
        │                        ProfitCalculator, Results (11 files)
        ├── data\locationData.js
        ├── locales\           ← 10 complete JSON files (en,hi,kn,te,ta,ml,mr,gu,bn,pa)
        └── utils\resultsTranslations.js
```

---

## 4. Tech Stack (ACTUAL — verified, do not trust REPORT.md versions)

**Backend:** Python 3.x, FastAPI, Uvicorn, PyTorch (`torch`/`torch.nn`), scikit-learn (DecisionTreeRegressor), pandas, numpy, pydantic, httpx, python-dateutil, anyio, sniffio. **No shap, no numba, no tensorflow, no scipy-ML.** See `backend/requirements.txt`.

**Frontend:** React 18.2, Vite 5.4.21, Tailwind CSS 3.4.1, Framer Motion 11, Lucide icons, Axios, Recharts 2.12, i18next 26 + react-i18next 17, clsx + tailwind-merge. Build output: single JS chunk **956.63 kB (296.62 kB gzip)** → Vite >500 kB warning (expected, not fatal).

> REPORT.md's stack table says "Vite 4.x, TF/RandomForest, Pydantic 2.x" — **outdated**; actual is Vite 5, PyTorch, DecisionTreeRegressors. Update it during report work.

---

## 5. Backend Deep Dive (`backend/app/main.py`, ~2360 lines — a monolith)

### Endpoints (line numbers current as of last session)
| Method & Path | Line | Purpose |
|---|---|---|
| `GET /` | 1584 | health + model-loaded status |
| `GET /supported-crops` | 1604 | crop list |
| `GET /locations` | 1633 | states/districts |
| `POST /predict-crop` | 1662 | crop-only prediction |
| `POST /predict-price` | 1723 | price-only prediction |
| `GET /price-history?crop=` | 1765 | returns full historical WPI series for a crop (404 if unknown) |
| `POST /predict` | 1781 | **main unified endpoint** → `UnifiedPredictionOutput` incl. `price_history` |
| `POST /chatbot` | 2208 | **legacy/duplicate** chatbot (in main.py) — NOT used by frontend |
| `GET /chatbot/languages` | 2244 | 10-language list (matches frontend) — legacy |

### Farmer Message Alert System (`app/alerts.py`, standalone router)
| Method & Path | Purpose |
|---|---|
| `GET /alerts/status` | provider, farmer count, supported crops, background-running |
| `GET /alerts/crops` | crop list + sowing/harvest calendar (25 entries) |
| `POST /alerts/register` | register/fetch farmer (idempotent by phone) → `{farmer:{id,...}}` |
| `GET /alerts/farmers` | list all farmers |
| `GET /alerts/farmers/{id}` | single farmer profile (+ alert/unread counts) |
| `GET /alerts/farmers/{id}/alerts?unread=` | alert inbox (newest first, 100 max) |
| `POST /alerts/farmers/{id}/preferences` | update weather/market/farming prefs |
| `POST /alerts/alerts/{id}/read` / `.../dismiss` | mark read / hide |
| `POST /alerts/generate` | `{farmer_id?, force?}` — generate + deliver now (demo trigger) |
| `POST /alerts/send-test` | demo notification to any phone (lang-aware) |
| `GET /alerts/health` | data-file availability |
- **Alert types:** weather (live Open-Meteo forecast, no key, with IMD rainfall-normal fallback; thresholds for rain/temp), market (1m/3m WPI moves from `data/prices/*.csv`, drop ≤−5% / rise ≥8%), farming (sow/pre-harvest/harvest calendar reminders).
- **Delivery:** console provider by default (writes `[ALERT SMS → phone] …` to backend log = demo SMS). Real Twilio SMS if `TWILIO_ACCOUNT_SID/AUTH_TOKEN/FROM` set in `backend/.env` (REST via httpx, no SDK). `.env.example` documents them.
- **Localization:** alerts render in farmer's `language` (en/hi/kn templates, English fallback).
- **Persistence:** `data/alerts/farmers.json` (auto-created).
- **Scheduler:** daemon thread `alert-generator` started from `main.py` `@app.on_event("startup")` → first run +20s, then every 6h; dedup per farmer (weather 1d, other 6d); `force=true` bypasses dedup for demos.

### Chatbot has TWO implementations (confirmed duplication)
1. `backend/app/chatbot.py` — `router = APIRouter()`; `POST /chat` (132), `GET /chat/status` (230). Uses OpenRouter. **Frontend calls THIS one** (Chatbot.jsx hits `/chat` + `/chat/status`).
2. `class MultilingualChatbot` inside main.py (2031) + `/chatbot`, `/chatbot/languages` — **legacy duplicate not used by frontend**.

### Key classes (line numbers)
| Class | Line | Role |
|---|---|---|
| `CropExplainability` | 171 | XAI breakdown, soil analysis, growth guidance (rule-based scoring) |
| `Net_64_128_64` | 830 | PyTorch NN (input 7 → 41/42 outputs) — crop model architecture |
| `Commodity` | 851 | per-crop WPI model; trains its own `DecisionTreeRegressor` in-memory from CSV; `get_predicted_value` (870), `get_shap_values` (885), `get_price_history` (896), `get_crop_name` (907) |
| `ShapExplainer` | 920 | **dependency-free exact interventional SHAP** (combinatorial subset expectations over training/background data) — `explain(x)` (963). Do NOT replace with `shap` lib (uninstallable here). |
| `ModelManager` | 984 | loads everything at startup; `_load_models` (994); `predict_crop` (1138); `_predict_crop_rule_based` (1178); `predict_price` (1474) |
| `MultilingualChatbot` | 2031 | legacy in-main chatbot |

### Data flow — `POST /predict`
1. `ModelManager.predict_crop(...)` → if saved NN weights present, NN path; else **rule-based fallback** (returns flag "Crop model not found, using rule-based prediction").
2. Top crops ranked with `price_shap` from a `Commodity`/`ShapExplainer` per crop.
3. Recommended crop's full WPI series attached as `price_history` (dict with `points`).

### Verified `/predict` response structure (as of last session)
Top-level keys: `recommended_crop`, `confidence`, `predicted_price`, `price_available`, `explanation`, `soil_analysis`, `growth_advice`, `details`, `xai_breakdown`, `price_history`.
- The top-5 list is **`details.top_5_recommendations`** (NOT top-level `top_5_crops`). Each row: `rank`, `crop`, `confidence`, `predicted_price`, `price_method` (e.g. `proxy:paddy`), `price_available`, `is_proxy_price`, `price_shap` (`feature_names` + `values` + `expected_value`).

### Price models — IMPORTANT
- `backend/models/price/` is **empty**. The 23 price models are **trained in-memory at startup** from `data/prices/*.csv` (DecisionTreeRegressors). Nothing persisted.
- Crop model weights `models/crop/baseline_42crops.hdf5` + `encoder_42crops.pkl` are **referenced (main.py:1001,1011) but MISSING from disk** → that's why predict falls back to rule-based. File `models/crop/net.py` exists but weights do not. (This is why `crop_model_loaded` is false.)

### Known source inconsistencies (don't panic, just note)
- Module docstring (main.py:1–9) says "22 classes / 24 DecisionTreeRegressors" but reality is 42-crop encoder, 23 CSVs.
- Net is `(7, 41)` vs `encoder_42crops.pkl` → 42 crops.

---

## 6. Frontend Deep Dive

- **App.jsx** — `BrowserRouter` shell: Navbar, Routes, Footer, global bg gradient, floating chat shortcut (→ `/chat`), loading overlay. Holds predict state (`locations`/`results`/`error`/`loading`) and the `/predict` API call; **`handlePredict` navigates to `/results` on submit** (loading shows there). `ScrollToTop` on route change.
- **Routes:** `/` Home, `/predict` (form only), `/results` (all result panels), `/chat` (full-page chat). 404 → Home.
- **Pages (4):** `HomePage`, `PredictPage`, `ResultsPage`, `ChatPage` in `src/pages/`.
- **Navbar.jsx** — react-router `NavLink`s (Home / #features / Predict / Chat) with active pill; **theme toggle + `LanguageSwitcher` now live in the navbar** (no more floating FABs). CTA "Get Started" → `/predict`. Mobile menu includes theme + language.
- **Chatbot.jsx** — now supports a `fullPage` variant (`fullPage` + `onClose` props) used by `ChatPage`; floating-widget mode kept for compatibility but App no longer mounts it (replaced by floating shortcut → `/chat`).
- **Components (11):**
  - `PredictionForm.jsx` — soil/climate inputs (all select dropdowns for state/district/month/year).
  - `Results.jsx` (~581 lines) — renders prediction cards, `recommendedShap = top5[0]?.price_shap`, `PriceChart` when `price_history` present, always renders `ProfitCalculator`. Rendered inside `ResultsPage` at `max-w-4xl`.
  - `PriceChart.jsx` — WPI AreaChart (Recharts) + SHAP horizontal BarChart.
  - `ProfitCalculator.jsx` — acre stepper, revenue/cost/net estimate.
  - `Chatbot.jsx` — hits `/chat` + `/chat/status`; language-aware; OpenRouter + fallback.
  - `LanguageSwitcher.jsx` — 10 entries (en/hi/kn/te/ta/ml/mr/gu/bn/pa).
  - `Navbar`, `Hero`, `Features`, `CropComparison`, `Footer`.
- **i18n:** all 10 locale JSON files complete & valid (`ConvertFrom-Json` verified). `i18n.js` registers all 10 in `resources`. `PriceChart` + `ProfitCalculator` keys exist under `priceChart.*` / `profitCalculator.*`. New pages reuse existing keys (no new locale keys added).
- **api.js:** baseURL `http://127.0.0.1:8081`.
- `App.jsx.bak` = stale backup with old hardcoded URL (delete candidate).

---

## 7. ⚠️ Critical Gotchas (READ BEFORE RUNNING ANYTHING)

1. **torch before sklearn in main.py.** Import order at top (torch line 23, sklearn line 26) matters on this machine; swapping breaks startup. Preserve it.
2. **`shap` and `numba` cannot be pip-installed on this machine** (permanently blocked). The dependency-free `ShapExplainer` is the settled solution. **Never try to re-add `shap`.** `requirements.txt` intentionally omits it.
3. **Shell is Windows PowerShell 5.1.** Use `;` to chain (no `&&`). Always quote paths with spaces (`"E:\AGRISAARTHII\AGRI MERGE\..."`). Python = `backend\venv\Scripts\python.exe`.
4. **Backend must start from `backend\`** (imports are `app.main`, `app.chatbot`).
5. **Vite >500 kB chunk warning is expected** (956 kB). Not an error.
6. **Startup is slow/blocking**: torch, sklearn, pandas all import eagerly at load; `ModelManager._load_models` trains 23 price regressors at boot. Keep that in mind when testing (give it time) and when planning lazy-loading work.
7. **Don't commit secrets** — see Security below. `.gitignore` now excludes `.env`, `.env.*.local`, `node_modules`, `dist`, and **`venv/`** (added).

---

## 8. 🔴 Security Issues (URGENT — act before demo/push)

**Status: hardcoded key REMOVED from source ✅**
1. ~~Hardcoded live OpenRouter API key in `backend/app/chatbot.py`~~ → **FIXED.** Key removed from source. `chatbot.py` now reads `OPENROUTER_API_KEY` from the environment, falling back to `backend/.env` (gitignored) via a dependency-free loader (`_load_env_file`). `backend/.env.example` created as a template.
   - **⚠️ REMAINING USER ACTION (rotation):** the value in `backend/.env` is still the OLD exposed key. The user must go to https://openrouter.ai/keys, **revoke it**, generate a new one, paste it into `backend/.env`, and restart the backend. (Only the user can do this — requires dashboard access.)
   - Note: `main.py`'s legacy chatbot (line 2064) already read from `os.getenv` — it was not hardcoded.
2. **`.env` + `.env.example` now exist** in `backend/` (`.env` gitignored; `.env.example` committed-safe). `.env` contains the old key (kept so the app still works locally until rotation).
3. CORS is localhost-only — fine for dev, but frontend served from 5173 hits backend 8081; deployment will need CORS + `VITE_API_BASE` config.

---

## 9. Current Feature Status (implemented & verified)

- ✅ Rule-based crop prediction (NN weights missing → "Crop model not found, using rule-based prediction")
- ✅ 23 WPI price models (in-memory DecisionTreeRegressors)
- ✅ Dependency-free exact interventional SHAP (`ShapExplainer`) + per-crop `price_shap` + top-level `xai_breakdown`
- ✅ `GET /price-history` + `Commodity.get_price_history()` (returns full CSV series)
- ✅ `/predict` returns `price_history` for recommended crop
- ✅ `PriceChart.jsx` (trend + SHAP) & `ProfitCalculator.jsx` wired into `Results.jsx`
- ✅ Chatbot (OpenRouter + fallback) — hits `/chat`, `/chat/status`
- ✅ **10-language UI** (en, hi, kn, te, ta, ml, mr, gu, bn, pa) — all locale files complete & valid JSON, all registered
- ✅ **Multi-page UI (react-router-dom 7)** — `/`, `/predict`, `/results`, `/chat`, **`/alerts`**; results on a dedicated page (form-only Predict page); Navbar active states + integrated theme/language controls
- ✅ **Farmer Message Alert System** (`app/alerts.py` + `/alerts` AlertsPage) — farmer registration (phone/language/state/district/crops/prefs, JSON-persisted), weather alerts (live Open-Meteo + normals fallback), market alerts (WPI moves), farming calendar reminders, console demo SMS + optional Twilio, background generator every 6h, dedup, read/dismiss. `alerts.*` i18n added to **all 10 locales** + navbar link + features card. **Verified:** register→generate→list→read→test-SMS (en+hi+kn) all 200; thread runs; `npm run build` OK.
- ✅ Verified: `/predict` (test_payload.json) → 200 with all fields; `/price-history?crop=paddy` → 200/81 pts; `?crop=zzz` → 404; `npm run build` OK (2743 modules)

---

## 10. Audit: Known Gaps (verified — see roadmap for fixes)

| Gap | Evidence | Impact |
|---|---|---|
| **No tests at all** | no `test_*.py` / `*.test.js(x)` / `*.spec.js` anywhere outside node_modules/venv | credibility gap for evaluation |
| **No Docker** | no `Dockerfile` / `docker-compose*` | can't deploy easily |
| **No CI** | no `.github/workflows` | no quality gate |
| ~~No react-router~~ | **DONE this session** — routes `/`, `/predict`, `/results`, `/chat` | single-page limitation resolved |
| ~~Farmer Alert System~~ | **DONE this session** — `app/alerts.py` + `/alerts` page (weather/market/farming, console/Twilio SMS) | objective #6 completed |
| ~~Live weather API~~ | **PARTIAL** — live Open-Meteo forecast now used in `app/alerts.py` (cached, fallback to normals); NOT yet in `/predict` | weather alerts are real-time; prediction still static |
| **No `.env*`** | not even `.env.example` | hardcoded key risk, non-portable |
| **requirements.txt unpinned** | ranges only (`fastapi>=0.91.0`) | not reproducible |
| **venv not portable / not in .gitignore** | local venv, no pip freeze | needs `pip freeze > requirements.txt` |
| **Big single JS chunk** | 956.63 kB (296.62 kB gzip) | route splitting opportunity |
| **Blocking startup imports** | torch/TF/sklearn/pandas eager import at boot | slow start; lazy-load opportunity |
| **Monolithic main.py** | 2276 lines, all logic in one file | refactor opportunity |
| **Duplicate chatbot code** | main.py `/chatbot` vs chatbot.py `/chat` | consolidate |
| **Stale/duplicate files** | `App.jsx.bak`, stale REPORT.md stack table, stale module docstring | cleanup |
| **Crop model files missing** | weights referenced but absent | trained NN unavailable → rule-based only |

---

## 11. Improvement Roadmap (prioritized for final-year evaluation)

### 🔴 Tier 1 — Academic Rigor (highest scoring, medium effort)
1. **Proper ML methodology** — `notebooks/evaluation.ipynb` with: stratified 70/20/10 split (fixed seed), 5-fold CV (mean±std), model comparison table (majority baseline vs DT vs RF vs XGBoost vs NN) with acc/precision/recall/F1, `GridSearchCV` tuning, learning curves, confusion matrix + class-wise F1 (dataset may be imbalanced → class weights), and for price models: MAE/RMSE/R² + naive baseline ("predict last year") to prove it beats simple forecasting.
2. **Quantified problem statement** in report intro — e.g., "~140M+ Indian farming households; avg monthly farm income ~₹10,000 (NSSO 2021); crop-loss cost of poor selection". Statistics make the project defensible.
3. **Reproducibility** — pin versions, set and document seed everywhere.

### 🟠 Tier 2 — Novelty / Differentiators
4. **RAG chatbot** (chatbot from "LLM wrapper" → grounded retrieval): small vector store (FAISS/ChromaDB) over agronomy knowledge + own `data/`; chat answers cite your dataset. High innovation credit, low cost.
5. **Live data APIs** — Open-Meteo weather already wired in the **alerts** module (roadmap item partly done); next: route live weather into `/predict` itself, and Agmarknet/API for real mandi prices feeding the price chart. Converts demo from "looks real" → "real-time".
6. **Stronger price model** — SARIMA or LSTM with seasonal decomposition on extended (2024) data; stationarity tests, ACF/PACF. Classic thesis material.
7. **Optional wow: crop disease detection** — transfer-learn MobileNet/EfficientNet on PlantVillage; photo-upload demo.
8. **Deliver alert objective end-to-end** — add real Twilio creds to `.env` for demo SMS; consider SMS gateway batching + an admin "send to all farmers" endpoint (manual `POST /alerts/generate` exists).

### 🟡 Tier 3 — Engineering Professionalism
8. **Refactor 2276-line main.py** into `routers/`, `services/`, `models/`, `schemas/`.
9. **Add tests** — pytest for `ShapExplainer`, price history, `/predict`, `/price-history` (TestClient already works); frontend Vitest/RTL.
10. **Docker + deploy** — docker-compose backend+frontend; deploy backend to Render/Railway, frontend to Vercel/Netlify; a **live URL** in report/demo.
11. **CI/CD + secrets** — GitHub Actions running pytest + `npm build`; `OPENROUTER_API_KEY` → `.env`.

### 🟢 Tier 4 — Presentation & Report
12. **Literature review** — Breiman RF 2001, Lundberg & Lee SHAP 2017, recent agri-AI papers.
13. **Comparison table vs existing systems** (mKisan, Kisan Suvidha, CropIn, Plantix) — 2–3 columns showing your differentiators (explainability, multilingual, free, offline-capable).
14. **Honest Limitations + Future Work** sections matching Tier 2 ideas.
15. **Surface SHAP work prominently** — explainable AI is a current research trend; dependency-free implementation is genuinely non-trivial.

### Suggested order if time is short
```
1. Tests + .env + pinned requirements                 (1 day — fixes credibility)
2. Evaluation notebook w/ cross-val + baselines       (1-2 days — fixes rigor)
3. Live weather/mandi API integration                 (1-2 days — biggest demo impact)
4. RAG chatbot                                        (2-3 days — strongest novelty)
5. Docker + deploy + live URL                         (1 day — demo polish)
```

---

## 12. SDG Mapping (prepared for REPORT.md — not yet written in)

**Direct targets:**
- **SDG 1 (No Poverty)** — higher crop selection success → income stability for smallholders (esp. marginal farmers).
- **SDG 2 (Zero Hunger)** — better yields via correct crop/fertilizer/water guidance.
- **SDG 8 (Decent Work & Economic Growth)** — price prediction + profit calculator improves farm profitability & market decisions.
- **SDG 12 (Responsible Consumption & Production)** — data-driven input use (fertilizer NPK) reduces waste/overuse.
- **SDG 13 (Climate Action)** — climate-aware recommendation (temp/rainfall) → resilient, adaptive farming.

**Indirect support:** SDG 3 (well-being via income security), 5 (gender: women farmers in agri labor force), 6 (water-conscious crop choice), 9 (innovation/infrastructure), 10 (reduced inequality, smallholder inclusion), 15 (sustainable land use), 17 (partnerships/data).

---

## 13. Work History Log (recent session highlights)

- Built **dependency-free exact interventional SHAP** (`ShapExplainer`, main.py:920) — replaces `shap` lib (uninstallable here). `Commodity.get_shap_values()` at main.py:885.
- Added `Commodity.get_price_history()` (main.py:896) + `GET /price-history` (1765).
- `/predict` now returns per-crop `price_shap` + top-level `price_history` via `UnifiedPredictionOutput.price_history`.
- Frontend: created `PriceChart.jsx` (WPI AreaChart + SHAP BarChart) and `ProfitCalculator.jsx` (acre stepper, revenue/cost/net); wired both into `Results.jsx`.
- i18n: added `priceChart.*` + `profitCalculator.*` keys; **created all 10 locale files complete** (bn, gu, mr, pa created fresh this round; others completed); all registered in `i18n.js` + `LanguageSwitcher.jsx`.
- Verified everything (see §2). `npm run build` OK.
- SDG narrative elaborated at chat level (§12), not yet written to REPORT.md.
- Last deliverable: **gap audit** (§10) + prioritized roadmap (§11) — no implementation started from it yet.
- **This session:** Multi-page UI. Installed `react-router-dom@7.18`; created `src/pages/` (HomePage, PredictPage, ResultsPage, ChatPage); App.jsx is now a BrowserRouter shell; **predict form → `/results` on submit** (form no longer shares the page with results); Navbar rewritten with NavLinks + integrated theme/language controls; Chatbot gained a `fullPage` variant; Footer links converted to routes (docs port fixed 8080→8081). Both servers run (backend 8081, vite 3000). Handbook path corrected to `E:\AGRI MERGE`.
- **This session (round 2):** Implemented the **Farmer Message Alert System** (objective #6 — previously the single unimplemented objective). Backend: new `app/alerts.py` (self-contained, no main imports) with farmer registry (JSON), weather/market/farming alert builders, console+Twilio providers, 12 `/alerts/*` endpoints, background generator thread wired via `main.py` startup hook. Frontend: new `AlertsPage.jsx` (`/alerts` route, navbar link + features card), full `alerts.*` i18n in all 10 locales. Verified: full backend smoke (register/generate/read/test-sms, en+hi+kn), startup thread alive, `npm run build` OK (2743). Test data cleaned after verification.

---

## 14. Report/Docs Status

- `REPORT.md` — 376 lines: has Executive Summary, Objectives, System Architecture, Tech Stack (**stale versions**), etc. **Missing:** SDG section (§12), literature review, methodology/evaluation (§11 items 1–2), limitations/future work, comparison table, latest features (SHAP/price chart/profit calculator/10 languages) documented.
- `README.md` — exists (assume basic run instructions; verify before demo).
- `Enhancment.txt` — user's own notes.

---

## 15. Open Decisions (ask the user if relevant)

- Which roadmap items to implement next (default suggestion: start with **#1 tests + .env + pinned requirements** and **#2 evaluation notebook**).
- Whether to rotate/revoke the exposed OpenRouter key (recommended) and move it to `.env`. **DONE (partially):** key moved to `backend/.env`; only remaining step is user rotation at https://openrouter.ai/keys.
- Whether the project should become a git repo (for CI/CD work).
- Whether to write the SDG section into REPORT.md now.
