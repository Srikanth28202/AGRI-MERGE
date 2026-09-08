"""
Farmer Message Alert System Module
==================================
Self-contained alert engine for AgriSarathi AI.

Delivers timely SMS/in-app notifications on:
  1. Weather updates      - live Open-Meteo forecast (free, no key) with
                            static IMD rainfall-normal fallback.
  2. Market information   - WPI price-move detections from data/prices/*.csv.
  3. Farming activities   - crop calendar reminders (sowing / harvest).

Persistence: farmer registry stored as JSON in data/alerts/farmers.json.
Delivery   : console provider (demo) by default; real Twilio SMS when
             TWILIO_* variables are present in backend/.env.
Localization: alerts are generated in the farmer's registered language
             (en / hi / kn supported, English fallback).
"""

import json
import logging
import os
import threading
import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx
import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter()

# ============================================================================
# Paths & configuration
# ============================================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
PRICE_DATA_DIR = os.path.join(DATA_DIR, "prices")
RAINFALL_PATH = os.path.join(DATA_DIR, "rainfall", "rainfall_normal.csv")
ALERT_DATA_DIR = os.path.join(DATA_DIR, "alerts")
FARMERS_FILE = os.path.join(ALERT_DATA_DIR, "farmers.json")


def _load_env_file(path: str) -> dict:
    """Minimal .env loader (no external dependency)."""
    env = {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                env[key.strip()] = value.strip().strip('"').strip("'")
    except OSError:
        pass
    return env


_ENV = _load_env_file(os.path.join(BASE_DIR, ".env"))

TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", _ENV.get("TWILIO_ACCOUNT_SID", ""))
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", _ENV.get("TWILIO_AUTH_TOKEN", ""))
TWILIO_FROM = os.environ.get("TWILIO_FROM", _ENV.get("TWILIO_FROM", ""))

# ============================================================================
# Alert thresholds
# ============================================================================

MONSOON_MONTHS = {6, 7, 8, 9}
HEAVY_RAIN_MM = 80.0          # 7-day forecast precipitation threshold
TEMP_HOT_THRESHOLD = 37.0     # max temperature heat-stress threshold (°C)
TEMP_COLD_THRESHOLD = 5.0     # min temperature frost threshold (°C)
PRICE_DROP_PCT = -5.0         # 1-month WPI fall warning threshold (%)
PRICE_RISE_PCT = 8.0          # 1-month WPI rise info threshold (%)
GENERATION_INTERVAL_HOURS = 6
DEDUP_WINDOW_DAYS = {"weather": 1, "market": 6, "farming": 6}

_MONTH_SHORT = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# ============================================================================
# Crop calendar (sowing / harvest months as integers 1-12)
# ============================================================================

CROP_CALENDAR: Dict[str, Dict[str, List[int]]] = {
    "paddy": {"sowing": [6, 7], "harvest": [10, 11]},
    "wheat": {"sowing": [11, 12], "harvest": [3, 4]},
    "maize": {"sowing": [6, 7], "harvest": [10, 11]},
    "cotton": {"sowing": [5, 6], "harvest": [10, 11]},
    "rice": {"sowing": [6, 7], "harvest": [10, 11]},
    "sugarcane": {"sowing": [2, 3], "harvest": [11, 12]},
    "groundnut": {"sowing": [6, 7], "harvest": [10, 11]},
    "bajra": {"sowing": [6, 7], "harvest": [9, 10]},
    "jowar": {"sowing": [6, 7], "harvest": [10, 11]},
    "barley": {"sowing": [11, 12], "harvest": [3, 4]},
    "gram": {"sowing": [10, 11], "harvest": [2, 3]},
    "chickpea": {"sowing": [10, 11], "harvest": [2, 3]},
    "arhar": {"sowing": [6, 7], "harvest": [12, 1]},
    "moong": {"sowing": [6, 7], "harvest": [8, 9]},
    "masoor": {"sowing": [10, 11], "harvest": [3, 4]},
    "urad": {"sowing": [6, 7], "harvest": [9, 10]},
    "ragi": {"sowing": [6, 8], "harvest": [10, 12]},
    "soyabean": {"sowing": [6, 7], "harvest": [10, 11]},
    "sunflower": {"sowing": [6, 7], "harvest": [10, 11]},
    "safflower": {"sowing": [10, 11], "harvest": [3, 4]},
    "niger": {"sowing": [6, 7], "harvest": [9, 10]},
    "rape": {"sowing": [10, 11], "harvest": [3, 4]},
    "sesamum": {"sowing": [6, 7], "harvest": [9, 10]},
    "copra": {"sowing": [1], "harvest": []},   # perennial – no harvest reminders
    "jute": {"sowing": [4, 5], "harvest": [8, 9]},
}

# Aliases from crop names (frontend/product-level) to price CSV files.
_CROP_CSV_ALIASES = {
    "rice": "Paddy.csv",
    "chickpea": "Gram.csv",
    "mungbean": "Moong.csv",
    "pigeonpeas": "Arhar.csv",
    "blackgram": "Urad.csv",
    "kidneybeans": "Arhar.csv",
    "lentil": "Masoor.csv",
    "mothbeans": "Moong.csv",
    "coconut": "Copra.csv",
}


def _csv_for_crop(crop: str) -> Optional[str]:
    name = crop.strip().lower()
    if name in _CROP_CSV_ALIASES:
        return _CROP_CSV_ALIASES[name]
    fallback = f"{name.capitalize()}.csv"
    if os.path.exists(os.path.join(PRICE_DATA_DIR, fallback)):
        return fallback
    for f in os.listdir(PRICE_DATA_DIR):
        if f.lower() == f"{name}.csv":
            return f
    return None


# ============================================================================
# Localized message templates (en / hi / kn, English fallback)
# ============================================================================

TITLES = {
    "weather": {"en": "Weather Alert", "hi": "मौसम अलर्ट", "kn": "ಹವಾಮಾನ ಎಚ್ಚರಿಕೆ"},
    "market": {"en": "Market Update", "hi": "बाज़ार अपडेट", "kn": "ಮಾರುಕಟ್ಟೆ ಅಪ್ಡೇಟ್"},
    "farming": {"en": "Farming Reminder", "hi": "खेती सलाह", "kn": "ಕೃಷಿ ಜ್ಞಾಪನೆ"},
}

MESSAGES = {
    "weather_heavy_rain": {
        "en": "Heavy rain expected in {district} over the next 7 days (~{mm:.0f} mm). Clear drainage channels and postpone chemical sprays.",
        "hi": "अगले 7 दिनों में {district} में भारी बारिश की संभावना (~{mm:.0f} मिमी)। जल निकासी साफ रखें और छिड़काव स्थगित करें।",
        "kn": "ಮುಂದಿನ 7 ದಿನಗಳಲ್ಲಿ {district} ನಲ್ಲಿ ಭಾರಿ ಮಳೆ ನಿರೀಕ್ಷೆ (~{mm:.0f} ಮಿ.ಮೀ). ಬಚ್ಚಲು ಚಾನೆಲ್ ಸ್ವಚ್ಛಗೊಳಿಸಿ, ಸಿಂಪಡಣೆ ಮುಂದೂಡಿ.",
    },
    "weather_heat": {
        "en": "Heat wave: up to {temp:.0f}°C expected in {district}. Irrigate early morning or evening and shade young plants.",
        "hi": "गर्मी की लहर: {district} में तापमान {temp:.0f}°C तक जा सकता है। सुबह या शाम सिंचाई करें और नए पौधों को छाया दें।",
        "kn": "ಶಾಖದ ಅಲೆ: {district} ನಲ್ಲಿ {temp:.0f}°C ವರೆಗೂ ತಾಪಮಾನ ನಿರೀಕ್ಷೆ. ಬೆಳಿಗ್ಗೆ/ಸಂಜೆ ನೀರಾವರಿ, ಎಳೆಯ ಬೆಳೆಗೆ ನೆರಳು ಒದಗಿಸಿ.",
    },
    "weather_cold": {
        "en": "Cold spell: minimum {temp:.0f}°C in {district}. Protect seedlings with mulch and avoid early-morning irrigation.",
        "hi": "ठंड: {district} में न्यूनतम तापमान {temp:.0f}°C। पौधों को मल्च से सुरक्षित रखें और सुबह सिंचाई से बचें।",
        "kn": "ಚಳಿ: {district} ನಲ್ಲಿ ಕನಿಷ್ಠ {temp:.0f}°C. ಮೊಳಕೆಗಳಿಗೆ ಮಲ್ಚ್ ಹಾಕಿ, ಮುಂಜಾನೆ ನೀರಾವರಿ ಮಾಡಬೇಡಿ.",
    },
    "weather_monsoon": {
        "en": "Monsoon active in {district} — ideal for kharif sowing. Keep seedbeds ready and watch for waterlogging.",
        "hi": "{district} में मानसून सक्रिय है — खरीफ बुवाई के लिए उपयुक्त समय। बीज क्यारियाँ तैयार रखें और जलभराव पर ध्यान दें।",
        "kn": "{district} ನಲ್ಲಿ ಮಳೆಗಾಲ ಸಕ್ರಿಯ — ಖಾರಿಫ್ ಬಿತ್ತನೆಗೆ ಸೂಕ್ತ. ಸೀಡ್ಬೆಡ್ ಸಿದ್ಧವಿಡಿ, ನೀರು ನಿಲ್ಲುವುದನ್ನು ಗಮನಿಸಿ.",
    },
    "weather_dry": {
        "en": "Low rainfall expected in {district} in the coming week. Plan irrigation and water-saving (drip) methods.",
        "hi": "आने वाले सप्ताह में {district} में कम बारिश की संभावना। सिंचाई और ड्रिप (जल-बचत) विधियों की योजना बनाएं।",
        "kn": "ಮುಂದಿನ ವಾರ {district} ನಲ್ಲಿ ಕಡಿಮೆ ಮಳೆ ನಿರೀಕ್ಷೆ. ನೀರಾವರಿ ಮತ್ತು ನೀರು-ಉಳಿತಾಯ (ಹನಿ) ವಿಧಾನ ಯೋಜಿಸಿ.",
    },
    "market_drop": {
        "en": "Price drop: {crop} fell {pct:.1f}% in one month (latest WPI {price:.1f}). Consider holding stock if storage is possible.",
        "hi": "कीमत में गिरावट: {crop} एक महीने में {pct:.1f}% गिरा (नवीनतम WPI {price:.1f})। संभव हो तो स्टॉक रखने पर विचार करें।",
        "kn": "ಬೆಲೆ ಕುಸಿತ: {crop} ಒಂದು ತಿಂಗಳಲ್ಲಿ {pct:.1f}% ಕುಸಿದಿದೆ (ಇತ್ತೀಚಿನ WPI {price:.1f}). ಶೇಖರಣೆ ಸಾಧ್ಯವಾದರೆ ಸ್ಟಾಕ್ ಹಿಡಿದಿಡಿ.",
    },
    "market_rise": {
        "en": "Good news: {crop} price rose {pct:.1f}% in one month (latest WPI {price:.1f}). Now may be a good time to sell.",
        "hi": "अच्छी खबर: {crop} की कीमत एक महीने में {pct:.1f}% बढ़ी (नवीनतम WPI {price:.1f})। अभी बेचना लाभदायक हो सकता है।",
        "kn": "ಶುಭ ಸುದ್ದಿ: {crop} ಬೆಲೆ ಒಂದು ತಿಂಗಳಲ್ಲಿ {pct:.1f}% ಏರಿದೆ (ಇತ್ತೀಚಿನ WPI {price:.1f}). ಈಗ ಮಾರಾಟಕ್ಕೆ ಒಳ್ಳೆಯ ಸಮಯ.",
    },
    "market_update": {
        "en": "{crop} latest WPI is {price:.1f} ({pct:+.1f}% in a month). Plan your selling window.",
        "hi": "{crop} का नवीनतम WPI {price:.1f} है (महीने में {pct:+.1f}%)। अपनी बिक्री अवधि की योजना बनाएं।",
        "kn": "{crop} ಇತ್ತೀಚಿನ WPI {price:.1f} (ತಿಂಗಳಲ್ಲಿ {pct:+.1f}%). ಮಾರಾಟ ಸಮಯ ಯೋಜಿಸಿ.",
    },
    "farming_sow": {
        "en": "It's sowing time for {crop}. Prepare the field, check soil moisture and complete seed treatment.",
        "hi": "{crop} की बुवाई का समय है। खेत तैयार करें, मिट्टी की नमी जांचें और बीज उपचार पूरा करें।",
        "kn": "{crop} ಬಿತ್ತನೆ ಸಮಯ. ಹೊಲ ಸಿದ್ಧಗೊಳಿಸಿ, ಮಣ್ಣಿನ ತೇವಾಂಶ ಪರೀಕ್ಷಿಸಿ, ಬೀಜ ಸಂಸ್ಕರಣೆ ಮುಗಿಸಿ.",
    },
    "farming_prepare_harvest": {
        "en": "{crop} harvest is approaching (expected in {months}). Prepare storage, labour and drying space.",
        "hi": "{crop} की कटाई नजदीक है (अपेक्षित: {months})। भंडारण, श्रम और सुखाने की जगह तैयार करें।",
        "kn": "{crop} ಸುಗ್ಗಿ ಹತ್ತಿರದಲ್ಲಿದೆ (ನಿರೀಕ್ಷೆ: {months}). ಶೇಖರಣೆ, ಕೂಲಿ ಮತ್ತು ಒಣಗಿಸುವ ಜಾಗ ಸಿದ್ಧಗೊಳಿಸಿ.",
    },
    "farming_harvest": {
        "en": "Harvest window for {crop} is open. Finish harvesting at the right moisture to avoid losses.",
        "hi": "{crop} की कटाई का समय आ गया है। नुकसान से बचने के लिए सही नमी पर कटाई पूरी करें।",
        "kn": "{crop} ಸುಗ್ಗಿ ಅವಧಿ ಆರಂಭವಾಗಿದೆ. ನಷ್ಟ ತಪ್ಪಿಸಲು ಸರಿಯಾದ ತೇವಾಂಶದಲ್ಲೇ ಕಟಾವು ಮುಗಿಸಿ.",
    },
    "test": {
        "en": "This is a test alert from AgriSarathi AI. Your SMS/in-app notification channel is working.",
        "hi": "यह AgriSarathi AI की परीक्षण सूचना है। आपका SMS नोटिफिकेशन चैनल सही से काम कर रहा है।",
        "kn": "ಇದು AgriSarathi AI ಪರೀಕ್ಷಾ ಅಧಿಸೂಚನೆ. ನಿಮ್ಮ SMS/ಅಧಿಸೂಚನೆ ಮಾರ್ಗವು ಕಾರ್ಯನಿರ್ವಹಿಸುತ್ತಿದೆ.",
    },
}

_SUPPORTED_LANGS = ("en", "hi", "kn")


def _tr(template: Dict[str, str], lang: str, **kwargs: Any) -> str:
    lang = lang if lang in template else "en"
    return template[lang].format(**kwargs)


def _title(category: str, lang: str) -> str:
    block = TITLES.get(category, TITLES["weather"])
    return block.get(lang, block.get("en", category))


# ============================================================================
# Static India data loaded once at import
# ============================================================================

_RAINFALL_NORMALS: Dict[tuple, Dict[int, float]] = {}
_RAINFALL_LOADED = False


def _load_rainfall_normals() -> None:
    global _RAINFALL_NORMALS, _RAINFALL_LOADED
    if _RAINFALL_LOADED:
        return
    try:
        df = pd.read_csv(RAINFALL_PATH)
        month_cols = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
                      "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
        for _, row in df.iterrows():
            state = str(row["STATE_UT_NAME"]).upper()
            district = str(row["DISTRICT"]).upper()
            _RAINFALL_NORMALS[(state, district)] = {
                i + 1: float(row[m]) for i, m in enumerate(month_cols) if str(row[m]) != "nan"
            }
        logger.info(f"Alerts: loaded rainfall normals for {len(_RAINFALL_NORMALS)} districts")
    except Exception as e:
        logger.error(f"Alerts: could not load rainfall normals: {e}")
    finally:
        _RAINFALL_LOADED = True


def _district_rain_normal(state: str, district: str) -> Dict[int, float]:
    return _RAINFALL_NORMALS.get((state.upper(), district.upper()), {})


# ============================================================================
# Live weather (Open-Meteo, free & keyless) with caching
# ============================================================================

_GEO_CACHE: Dict[str, Any] = {}
_WEATHER_CACHE: Dict[str, tuple] = {}


def _geocode(state: str, district: str) -> Optional[tuple]:
    query = f"{district}, {state}, India"
    if query in _GEO_CACHE:
        return _GEO_CACHE[query]
    try:
        r = httpx.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": district, "count": 3, "language": "en", "format": "json"},
            timeout=6,
        )
        r.raise_for_status()
        for res in r.json().get("results", []):
            country = res.get("country", "")
            if "india" in country.lower():
                lat, lon = res["latitude"], res["longitude"]
                _GEO_CACHE[query] = (lat, lon)
                return lat, lon
        _GEO_CACHE[query] = None
    except Exception as e:
        logger.warning(f"Alerts: geocoding failed for {query}: {e}")
        _GEO_CACHE[query] = None
    return None


def _fetch_live_weather(state: str, district: str) -> Optional[Dict[str, float]]:
    cache_key = f"{district.upper()}|{state.upper()}"
    now = time.time()
    cached = _WEATHER_CACHE.get(cache_key)
    if cached and now - cached[0] < 1800:
        return cached[1]
    latlon = _geocode(state, district)
    if not latlon:
        _WEATHER_CACHE[cache_key] = (now, None)
        return None
    lat, lon = latlon
    try:
        r = httpx.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat, "longitude": lon,
                "daily": "precipitation_sum,temperature_2m_max,temperature_2m_min",
                "timezone": "auto", "forecast_days": 7,
            },
            timeout=8,
        )
        r.raise_for_status()
        daily = r.json()["daily"]
        data = {
            "precip7": float(sum(daily["precipitation_sum"])),
            "tmax7": float(max(daily["temperature_2m_max"])),
            "tmin7": float(min(daily["temperature_2m_min"])),
        }
        _WEATHER_CACHE[cache_key] = (now, data)
        return data
    except Exception as e:
        logger.warning(f"Alerts: weather forecast failed for {cache_key}: {e}")
        _WEATHER_CACHE[cache_key] = (now, None)
        return None


# ============================================================================
# Market trend analysis (WPI CSVs)
# ============================================================================

def _market_trend(crop: str) -> Optional[Dict[str, Any]]:
    csv_name = _csv_for_crop(crop)
    if not csv_name:
        return None
    path = os.path.join(PRICE_DATA_DIR, csv_name)
    try:
        df = pd.read_csv(path)
        if len(df) < 4:
            return None
        wpi = df["WPI"].astype(float).tolist()
        latest, prev, prev3 = wpi[-1], wpi[-2], wpi[-4]
        return {
            "crop": csv_name.replace(".csv", ""),
            "latest": latest,
            "chg1": (latest - prev) / prev * 100 if prev else 0.0,
            "chg3": (latest - prev3) / prev3 * 100 if prev3 else 0.0,
            "month": int(df.iloc[-1]["Month"]),
            "year": int(df.iloc[-1]["Year"]),
        }
    except Exception as e:
        logger.warning(f"Alerts: market trend failed for {crop}: {e}")
        return None


# ============================================================================
# Farmer registry (JSON-persisted)
# ============================================================================

_FARMER_LOCK = threading.Lock()


class FarmerRegistry:
    def __init__(self, path: str):
        self.path = path
        self.farmers: Dict[str, dict] = {}
        self.load()

    def load(self) -> None:
        try:
            if os.path.exists(self.path):
                with open(self.path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.farmers = data if isinstance(data, dict) else {}
        except Exception as e:
            logger.error(f"Alerts: failed to load farmer registry: {e}")
            self.farmers = {}

    def save(self) -> None:
        try:
            os.makedirs(ALERT_DATA_DIR, exist_ok=True)
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.farmers, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Alerts: failed to persist farmer registry: {e}")

    # -- CRUD ---------------------------------------------------------------
    def find_by_phone(self, phone: str) -> Optional[dict]:
        norm = "".join(ch for ch in phone if ch.isdigit())
        for farmer in self.farmers.values():
            if "".join(ch for ch in farmer.get("phone", "") if ch.isdigit()) == norm:
                return farmer
        return None

    def get(self, farmer_id: str) -> Optional[dict]:
        return self.farmers.get(farmer_id)

    def list(self) -> List[dict]:
        return [dict(f) for f in self.farmers.values()]

    def create(self, payload: dict) -> dict:
        with _FARMER_LOCK:
            existing = self.find_by_phone(payload.get("phone", ""))
            if existing:
                return existing
            farmer_id = f"f-{uuid.uuid4().hex[:10]}"
            farmer = {
                "id": farmer_id,
                "name": payload.get("name", ""),
                "phone": payload.get("phone", ""),
                "language": payload.get("language", "en"),
                "state": payload.get("state", ""),
                "district": payload.get("district", ""),
                "crops": list(payload.get("crops", []) or []),
                "alert_preferences": {
                    "weather": bool(payload.get("alert_preferences", {}).get("weather", True)),
                    "market": bool(payload.get("alert_preferences", {}).get("market", True)),
                    "farming": bool(payload.get("alert_preferences", {}).get("farming", True)),
                },
                "created_at": datetime.utcnow().isoformat() + "Z",
                "alerts": [],
                "last_generated": {},
            }
            self.farmers[farmer_id] = farmer
            self.save()
            return farmer

    def update_preferences(self, farmer_id: str, prefs: dict) -> Optional[dict]:
        farmer = self.farmers.get(farmer_id)
        if not farmer:
            return None
        for key in ("weather", "market", "farming"):
            if key in prefs:
                farmer["alert_preferences"][key] = bool(prefs[key])
        self.save()
        return farmer

    def add_alert(self, farmer_id: str, alert: dict) -> dict:
        farmer = self.farmers.get(farmer_id)
        if not farmer:
            raise KeyError(farmer_id)
        alert["id"] = f"a-{uuid.uuid4().hex[:10]}"
        with _FARMER_LOCK:
            farmer["alerts"].insert(0, alert)
            farmer["alerts"] = farmer["alerts"][:100]
            farmer["last_generated"][alert["dedup_key"]] = datetime.utcnow().date().isoformat()
            self.save()
        return alert

    def list_alerts(self, farmer_id: str, unread_only: bool = False) -> List[dict]:
        farmer = self.farmers.get(farmer_id)
        if not farmer:
            return []
        alerts = [a for a in farmer["alerts"] if not a.get("dismissed")]
        if unread_only:
            alerts = [a for a in alerts if not a.get("read")]
        return alerts

    def mark_read(self, alert_id: str) -> Optional[dict]:
        for farmer in self.farmers.values():
            for alert in farmer.get("alerts", []):
                if alert["id"] == alert_id:
                    alert["read"] = True
                    with _FARMER_LOCK:
                        self.save()
                    return alert
        return None

    def dismiss(self, alert_id: str) -> Optional[dict]:
        for farmer in self.farmers.values():
            for alert in farmer.get("alerts", []):
                if alert["id"] == alert_id:
                    alert["dismissed"] = True
                    with _FARMER_LOCK:
                        self.save()
                    return alert
        return None

    def seen_recently(self, farmer: dict, dedup_key: str, category: str) -> bool:
        last = farmer.get("last_generated", {}).get(dedup_key)
        if not last:
            return False
        window = DEDUP_WINDOW_DAYS.get(category, 6)
        try:
            last_dt = datetime.strptime(last, "%Y-%m-%d").date()
        except ValueError:
            return False
        return (datetime.utcnow().date() - last_dt).days < window


registry = FarmerRegistry(FARMERS_FILE)


# ============================================================================
# Alert generation engine
# ============================================================================

class AlertEngine:
    def __init__(self):
        _load_rainfall_normals()

    # -- builders -----------------------------------------------------------
    def _build_weather(self, farmer: dict) -> List[dict]:
        if not farmer["alert_preferences"].get("weather", False):
            return []
        state, district = farmer.get("state", ""), farmer.get("district", "")
        lang = farmer.get("language", "en")
        month = datetime.now().month
        out = []
        live = _fetch_live_weather(state, district)
        norms = _district_rain_normal(state, district)

        if live:
            if live["precip7"] >= HEAVY_RAIN_MM:
                out.append(("weather", "warning", "weather_heavy_rain",
                            {"district": district, "mm": live["precip7"]}))
            if live["tmax7"] >= TEMP_HOT_THRESHOLD:
                out.append(("weather", "warning", "weather_heat",
                            {"district": district, "temp": live["tmax7"]}))
            if live["tmin7"] <= TEMP_COLD_THRESHOLD:
                out.append(("weather", "warning", "weather_cold",
                            {"district": district, "temp": live["tmin7"]}))
            if month not in MONSOON_MONTHS and live["precip7"] < (norms.get(month, 40) / 4.0) * 0.5:
                out.append(("weather", "info", "weather_dry", {"district": district}))
        else:
            if month in MONSOON_MONTHS:
                out.append(("weather", "info", "weather_monsoon", {"district": district}))

        return out

    def _build_market(self, farmer: dict) -> List[dict]:
        if not farmer["alert_preferences"].get("market", False):
            return []
        lang = farmer.get("language", "en")
        out = []
        for crop in farmer.get("crops", []) or []:
            trend = _market_trend(crop)
            if not trend:
                continue
            out.append(("market", "info", "market_update",
                        {"crop": trend["crop"].title(), "price": trend["latest"], "pct": trend["chg1"]}))
            if trend["chg1"] <= PRICE_DROP_PCT:
                out.append(("market", "warning", "market_drop",
                            {"crop": trend["crop"].title(), "pct": abs(trend["chg1"]), "price": trend["latest"]}))
            elif trend["chg1"] >= PRICE_RISE_PCT:
                out.append(("market", "info", "market_rise",
                            {"crop": trend["crop"].title(), "pct": trend["chg1"], "price": trend["latest"]}))
        return out

    def _build_farming(self, farmer: dict) -> List[dict]:
        if not farmer["alert_preferences"].get("farming", False):
            return []
        lang = farmer.get("language", "en")
        month = datetime.now().month
        out = []
        for crop in farmer.get("crops", []) or []:
            cal = CROP_CALENDAR.get(crop.strip().lower())
            if not cal:
                continue
            harvest = cal.get("harvest", [])
            pre = sorted({(m - 1) if m > 1 else 12 for m in harvest})
            if month in cal.get("sowing", []):
                out.append(("farming", "info", "farming_sow", {"crop": crop.title()}))
            if month in pre:
                months_txt = ", ".join([_MONTH_SHORT[m] for m in sorted(harvest)])
                out.append(("farming", "info", "farming_prepare_harvest",
                            {"crop": crop.title(), "months": months_txt}))
            if month in harvest:
                out.append(("farming", "info", "farming_harvest", {"crop": crop.title()}))
        return out

    # -- orchestration ------------------------------------------------------
    def generate_for_farmer(self, farmer: dict, force: bool = False) -> List[dict]:
        lang = farmer.get("language", "en")
        created = []
        builders = [self._build_weather, self._build_market, self._build_farming]
        for builder in builders:
            for category, severity, msg_key, kwargs in builder(farmer):
                dedup_key = f"{category}:{msg_key}"
                if kwargs.get("district"):
                    dedup_key += f":{kwargs['district'].upper()}"
                if msg_key in ("market_update", "market_drop", "market_rise"):
                    dedup_key += f":{kwargs.get('crop', '').lower()}"
                if msg_key in ("farming_sow", "farming_prepare_harvest", "farming_harvest"):
                    dedup_key += f":{kwargs.get('crop', '').lower()}"
                if not force and registry.seen_recently(farmer, dedup_key, category):
                    continue
                alert = {
                    "category": category,
                    "severity": severity,
                    "title": _title(category, lang),
                    "message": _tr(MESSAGES[msg_key], lang, **kwargs),
                    "language": lang,
                    "dedup_key": dedup_key,
                    "created_at": datetime.utcnow().isoformat() + "Z",
                    "read": False,
                    "dismissed": False,
                }
                try:
                    registry.add_alert(farmer["id"], alert)
                    created.append(alert)
                except KeyError:
                    continue
        return created

    def generate_all(self, force: bool = False) -> Dict[str, Any]:
        total, delivered = 0, 0
        per_farmer = {}
        for farmer_id, farmer in list(registry.farmers.items()):
            try:
                created = self.generate_for_farmer(farmer, force=force)
                per_farmer[farmer_id] = created
                for alert in created:
                    total += 1
                    if _send_notification(farmer, alert):
                        delivered += 1
            except Exception as e:
                logger.exception(f"Alerts: generation failed for {farmer_id}: {e}")
        return {
            "generated": total,
            "delivered": delivered,
            "delivery_mode": provider().name,
            "per_farmer": per_farmer,
        }


engine = AlertEngine()


# ============================================================================
# Notification providers (console demo + optional Twilio SMS)
# ============================================================================

class ConsoleProvider:
    name = "console"
    description = "Demo SMS — messages are written to the backend log. Set TWILIO_* in backend/.env for real SMS."

    def send(self, phone: str, message: str) -> bool:
        logger.info(f"[ALERT SMS → {phone}] {message}")
        return True


class TwilioProvider:
    name = "twilio"
    description = "Real SMS via Twilio Messaging API."

    def send(self, phone: str, message: str) -> bool:
        if not (TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_FROM):
            logger.warning("Twilio provider selected but credentials missing — falling back to log.")
            return False
        try:
            url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json"
            resp = httpx.post(
                url,
                auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN),
                data={"To": phone, "From": TWILIO_FROM, "Body": message},
                timeout=15,
            )
            resp.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Alerts: Twilio send failed to {phone}: {e}")
            return False


def provider():
    if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_FROM:
        return TwilioProvider()
    return ConsoleProvider()


def _send_notification(farmer: dict, alert: dict) -> bool:
    phone = farmer.get("phone", "")
    if not phone:
        return False
    body = f"[{alert['title']}] {alert['message']}"
    try:
        return provider().send(phone, body)
    except Exception as e:
        logger.error(f"Alerts: delivery failed: {e}")
        return False


# ============================================================================
# Background generation thread
# ============================================================================

_stop_event = threading.Event()


def _generator_loop() -> None:
    try:
        time.sleep(20)
        while not _stop_event.is_set():
            logger.info(f"Alerts: background generation cycle started ({GENERATION_INTERVAL_HOURS}h interval)")
            try:
                result = engine.generate_all(force=False)
                if result["generated"]:
                    logger.info(f"Alerts: generated {result['generated']} alerts ({result['delivery_mode']})")
            except Exception:
                logger.exception("Alerts: background generation cycle failed")
            _stop_event.wait(GENERATION_INTERVAL_HOURS * 3600)
    except Exception:
        logger.exception("Alerts: generator thread crashed")


_generator_thread: Optional[threading.Thread] = None


def start_background_task() -> bool:
    """Start the daemon generator thread (idempotent). Called from main.py startup."""
    global _generator_thread
    if _generator_thread and _generator_thread.is_alive():
        return False
    _generator_thread = threading.Thread(target=_generator_loop, daemon=True, name="alert-generator")
    _generator_thread.start()
    logger.info("Alerts: background generator thread started")
    return True


def stop_background_task() -> None:
    _stop_event.set()


# ============================================================================
# Pydantic request/response models
# ============================================================================

class AlertPreferences(BaseModel):
    weather: bool = True
    market: bool = True
    farming: bool = True


class FarmerRegistration(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    phone: str = Field(..., min_length=10, max_length=20)
    language: str = Field(default="en", max_length=8)
    state: str = Field(..., min_length=1, max_length=100)
    district: str = Field(..., min_length=1, max_length=100)
    crops: List[str] = Field(default_factory=list)
    alert_preferences: Optional[AlertPreferences] = None


class GenerateRequest(BaseModel):
    farmer_id: Optional[str] = None
    force: bool = False


class TestSendRequest(BaseModel):
    phone: str = Field(..., min_length=10, max_length=20)
    language: str = Field(default="en", max_length=8)


def _farmer_public(farmer: dict) -> dict:
    return {
        "id": farmer["id"],
        "name": farmer.get("name"),
        "phone": farmer.get("phone"),
        "language": farmer.get("language"),
        "state": farmer.get("state"),
        "district": farmer.get("district"),
        "crops": farmer.get("crops"),
        "alert_preferences": farmer.get("alert_preferences"),
        "alert_count": len([a for a in farmer.get("alerts", []) if not a.get("dismissed")]),
        "unread_count": len([a for a in farmer.get("alerts", []) if not a.get("read") and not a.get("dismissed")]),
        "created_at": farmer.get("created_at"),
    }


# ============================================================================
# REST endpoints
# ============================================================================

@router.get("/alerts/status")
async def alert_system_status():
    """System status: providers, farmer count, supported crops."""
    return {
        "app": "AgriSarathi Farmer Message Alert System",
        "version": "1.0.0",
        "provider": provider().name,
        "provider_description": provider().description,
        "farmers_registered": len(registry.farmers),
        "supported_crops": sorted(CROP_CALENDAR.keys()),
        "price_csps": len([f for f in os.listdir(PRICE_DATA_DIR) if f.endswith(".csv")]),
        "generation_interval_hours": GENERATION_INTERVAL_HOURS,
        "background_running": bool(_generator_thread and _generator_thread.is_alive()),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@router.get("/alerts/crops")
async def alert_supported_crops():
    """Crops the alert system can cover, with their sowing/harvest calendar."""
    return {
        "crops": [
            {"name": name, "sowing_months": cal["sowing"], "harvest_months": cal["harvest"]}
            for name, cal in sorted(CROP_CALENDAR.items())
        ]
    }


@router.post("/alerts/register")
async def register_farmer(payload: FarmerRegistration):
    """Register (or fetch) a farmer for alert subscription."""
    phone_digits = "".join(ch for ch in payload.phone if ch.isdigit())
    if len(phone_digits) < 10:
        raise HTTPException(status_code=422, detail="Phone number must contain at least 10 digits.")
    existing = registry.find_by_phone(payload.phone)
    if existing:
        return {"already_registered": True, "farmer": _farmer_public(existing)}
    prefs = payload.alert_preferences or AlertPreferences()
    farmer = registry.create({
        "name": payload.name,
        "phone": payload.phone,
        "language": payload.language,
        "state": payload.state,
        "district": payload.district,
        "crops": payload.crops,
        "alert_preferences": prefs.model_dump() if hasattr(prefs, "model_dump") else prefs.dict(),
    })
    return {"already_registered": False, "farmer": _farmer_public(farmer)}


@router.get("/alerts/farmers")
async def list_farmers():
    return {"farmers": [_farmer_public(f) for f in registry.list()], "count": len(registry.farmers)}


@router.get("/alerts/farmers/{farmer_id}")
async def get_farmer(farmer_id: str):
    farmer = registry.get(farmer_id)
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found.")
    return {"farmer": _farmer_public(farmer)}


@router.get("/alerts/farmers/{farmer_id}/alerts")
async def get_farmer_alerts(farmer_id: str, unread: bool = False):
    farmer = registry.get(farmer_id)
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found.")
    return {"farmer_id": farmer_id, "alerts": registry.list_alerts(farmer_id, unread_only=unread)}


@router.post("/alerts/farmers/{farmer_id}/preferences")
async def update_farmer_preferences(farmer_id: str, prefs: AlertPreferences):
    updated = registry.update_preferences(farmer_id, prefs.model_dump() if hasattr(prefs, "model_dump") else prefs.dict())
    if not updated:
        raise HTTPException(status_code=404, detail="Farmer not found.")
    return {"farmer": _farmer_public(updated)}


@router.post("/alerts/alerts/{alert_id}/read")
async def mark_alert_read(alert_id: str):
    alert = registry.mark_read(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found.")
    return {"alert": alert}


@router.post("/alerts/alerts/{alert_id}/dismiss")
async def dismiss_alert(alert_id: str):
    alert = registry.dismiss(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found.")
    return {"alert_id": alert_id, "dismissed": True}


@router.post("/alerts/generate")
async def generate_alerts(payload: GenerateRequest):
    """Trigger alert generation + delivery for all farmers (or one)."""
    if payload.farmer_id:
        farmer = registry.get(payload.farmer_id)
        if not farmer:
            raise HTTPException(status_code=404, detail="Farmer not found.")
        created = engine.generate_for_farmer(farmer, force=payload.force)
        delivered = sum(1 for a in created if _send_notification(farmer, a))
        return {
            "generated": len(created),
            "delivered": delivered,
            "delivery_mode": provider().name,
            "farmer_id": payload.farmer_id,
            "alerts": created,
        }
    return engine.generate_all(force=payload.force)


@router.post("/alerts/send-test")
async def send_test_alert(payload: TestSendRequest):
    """Send a demo notification to any phone number (console log or Twilio)."""
    msg = _tr(MESSAGES["test"], payload.language)
    ok = provider().send(payload.phone, f"[Test] {msg}")
    return {"delivered": ok, "delivery_mode": provider().name, "phone": payload.phone, "message": msg}


@router.get("/alerts/health")
async def alert_health():
    return {
        "status": "ok",
        "registry_file": FARMERS_FILE,
        "farmers_persisted": os.path.exists(FARMERS_FILE),
        "price_data_available": any(f.endswith(".csv") for f in os.listdir(PRICE_DATA_DIR)),
        "rainfall_data_available": os.path.exists(RAINFALL_PATH),
        "live_weather": "open-meteo (keyless)",
    }