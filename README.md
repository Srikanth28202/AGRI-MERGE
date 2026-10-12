# AgriSarathi AI — AI-Powered Crop Intelligence Platform

AgriSarathi AI is a web platform that helps Indian farmers make smarter decisions — **which crop to grow, what price to expect, how to guide it to harvest, and when to act** — using machine learning, live weather and market data.

Built with a **React (Vite) front-end** and a **FastAPI (PyTorch) back-end**, it ships a trained neural crop model, price forecasting, an AI farming chatbot, and a real messaging/alert system over Telegram.

---

## ✨ Features

- 🌱 **Crop Recommendation** — trained PyTorch neural network (`Net_64_128_64`) classifies the best crop among **41 crops** from soil (N-P-K, pH) + location + season, with a rule-based fallback.
- 💰 **Price Prediction** — per-commodity `DecisionTreeRegressor` models forecast WPI-based prices in ₹/quintal (23 commodities), plus live latest-WPI updates.
- 📈 **Growth Guidance** — week-by-week planting → harvest advice with environmental data.
- 🧠 **Explainable AI** — dependency-free SHAP-style explanations of why a crop was recommended.
- 🤖 **AI Chatbot** — OpenRouter cloud LLM with an agriculture system prompt, plus a multilingual rule-based fallback.
- 📲 **Alerts & Messaging** — background alert engine (every 6h) delivers **weather, market (WPI) and farming-calendar** alerts to farmers via **Telegram** (free, reliable), with CallMeBot WhatsApp / Fast2SMS / Twilio as alternates.
- 🌍 **Multilingual** — full UI + chatbot in **10 languages** (English, Hindi, Tamil, Telugu, Kannada, Malayalam, Marathi, Gujarati, Bengali, Punjabi).

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.10+** and Node.js **18+**
- Python packages installed in a virtual environment (`pip install -r requirements.txt`)

### 1) Backend
```bash
cd backend
python -m venv venv                 # already done in this repo
venv\Scripts\activate
pip install -r requirements.txt

# Optional: copy env template and add your keys
copy .env.example .env

# Run the API server
python -m uvicorn app.main:app --port 8081
```
Backend starts at **http://localhost:8081** — interactive API docs at **http://localhost:8081/docs**.

### 2) Frontend
```bash
cd frontend
npm install
npm run dev
```
Frontend starts at **http://localhost:3000**. The Vite dev server proxies `/api/*` → `http://127.0.0.1:8081` (strips the `/api` prefix), so the UI works out of the box.

---

## 🔐 Environment Variables (`backend/.env`)

| Variable | Purpose | Required |
|---|---|---|
| `OPENROUTER_API_KEY` | Powers the AI chatbot (free key from openrouter.ai/keys) | for AI chat |
| `OPENROUTER_MODEL` | Chat model id (default: a current free-tier model) | optional |
| `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` | Real alert delivery via Telegram bot (create with @BotFather) | for alerts |
| `CALLMEBOT_PHONE` / `CALLMEBOT_API_KEY` | WhatsApp via CallMeBot | optional |
| `FAST2SMS_API_KEY` | SMS via Fast2SMS | optional |
| `TWILIO_ACCOUNT_SID` / `TWILIO_AUTH_TOKEN` / `TWILIO_FROM` | SMS via Twilio | optional |

Provider priority: **Telegram → CallMeBot → Fast2SMS → Twilio → console log**. With no keys set, the app runs fully except real delivery (alerts are written to the backend log).

> The chatbot degrades gracefully: without a key (or on API errors) it uses the built-in multilingual rule-based fallback instead of crashing.

---

## 📁 Project Structure

```
AGRI MERGE/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI app: crop/price/growth/explainability APIs
│   │   ├── chatbot.py        # AI chatbot (OpenRouter) + rule-based fallback
│   │   └── alerts.py         # Alert engine + Telegram/Fast2SMS/CallMeBot/Twilio providers
│   ├── data/
│   │   ├── rainfall/         # District rainfall normals (IMD)
│   │   ├── prices/           # WPI commodity price CSVs
│   │   └── crops/            # Training dataset (crop_recommendation.csv, 41 crops)
│   ├── models/crop/          # Trained artifacts: state_dict (.hdf5), encoder, normalization
│   ├── train_crop_model.py   # Crop NN trainer (Net_64_128_64; ~90% val. accuracy)
│   ├── send_test.py          # One-off alert delivery tester
│   ├── requirements.txt
│   ├── .env / .env.example
│   └── test_payload.json     # Sample /predict request
│
├── frontend/                 # React + Vite
│   ├── src/
│   │   ├── pages/            # Home, Prediction, Chatbot, Alerts pages
│   │   ├── components/       # Hero, Navbar, PredictionForm, Results, ...
│   │   ├── locales/          # i18next translations (10 languages)
│   │   ├── App.jsx / main.jsx
│   │   └── index.css
│   ├── package.json
│   └── vite.config.js        # Dev server + /api proxy to :8081
│
├── REPORT.md                 # Project report (objectives, tech stack, SDGs)
└── README.md
```

---

## 🔁 How the Alert System Works

1. On startup a background thread runs every **6 hours**.
2. For every **registered farmer** it checks three triggers:
   - **Weather** — live Open-Meteo forecast (rain/temperature risk) for their district
   - **Market** — WPI price move for their crops
   - **Farming** — crop-calendar reminders (sowing / harvest windows)
3. Alerts are **deduplicated** per type (`dedup_key`) so none are repeated every cycle.
4. Each alert is delivered to the configured channel (Telegram by default) and stored in the farmer's inbox.

Register a farmer and trigger a run:
```bash
curl -X POST http://localhost:8081/alerts/register \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"Nisha\",\"phone\":\"+91 90000 00000\",\"state\":\"KARNATAKA\",\"district\":\"BANGALORE RUR\",\"crops\":[\"paddy\"]}"

curl -X POST http://localhost:8081/alerts/generate -H "Content-Type: application/json" -d "{\"force\":true}"
```

---

## 📚 API Endpoints

**Core**
| Method | Path | Description |
|---|---|---|
| GET | `/` | API info |
| GET | `/locations` | Supported states & districts |
| GET | `/supported-crops` | Crops the model can predict |
| POST | `/predict` | Unified crop recommendation + price + growth advice (N, P, K, pH, state, district, month) |
| POST | `/predict-crop` | Crop prediction only |
| POST | `/predict-price` | WPI price forecast for a commodity |
| GET | `/price-history` | Historical price series |
| POST | `/chat` | AI chatbot message |
| GET | `/chat/status` | Chatbot mode (ai / fallback) + model |

**Alerts**
| Method | Path | Description |
|---|---|---|
| GET | `/alerts/status` | System status (active provider, farmers, crops) |
| POST | `/alerts/register` | Register a farmer for alerts |
| GET | `/alerts/farmers` | List registered farmers |
| POST | `/alerts/generate` | Generate + deliver alerts (all farmers or one) |
| POST | `/alerts/send-test` | Send a test message via the active provider |
| GET | `/alerts/health` / `/alerts/crops` | Health + crop-calendar info |

Full interactive list: **http://localhost:8081/docs**.

---

## 🛠️ Tech Stack

**Backend**
- FastAPI + Uvicorn + Pydantic
- PyTorch (crop neural network)
- scikit-learn (DecisionTreeRegressor price models)
- Pandas, NumPy
- httpx (OpenRouter, Telegram, weather, SMS APIs)

**Frontend**
- React 18 + Vite 5
- Tailwind CSS, Framer Motion
- Recharts (price charts)
- react-i18next (10 languages)
- Axios

---

## 📝 License

MIT License — see the `LICENSE` file for details.

## 🙏 Acknowledgments

- Crop dataset (UCI crop recommendation, 4,100 samples / 41 labels)
- WPI commodity prices (Ministry of Consumer Affairs / OGD)
- Rainfall normals from IMD data
- Open-Meteo (keyless weather forecasts) & OpenRouter (free LLM access)