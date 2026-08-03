# AgriSarathi - AI-Powered Crop Intelligence Platform

A unified crop recommendation and price prediction system with a modern React frontend and FastAPI backend.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 18+
- npm or yarn

### Backend Setup

```bash
cd backend
pip install -r requirements.txt

# Set your OpenRouter API key for AI chatbot (optional)
$env:OPENROUTER_API_KEY="your-api-key"

# Run the server
python app/main.py
```

Backend will start on `http://localhost:8081`

**Note:** The backend uses rule-based crop prediction as a fallback when ML model files are not present. Price prediction works with the CSV data files in `backend/data/prices/`.

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend will start on `http://localhost:3000` (or next available port if 3000 is busy)

## 📁 Project Structure

```
AGRI MERGE/
├── backend/                 # FastAPI Backend
│   ├── app/
│   │   └── main.py         # Main API application
│   ├── data/
│   │   ├── rainfall/       # Rainfall data
│   │   ├── prices/         # Crop price CSV files
│   │   └── crops/          # Crop recommendation data
│   ├── models/             # ML model files
│   │   └── crop/
│   │       └── net.py      # Neural network definition
│   ├── services/           # Business logic
│   ├── config/             # Configuration files
│   └── requirements.txt    # Python dependencies
│
├── frontend/               # React + Vite Frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   │   ├── Chatbot.jsx
│   │   │   ├── Features.jsx
│   │   │   ├── Footer.jsx
│   │   │   ├── Hero.jsx
│   │   │   ├── Navbar.jsx
│   │   │   ├── PredictionForm.jsx
│   │   │   └── Results.jsx
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── index.html
│
└── README.md
```

## 🔧 Features

- **Crop Recommendation**: AI-powered crop suggestions based on soil parameters, location, and climate
- **Price Prediction**: Forecast crop prices using historical data
- **AI Chatbot**: Multilingual farming assistant (11 Indian languages)
- **XAI Explanations**: Understand why specific crops are recommended
- **Modern UI**: Responsive design with dark mode support

## 🛠️ Tech Stack

**Backend:**
- FastAPI
- PyTorch (Neural Network)
- scikit-learn (Price Prediction)
- Pandas & NumPy

**Frontend:**
- React 18
- Vite
- Tailwind CSS
- Framer Motion
- Axios

## 📚 API Endpoints

- `GET /` - API info
- `GET /locations` - Get states and districts
- `POST /predict` - Get crop recommendation and price prediction
- `POST /chatbot` - AI chatbot endpoint

## 🔐 Environment Variables

Backend (optional):
- `OPENROUTER_API_KEY` - For AI chatbot features

## 📝 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- Crop recommendation model trained on Indian agricultural data
- Price prediction using historical commodity prices
- Climate data from Indian meteorological sources

---

## 🔧 System Status & Fixes Applied

### Issues Found and Fixed:

1. **Backend Model Loading Error**
   - **Issue:** `NameError: name 'CROP_MODEL_PATH' is not defined`
   - **Fix:** Made ML model loading optional with try/except, added rule-based fallback for crop prediction when model files are missing

2. **Missing crop_encoder References**
   - **Issue:** Multiple endpoints (`/supported-crops`, `/predict-crop`, `/predict`) failed when `crop_encoder` was None
   - **Fix:** Added null checks and fallback crop lists for all endpoints

3. **Frontend-Backend Data Mismatch**
   - **Issue:** Frontend expected `details.environmental_data.temperature` but backend returned `temperature_celsius`
   - **Fix:** Updated frontend Results.jsx to use correct field names (`temperature_celsius`, `humidity_percent`, `rainfall_mm`)

4. **Frontend Response Structure**
   - **Issue:** Frontend expected nested `details.xai_explanation` but backend returned flat fields
   - **Fix:** Updated frontend to match backend response structure (explanation, soil_analysis, growth_advice at top level)

5. **Price Display in Top 5**
   - **Issue:** Frontend used `crop.price` but backend returns `crop.predicted_price`
   - **Fix:** Updated Results.jsx to use correct field name

### Current System State:

- **Backend:** ✅ Runs without errors, uses rule-based crop prediction (ML models optional), price prediction works with CSV data
- **Frontend:** ✅ API calls fixed, JSON structure aligned, error handling in place
- **Integration:** ✅ Ready for end-to-end testing

### Files Modified:

**Backend:**
- `backend/app/main.py` - Added fallback for missing ML models, fixed all crop_encoder references

**Frontend:**
- `frontend/src/components/Results.jsx` - Fixed field names, response structure alignment

**Cleanup:**
- Removed: `backend.log`, `backend_err.log`, `backend_out.log`, `backend_run.log`, `dev_output.txt`, `frontend.log`, `start_server.bat`
- Removed: `crop-prediction/` folder, `CLEANUP_ANALYSIS.md`, `PROJECT_SUMMARY.md`, `QUICK_START.md`, `README_UNIFIED.md`
