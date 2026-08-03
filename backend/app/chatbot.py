"""
AI Chatbot Module - OpenRouter API Integration
Separate module for the AgriSarathi AI chatbot feature
"""

import os
import logging
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional
import httpx

logger = logging.getLogger(__name__)
router = APIRouter()

# OpenRouter configuration - FREE tier available!
# Get free API key at: https://openrouter.ai/keys
# Key is read from the OPENROUTER_API_KEY environment variable, falling back
# to backend/.env (gitignored). NEVER hardcode secrets in source code.


def _load_env_file(path: str) -> dict:
    """Minimal .env loader (no external dependency). Returns key->value dict."""
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


_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ENV = _load_env_file(os.path.join(_BACKEND_DIR, ".env"))

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", _ENV.get("OPENROUTER_API_KEY", ""))
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", _ENV.get("OPENROUTER_MODEL", "nousresearch/hermes-3-llama-3.1-405b:free"))

# Alternative free models:
# - "mistralai/mistral-7b-instruct:free" (may be unavailable)
# - "meta-llama/llama-3-8b-instruct:free"
# - "google/gemma-7b-it:free"

# ============================================================================
# Pydantic Models
# ============================================================================

class ChatRequest(BaseModel):
    """Chat request model"""
    message: str = Field(..., description="User question for the AI")
    context: str = Field(default="", description="Optional context about crops/soil")

class ChatResponse(BaseModel):
    """Chat response model"""
    response: str = Field(..., description="AI generated response")
    success: bool = Field(default=True, description="Whether the request was successful")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    model_used: str = Field(default="mistral-7b", description="Model used for response")
    is_ai_generated: bool = Field(default=False, description="Whether response is from AI API")

# ============================================================================
# System Prompt
# ============================================================================

AGRICULTURE_SYSTEM_PROMPT = """You are AgriSarathi AI, a friendly and knowledgeable agriculture expert helping Indian farmers.

YOUR ROLE:
- Answer farming questions in simple, practical language
- Provide crop recommendations based on soil, climate, and season
- Give step-by-step guidance for planting, irrigation, fertilization, and pest control
- Explain soil health, NPK values, and pH levels in easy terms
- Offer organic and chemical farming advice
- Share market insights and selling strategies

RULES:
1. Use SIMPLE language that any farmer can understand - avoid technical jargon
2. Give PRACTICAL, actionable advice with specific quantities (kg, liters, acres)
3. Be ENCOURAGING and supportive in tone
4. For crop recommendations, always ask about soil NPK if not provided
5. Keep responses CONCISE but informative (2-4 short paragraphs max)
6. Include EMOJIS where appropriate to make it friendly 🌾
7. If unsure, suggest consulting local Krishi Vigyan Kendra (KVK) or agricultural officers

EXPERTISE AREAS:
- Crop selection for different regions and seasons
- Soil testing and improvement
- Organic farming and composting
- Chemical fertilizers (Urea, DAP, MOP) - proper usage and quantities
- Pest and disease management
- Irrigation methods (drip, sprinkler, flood)
- Government schemes and subsidies
- Market prices and selling strategies

Remember: Farmers may not be tech-savvy. Keep responses clear, friendly, and immediately useful!"""

# ============================================================================
# Multilingual Fallback Chatbot
# ============================================================================

class MultilingualChatbot:
    """Multilingual AI Chatbot for Indian Farmers - Fallback when API is not available"""
    
    @staticmethod
    def get_response(message: str, language: str = "en") -> str:
        """Get rule-based response"""
        message_lower = message.lower()
        
        responses = {
            "en": {
                "greeting": "Hello! I'm AgriSarathi AI. Ask me about crops, soil, or farming! 🌾",
                "crop": "To recommend crops, I need:\n1. Your state and district\n2. Soil NPK values\n3. Current month\nUse the prediction form above! 🎯",
                "soil": "🧪 Soil Tips:\n• Nitrogen - Add urea or compost\n• Phosphorus - Use DAP\n• Potassium - Apply potash\n• pH 6.0-7.5 is ideal for most crops",
                "water": "💧 Irrigation Tips:\n• Water in morning (6-9 AM)\n• Drip saves 40% water\n• Critical at flowering stage\n• Avoid overwatering!",
                "pest": "🐛 Pest Control:\n• Neem spray (5ml/L water)\n• Garlic-chili spray\n• Yellow sticky traps\n• Marigold companion planting",
                "fertilizer": "🌱 Fertilizers:\n• Urea (46% N) - 40-60 kg/acre\n• DAP (18-46-0) - 25-50 kg/acre\n• Vermicompost - 2-4 tons/acre",
                "default": "I can help with:\n🌱 Crop selection\n🧪 Soil advice\n💧 Irrigation\n🐛 Pest control\n💰 Market prices\n\nWhat do you need help with?"
            },
            "hi": {
                "greeting": "नमस्ते! मैं अग्रीसारथी AI हूँ। फसलों, मिट्टी या खेती के बारे में पूछें! 🌾",
                "crop": "फसल सुझाव के लिए चाहिए:\n1. राज्य और जिला\n2. मिट्टी NPK मान\n3. वर्तमान महीना\nऊपर का फॉर्म भरें! 🎯",
                "soil": "🧪 मिट्टी के टिप्स:\n• नाइट्रोजन - यूरिया या खाद डालें\n• फॉस्फोरस - DAP का उपयोग करें\n• पोटेशियम - पोटाश डालें\n• pH 6.0-7.5 अधिकांश फसलों के लिए उत्तम",
                "water": "💧 सिंचाई के टिप्स:\n• सुबह (6-9 बजे) पानी दें\n• ड्रिप से 40% पानी बचता है\n• फूल आने के समय जरूरी\n• ज्यादा पानी न दें!",
                "pest": "🐛 कीट नियंत्रण:\n• नीम स्प्रे (5ml/L पानी)\n• लहसुन-मिर्च स्प्रे\n• पीले स्टिकी ट्रैप\n• गेंदे का साथी रोपण",
                "fertilizer": "🌱 उर्वरक:\n• यूरिया (46% N) - 40-60 किलो/एकड़\n• DAP (18-46-0) - 25-50 किलो/एकड़\n• वर्मीकंपोस्ट - 2-4 टन/एकड़",
                "default": "मैं मदद कर सकता हूँ:\n🌱 फसल चयन\n🧪 मिट्टी सलाह\n💧 सिंचाई\n🐛 कीट नियंत्रण\n💰 बाजार भाव\n\nआपको किस बारे में मदद चाहिए?"
            }
        }
        
        lang = language if language in responses else "en"
        
        if any(kw in message_lower for kw in ['hi', 'hello', 'hey', 'namaste', 'नमस्ते']):
            return responses[lang]["greeting"]
        elif any(kw in message_lower for kw in ['crop', 'which crop', 'what crop', 'फसल']):
            return responses[lang]["crop"]
        elif any(kw in message_lower for kw in ['soil', 'nitrogen', 'phosphorus', 'fertilizer', 'मिट्टी']):
            return responses[lang]["soil"]
        elif any(kw in message_lower for kw in ['water', 'irrigation', 'पानी']):
            return responses[lang]["water"]
        elif any(kw in message_lower for kw in ['pest', 'insect', 'disease', 'कीट']):
            return responses[lang]["pest"]
        elif any(kw in message_lower for kw in ['fertilizer', 'urea', 'dap', 'urvarak', 'खत']):
            return responses[lang]["fertilizer"]
        else:
            return responses[lang]["default"]

# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    AI Chatbot endpoint using OpenRouter (Cloud API - FREE tier)
    
    FREE MODELS AVAILABLE:
    - mistralai/mistral-7b-instruct:free
    - meta-llama/llama-3-8b-instruct:free
    - nousresearch/hermes-3-llama-3.1-405b:free
    
    To get API key:
    1. Go to https://openrouter.ai/keys
    2. Create free account
    3. Copy API key
    4. Set as environment variable: OPENROUTER_API_KEY=your_key
    
    Without API key, uses intelligent rule-based fallback.
    """
    try:
        # If no API key, use fallback
        if not OPENROUTER_API_KEY:
            fallback_response = MultilingualChatbot.get_response(request.message)
            return ChatResponse(
                response=fallback_response,
                success=True,
                model_used="rule-based-fallback",
                is_ai_generated=False
            )
        
        # Prepare messages
        messages = [
            {"role": "system", "content": AGRICULTURE_SYSTEM_PROMPT},
            {"role": "user", "content": request.message}
        ]
        
        # Call OpenRouter API
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "http://localhost:8081",
                    "X-Title": "AgriSarathi AI"
                },
                json={
                    "model": OPENROUTER_MODEL,
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 500,
                    "top_p": 0.9,
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result["choices"][0]["message"]["content"].strip()
                
                return ChatResponse(
                    response=ai_response,
                    success=True,
                    model_used=OPENROUTER_MODEL,
                    is_ai_generated=True,
                    error=None
                )
            else:
                # Fallback to rule-based if API fails
                fallback_response = MultilingualChatbot.get_response(request.message)
                return ChatResponse(
                    response=fallback_response,
                    success=True,
                    model_used="rule-based-fallback",
                    is_ai_generated=False,
                    error=f"OpenRouter API error: {response.status_code}. Using fallback response."
                )
                
    except httpx.TimeoutException:
        # Fallback on timeout
        fallback_response = MultilingualChatbot.get_response(request.message)
        return ChatResponse(
            response=fallback_response,
            success=True,
            model_used="rule-based-fallback",
            is_ai_generated=False,
            error="AI service timeout. Using fallback response."
        )
    except Exception as e:
        logger.error(f"Chatbot error: {str(e)}")
        # Fallback on any error
        fallback_response = MultilingualChatbot.get_response(request.message)
        return ChatResponse(
            response=fallback_response,
            success=True,
            model_used="rule-based-fallback",
            is_ai_generated=False,
            error=f"AI service error. Using fallback response."
        )

@router.get("/chat/status")
async def chat_status():
    """Check if AI chatbot is available"""
    if not OPENROUTER_API_KEY:
        return {
            "available": True,
            "mode": "fallback",
            "message": "Using rule-based fallback (no API key set). Set OPENROUTER_API_KEY for AI-powered responses.",
            "setup_instructions": [
                "1. Get free API key: https://openrouter.ai/keys",
                "2. Set environment variable: OPENROUTER_API_KEY=your_key",
                "3. Restart backend server"
            ]
        }
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Test with a simple request
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": OPENROUTER_MODEL,
                    "messages": [{"role": "user", "content": "Hi"}],
                    "max_tokens": 10
                }
            )
            
            if response.status_code == 200:
                return {
                    "available": True,
                    "mode": "ai",
                    "model": OPENROUTER_MODEL,
                    "message": "AI chatbot ready with cloud-based open-source LLM"
                }
            else:
                return {
                    "available": True,
                    "mode": "fallback",
                    "message": f"API returned {response.status_code}. Will use fallback responses.",
                    "error": response.text
                }
    except Exception as e:
        return {
            "available": True,
            "mode": "fallback",
            "message": "AI API unavailable. Using intelligent fallback.",
            "error": str(e)
        }
