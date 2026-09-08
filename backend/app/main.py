"""
Unified Crop Recommendation and Price Prediction API
Integrates:
  - Crop Prediction (PyTorch Neural Network, 22 classes)
  - Crop Price Prediction (24 DecisionTreeRegressors)

Author: Cascade AI
Date: 2026-04-21
"""

import os
import json
import math
import pickle
import itertools
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from dataclasses import dataclass

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from sklearn.tree import DecisionTreeRegressor
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import httpx  # For Ollama API calls
# requests removed - no external API dependency

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# PATH CONFIGURATION - Adjust these paths as needed
# ============================================================================
# Get the backend root directory (parent of app folder)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Data paths
DATA_DIR = os.path.join(BASE_DIR, "data")
RAINFALL_DATA_PATH = os.path.join(DATA_DIR, "rainfall", "rainfall_normal.csv")
PRICE_DATA_DIR = os.path.join(DATA_DIR, "prices")

# Model paths (for future model files)
MODELS_DIR = os.path.join(BASE_DIR, "models")

# No external API needed - using climate estimation based on month and rainfall

# ============================================================================
# CROP NAME MAPPING
# ============================================================================

# Mapping from crop prediction output to price prediction input
# Only crops with corresponding price data are mapped
CROP_TO_PRICE_MAPPING = {
    "rice": "paddy",           # paddy is rice
    "cotton": "cotton",        # direct match
    "jute": "jute",            # direct match
    "maize": "maize",          # direct match
}

# Crops that have price data but NO crop prediction support
PRICE_ONLY_CROPS = [
    "arhar", "bajra", "barley", "copra", "sesamum", "gram",
    "groundnut", "jowar", "masoor", "moong", "niger", "ragi",
    "rape", "safflower", "soyabean", "sugarcane", "sunflower",
    "urad", "wheat"
]

# Note: ALL 22 predicted crops now have price prediction via proxy models!
# CROP_ONLY_CROPS is deprecated - kept for backward compatibility
CROP_ONLY_CROPS = []  # All crops now have price prediction support

# Base prices for price calculation (from price model + estimated for missing crops)
BASE_PRICES = {
    # Original 23 crops with price data
    "Paddy": 1245.5,
    "Arhar": 3200,
    "Bajra": 1175,
    "Barley": 980,
    "Copra": 5100,
    "Cotton": 3600,
    "Sesamum": 4200,
    "Gram": 2800,
    "Groundnut": 3700,
    "Jowar": 1520,
    "Maize": 1175,
    "Masoor": 2800,
    "Moong": 3500,
    "Niger": 3500,
    "Ragi": 1500,
    "Rape": 2500,
    "Jute": 1675,
    "Safflower": 2500,
    "Soyabean": 2200,
    "Sugarcane": 2250,
    "Sunflower": 3700,
    "Urad": 4300,
    "Wheat": 1350,
    # Estimated base prices for crops without historical data
    # Based on market research and commodity prices
    "Rice": 1245.5,           # Same as paddy
    "Apple": 8500,            # High-value fruit
    "Banana": 2800,           # Common fruit
    "Blackgram": 4300,        # Similar to urad (pulses)
    "Chickpea": 2800,         # Similar to gram
    "Coconut": 5100,          # Same as copra
    "Coffee": 12000,          # Cash crop (high value)
    "Grapes": 4500,           # Fruit
    "Kidneybeans": 3200,      # Similar to arhar
    "Lentil": 2800,           # Similar to masoor
    "Mango": 3500,            # Fruit (seasonal)
    "Mothbeans": 3500,        # Similar to moong
    "Mungbean": 3500,         # Same as moong
    "Muskmelon": 2200,        # Fruit
    "Orange": 3200,           # Fruit
    "Papaya": 2000,           # Fruit
    "Pigeonpeas": 3200,       # Similar to arhar
    "Pomegranate": 5500,      # Fruit (high value)
    "Watermelon": 1800        # Fruit
}

# Mapping for crops without their own WPI model to use similar crop's model
# This allows price prediction for ALL 22 predicted crops
CROP_WPI_PROXY = {
    # Pulses/Legumes - use gram, arhar, or masoor models
    "blackgram": "urad",        # Both blackgram and urad are similar pulses
    "chickpea": "gram",         # Chickpea = gram
    "kidneybeans": "arhar",     # Kidney beans similar to arhar
    "lentil": "masoor",         # Lentil = masoor
    "mothbeans": "moong",       # Similar small pulses
    "mungbean": "moong",        # Mungbean = moong
    "pigeonpeas": "arhar",      # Pigeon peas = arhar
    
    # Cereals/Grains - use maize, bajra, or wheat models
    "rice": "paddy",            # Direct mapping
    
    # Fruits - use generic seasonal patterns (will use bajra as proxy for cereal-based WPI trends)
    "apple": "wheat",           # Use wheat model for fruit price stability pattern
    "banana": "maize",          # Use maize model for banana (staple food pattern)
    "grapes": "cotton",         # Use cotton for cash crop pattern
    "mango": "sugarcane",       # Use sugarcane for seasonal fruit pattern
    "muskmelon": "bajra",       # Summer crop pattern
    "orange": "cotton",         # Cash crop pattern
    "papaya": "maize",          # Staple pattern
    "pomegranate": "cotton",    # High value crop pattern
    "watermelon": "bajra",      # Summer crop pattern
    
    # Cash crops - use similar patterns
    "coconut": "copra",         # Coconut = copra
    "coffee": "cotton",         # Cash crop volatility pattern
    
    # Direct matches (already in CROP_TO_PRICE_MAPPING)
    "cotton": "cotton",
    "jute": "jute", 
    "maize": "maize"
}

# Annual rainfall by month (from price model)
ANNUAL_RAINFALL = [29, 21, 37.5, 30.7, 52.6, 150, 299, 251.7, 179.2, 70.5, 39.8, 10.9]

# ============================================================================
# ============================================================================
# EXPLAINABLE AI (XAI) MODULE - Farmer-Friendly Explanations & Growth Guidance
# ============================================================================

class CropExplainability:
    """
    Generates farmer-friendly explanations for crop recommendations
    and provides growth guidance for selected crops.
    """
    
    # Crop requirements database (optimal ranges)
    CROP_REQUIREMENTS = {
        'rice': {
            'nitrogen': (80, 120), 'phosphorous': (40, 60), 'potassium': (60, 100),
            'ph': (5.5, 6.5), 'temperature': (20, 30), 'rainfall': (150, 300),
            'water_needs': 'High', 'soil_type': 'Clay/Loamy',
            'explanation': 'Rice loves water and slightly acidic soil. Your conditions match perfectly!'
        },
        'wheat': {
            'nitrogen': (60, 100), 'phosphorous': (30, 50), 'potassium': (50, 80),
            'ph': (6.0, 7.0), 'temperature': (15, 25), 'rainfall': (50, 100),
            'water_needs': 'Moderate', 'soil_type': 'Loamy/Clay',
            'explanation': 'Wheat grows well in your moderate temperature and balanced soil conditions.'
        },
        'maize': {
            'nitrogen': (70, 110), 'phosphorous': (35, 55), 'potassium': (55, 85),
            'ph': (5.8, 7.0), 'temperature': (18, 27), 'rainfall': (60, 110),
            'water_needs': 'Moderate-High', 'soil_type': 'Well-drained Loamy',
            'explanation': 'Maize needs warm weather and well-drained soil. Your farm conditions are ideal!'
        },
        'cotton': {
            'nitrogen': (50, 90), 'phosphorous': (25, 45), 'potassium': (40, 70),
            'ph': (6.0, 7.5), 'temperature': (21, 30), 'rainfall': (60, 120),
            'water_needs': 'Moderate', 'soil_type': 'Black/Clay',
            'explanation': 'Cotton thrives in warm climates with your soil type. Good choice for your region!'
        },
        'sugarcane': {
            'nitrogen': (100, 150), 'phosphorous': (50, 80), 'potassium': (80, 120),
            'ph': (6.0, 7.5), 'temperature': (20, 35), 'rainfall': (150, 250),
            'water_needs': 'High', 'soil_type': 'Deep Loamy',
            'explanation': 'Sugarcane needs plenty of water and nutrients. Your soil has good fertility!'
        },
        'groundnut': {
            'nitrogen': (30, 60), 'phosphorous': (40, 70), 'potassium': (40, 70),
            'ph': (6.0, 6.5), 'temperature': (20, 30), 'rainfall': (50, 100),
            'water_needs': 'Low-Moderate', 'soil_type': 'Sandy/Loamy',
            'explanation': 'Groundnut loves well-drained, sandy soil. Your conditions are perfect!'
        },
        'bajra': {
            'nitrogen': (40, 70), 'phosphorous': (30, 50), 'potassium': (30, 60),
            'ph': (6.0, 7.5), 'temperature': (25, 35), 'rainfall': (30, 80),
            'water_needs': 'Low', 'soil_type': 'Sandy/Loamy',
            'explanation': 'Bajra grows best in hot, dry conditions. Perfect for your area!'
        },
        'jowar': {
            'nitrogen': (50, 80), 'phosphorous': (30, 50), 'potassium': (40, 70),
            'ph': (6.0, 7.5), 'temperature': (20, 32), 'rainfall': (40, 100),
            'water_needs': 'Low-Moderate', 'soil_type': 'All types',
            'explanation': 'Jowar is hardy and grows in various soils. Good for your region!'
        },
        'tur': {
            'nitrogen': (20, 40), 'phosphorous': (30, 60), 'potassium': (20, 40),
            'ph': (6.0, 7.5), 'temperature': (20, 28), 'rainfall': (60, 100),
            'water_needs': 'Low', 'soil_type': 'Well-drained',
            'explanation': 'Tur (Pigeon Pea) is drought-tolerant. Perfect for your rainfall pattern!'
        },
        'gram': {
            'nitrogen': (20, 40), 'phosphorous': (40, 70), 'potassium': (20, 50),
            'ph': (6.0, 7.0), 'temperature': (18, 25), 'rainfall': (30, 60),
            'water_needs': 'Low', 'soil_type': 'Loamy/Clay',
            'explanation': 'Gram (Chickpea) needs cool weather and less water. Your conditions suit it!'
        },
        'masoor': {
            'nitrogen': (20, 40), 'phosphorous': (30, 60), 'potassium': (20, 40),
            'ph': (5.5, 6.5), 'temperature': (18, 25), 'rainfall': (40, 80),
            'water_needs': 'Low-Moderate', 'soil_type': 'Loamy',
            'explanation': 'Masoor (Lentil) prefers cool, slightly acidic soil. Great match!'
        },
        'moong': {
            'nitrogen': (20, 40), 'phosphorous': (30, 60), 'potassium': (20, 40),
            'ph': (6.0, 7.0), 'temperature': (25, 35), 'rainfall': (30, 80),
            'water_needs': 'Low-Moderate', 'soil_type': 'Loamy',
            'explanation': 'Moong grows fast in warm conditions. Good choice for your farm!'
        },
        'urad': {
            'nitrogen': (20, 40), 'phosphorous': (30, 60), 'potassium': (20, 40),
            'ph': (5.5, 7.0), 'temperature': (25, 35), 'rainfall': (40, 100),
            'water_needs': 'Moderate', 'soil_type': 'Clay/Loamy',
            'explanation': 'Urad (Black Gram) loves warm, humid conditions. Your farm is suitable!'
        },
        'jute': {
            'nitrogen': (60, 100), 'phosphorous': (40, 70), 'potassium': (40, 70),
            'ph': (6.0, 7.0), 'temperature': (24, 35), 'rainfall': (150, 250),
            'water_needs': 'High', 'soil_type': 'Alluvial',
            'explanation': 'Jute needs hot, humid weather with lots of water. Perfect for your region!'
        },
        'sunflower': {
            'nitrogen': (50, 80), 'phosphorous': (40, 70), 'potassium': (40, 70),
            'ph': (6.0, 7.5), 'temperature': (20, 30), 'rainfall': (60, 120),
            'water_needs': 'Moderate', 'soil_type': 'Well-drained',
            'explanation': 'Sunflower loves sunlight and well-drained soil. Good for your farm!'
        },
        'soyabean': {
            'nitrogen': (40, 80), 'phosphorous': (40, 80), 'potassium': (40, 80),
            'ph': (6.0, 7.5), 'temperature': (20, 30), 'rainfall': (60, 120),
            'water_needs': 'Moderate', 'soil_type': 'Loamy',
            'explanation': 'Soyabean enriches soil and grows well in your conditions!'
        },
        'paddy': {
            'nitrogen': (80, 120), 'phosphorous': (40, 60), 'potassium': (60, 100),
            'ph': (5.5, 6.5), 'temperature': (20, 32), 'rainfall': (125, 200),
            'water_needs': 'High', 'soil_type': 'Clay/Loamy',
            'explanation': 'Paddy (Rice) needs standing water and your climate is suitable!'
        },
        'rapeseed': {
            'nitrogen': (50, 80), 'phosphorous': (40, 70), 'potassium': (40, 70),
            'ph': (6.0, 7.0), 'temperature': (15, 25), 'rainfall': (40, 80),
            'water_needs': 'Moderate', 'soil_type': 'Clay/Loamy',
            'explanation': 'Rapeseed grows in cool conditions. Your winter months are ideal!'
        },
        'onion': {
            'nitrogen': (80, 120), 'phosphorous': (40, 60), 'potassium': (80, 120),
            'ph': (6.0, 7.0), 'temperature': (13, 24), 'rainfall': (50, 100),
            'water_needs': 'Moderate', 'soil_type': 'Sandy/Loamy',
            'explanation': 'Onion needs good fertility and moderate water. Your soil supports it!'
        },
        'potato': {
            'nitrogen': (80, 120), 'phosphorous': (50, 80), 'potassium': (100, 150),
            'ph': (5.5, 6.5), 'temperature': (15, 20), 'rainfall': (50, 100),
            'water_needs': 'Moderate-High', 'soil_type': 'Sandy/Loamy',
            'explanation': 'Potato loves cool weather and loose soil. Perfect for your conditions!'
        },
        'tomato': {
            'nitrogen': (100, 150), 'phosphorous': (60, 90), 'potassium': (120, 180),
            'ph': (6.0, 6.8), 'temperature': (20, 27), 'rainfall': (60, 150),
            'water_needs': 'Moderate-High', 'soil_type': 'Well-drained Loamy',
            'explanation': 'Tomato needs rich soil and consistent water. Your farm can support it!'
        },
        'apple': {
            'nitrogen': (50, 80), 'phosphorous': (30, 50), 'potassium': (60, 100),
            'ph': (6.0, 7.0), 'temperature': (10, 25), 'rainfall': (100, 150),
            'water_needs': 'Moderate', 'soil_type': 'Well-drained Loamy',
            'explanation': 'Apple needs cool winters and moderate rain. Your hilly region suits it!'
        },
        'orange': {
            'nitrogen': (60, 100), 'phosphorous': (40, 60), 'potassium': (60, 100),
            'ph': (6.0, 7.5), 'temperature': (20, 30), 'rainfall': (100, 150),
            'water_needs': 'Moderate', 'soil_type': 'Well-drained',
            'explanation': 'Orange loves warm, sunny weather. Your conditions are great!'
        },
        'banana': {
            'nitrogen': (100, 150), 'phosphorous': (50, 80), 'potassium': (150, 250),
            'ph': (6.0, 7.5), 'temperature': (25, 35), 'rainfall': (150, 250),
            'water_needs': 'High', 'soil_type': 'Well-drained Loamy',
            'explanation': 'Banana needs tropical warmth and lots of nutrients. Good match!'
        },
        'papaya': {
            'nitrogen': (80, 120), 'phosphorous': (40, 60), 'potassium': (100, 150),
            'ph': (6.0, 6.5), 'temperature': (25, 35), 'rainfall': (100, 200),
            'water_needs': 'High', 'soil_type': 'Well-drained',
            'explanation': 'Papaya grows fast in warm, humid conditions. Your farm is perfect!'
        },
        'coffee': {
            'nitrogen': (60, 100), 'phosphorous': (30, 50), 'potassium': (60, 100),
            'ph': (6.0, 6.5), 'temperature': (15, 28), 'rainfall': (150, 250),
            'water_needs': 'Moderate-High', 'soil_type': 'Well-drained Loamy',
            'explanation': 'Coffee loves hilly areas with moderate rain. Your elevation helps!'
        }
    }
    
    # Growth stages guidance for each crop
    GROWTH_GUIDANCE = {
        'rice': {
            'duration': '90-120 days',
            'stages': [
                {'week': 'Week 1-2', 'stage': 'Nursery/Germination', 'action': 'Keep nursery flooded with 2-3cm water. Protect from birds.'},
                {'week': 'Week 3-4', 'stage': 'Transplanting', 'action': 'Transplant 25-day seedlings. Apply basal fertilizer (DAP + Urea).'},{'week': 'Week 5-6', 'stage': 'Tillering', 'action': 'Maintain 5cm water depth. Apply nitrogen split dose.'},
                {'week': 'Week 7-10', 'stage': 'Flowering', 'action': 'Increase water to 10cm. Monitor for pests like stem borer.'},
                {'week': 'Week 11-14', 'stage': 'Grain Filling', 'action': 'Drain water before harvest. Apply potash if needed.'},
                {'week': 'Week 15+', 'stage': 'Harvest', 'action': 'Harvest when grains turn golden. Sun-dry for 3-4 days.'}
            ]
        },
        'wheat': {
            'duration': '120-150 days',
            'stages': [
                {'week': 'Week 1-3', 'stage': 'Germination', 'action': 'Ensure proper seed depth (4-5cm). Irrigate if soil is dry.'},
                {'week': 'Week 4-8', 'stage': 'Vegetative/Tillering', 'action': 'First irrigation at 21 days. Apply nitrogen fertilizer.'},
                {'week': 'Week 9-12', 'stage': 'Stem Extension', 'action': 'Second irrigation. Watch for yellow rust disease.'},
                {'week': 'Week 13-16', 'stage': 'Flowering/Heading', 'action': 'Critical irrigation stage. Apply micronutrients if needed.'},
                {'week': 'Week 17-20', 'stage': 'Grain Filling', 'action': 'Final irrigation when grains are forming. Protect from birds.'},
                {'week': 'Week 21+', 'stage': 'Harvest', 'action': 'Harvest when grain moisture is 12-14%. Store properly.'}
            ]
        },
        'maize': {
            'duration': '90-110 days',
            'stages': [
                {'week': 'Week 1-2', 'stage': 'Germination', 'action': 'Plant seeds 3-4cm deep. Ensure good soil contact.'},
                {'week': 'Week 3-5', 'stage': 'Seedling', 'action': 'Thin to 1 plant per hole. Apply phosphorus near roots.'},
                {'week': 'Week 6-8', 'stage': 'Vegetative', 'action': 'Side-dress nitrogen. Control weeds. Irrigate if dry.'},
                {'week': 'Week 9-12', 'stage': 'Tasseling/Silking', 'action': 'Peak water need - irrigate regularly. Watch for borers.'},
                {'week': 'Week 13-15', 'stage': 'Grain Filling', 'action': 'Reduce irrigation. Protect from monkeys/birds.'},
                {'week': 'Week 16+', 'stage': 'Harvest', 'action': 'Harvest when husks turn brown. Dry to 14% moisture.'}
            ]
        },
        'cotton': {
            'duration': '150-180 days',
            'stages': [
                {'week': 'Week 1-3', 'stage': 'Germination', 'action': 'Plant in warm soil (>18°C). Irrigate lightly.'},
                {'week': 'Week 4-6', 'stage': 'Seedling', 'action': 'Thin to healthy plants. Apply starter fertilizer.'},
                {'week': 'Week 7-10', 'stage': 'Vegetative/Squaring', 'action': 'Increase irrigation. Control sucking pests.'},
                {'week': 'Week 11-16', 'stage': 'Flowering/Boll Formation', 'action': 'Peak water need. Apply potash. Monitor bollworms.'},
                {'week': 'Week 17-22', 'stage': 'Boll Development', 'action': 'Reduce irrigation slightly. Pick early bolls.'},
                {'week': 'Week 23+', 'stage': 'Harvest', 'action': 'Pick bolls as they open. 3-5 pickings needed.'}
            ]
        },
        'sugarcane': {
            'duration': '12-18 months',
            'stages': [
                {'week': 'Week 1-4', 'stage': 'Germination', 'action': 'Plant setts with 2-3 buds. Keep soil moist.'},
                {'week': 'Month 2-3', 'stage': 'Tillering', 'action': 'Apply heavy nitrogen (150kg/acre). Earth up rows.'},
                {'week': 'Month 4-6', 'stage': 'Grand Growth', 'action': 'Peak growth - irrigate weekly. Apply micronutrients.'},
                {'week': 'Month 7-9', 'stage': 'Vegetative/Maturity', 'action': 'Stop nitrogen. Watch for borers. Remove water shoots.'},
                {'week': 'Month 10-12', 'stage': 'Ripening', 'action': 'Dry off irrigation. Apply ripening agent if needed.'},
                {'week': 'Month 12+', 'stage': 'Harvest', 'action': 'Harvest when brix is high. Replant ratoons or fresh.'}
            ]
        },
        'groundnut': {
            'duration': '90-120 days',
            'stages': [
                {'week': 'Week 1-2', 'stage': 'Germination', 'action': 'Plant shelled kernels. Light irrigation.'},
                {'week': 'Week 3-5', 'stage': 'Vegetative', 'action': 'Gypsum application (400kg/acre) crucial at flowering.'},
                {'week': 'Week 6-8', 'stage': 'Flowering/Pegging', 'action': 'Pegs enter soil - keep loose. Irrigate if dry.'},
                {'week': 'Week 9-12', 'stage': 'Pod Development', 'action': 'Calcium is critical. Control leaf spot diseases.'},
                {'week': 'Week 13-14', 'stage': 'Pod Filling', 'action': 'Reduce irrigation. Check pod maturity.'},
                {'week': 'Week 15+', 'stage': 'Harvest', 'action': 'Harvest when leaves yellow. Dry pods to 8% moisture.'}
            ]
        },
        'bajra': {
            'duration': '75-90 days',
            'stages': [
                {'week': 'Week 1-2', 'stage': 'Germination', 'action': 'Sow shallow (2-3cm) after rains. Thin overcrowded areas.'},
                {'week': 'Week 3-5', 'stage': 'Tillering', 'action': 'Apply nitrogen if rain permits. Hand weed.'},
                {'week': 'Week 6-8', 'stage': 'Flowering', 'action': 'Minimal water need. Watch for ergot disease.'},
                {'week': 'Week 9-10', 'stage': 'Grain Filling', 'action': 'Stop irrigation. Protect from birds.'},
                {'week': 'Week 11+', 'stage': 'Harvest', 'action': 'Harvest when heads droop. Thresh and store dry.'}
            ]
        },
        'jowar': {
            'duration': '105-120 days',
            'stages': [
                {'week': 'Week 1-2', 'stage': 'Germination', 'action': 'Sow 3-4cm deep. Ensure good seed-soil contact.'},
                {'week': 'Week 3-5', 'stage': 'Seedling', 'action': 'Thin to 15cm spacing. Apply DAP near rows.'},
                {'week': 'Week 6-8', 'stage': 'Tillering', 'action': 'Side-dress urea. Inter-culture weeding.'},
                {'week': 'Week 9-11', 'stage': 'Flowering', 'action': 'Irrigate if drought during boot stage.'},
                {'week': 'Week 12-14', 'stage': 'Grain Filling', 'action': 'Bird control crucial. Check grain hardness.'},
                {'week': 'Week 15+', 'stage': 'Harvest', 'action': 'Cut when grains hard. Stack for 5-7 days before threshing.'}
            ]
        },
        'tur': {
            'duration': '160-250 days',
            'stages': [
                {'week': 'Week 1-4', 'stage': 'Germination', 'action': 'Plant 2 seeds per hole. Minimal irrigation needed.'},
                {'week': 'Month 2-4', 'stage': 'Vegetative', 'action': 'One irrigation at flowering if dry. No nitrogen needed.'},
                {'week': 'Month 5-6', 'stage': 'Flowering/Podding', 'action': 'Critical for yield. Irrigate if long dry spell.'},
                {'week': 'Month 7+', 'stage': 'Harvest', 'action': 'Harvest when 80% pods brown. Dry properly to avoid storage pests.'}
            ]
        },
        'gram': {
            'duration': '90-120 days',
            'stages': [
                {'week': 'Week 1-3', 'stage': 'Germination', 'action': 'Sow deep (5-8cm) for rabi. Pre-sow irrigation if dry.'},
                {'week': 'Week 4-8', 'stage': 'Vegetative', 'action': 'No nitrogen - fixes its own. Weed by hand.'},
                {'week': 'Week 9-12', 'stage': 'Flowering/Podding', 'action': 'One irrigation at pod filling if needed.'},
                {'week': 'Week 13+', 'stage': 'Harvest', 'action': 'Cut when leaves drop and pods brown. Dry thoroughly.'}
            ]
        },
        'masoor': {
            'duration': '100-130 days',
            'stages': [
                {'week': 'Week 1-3', 'stage': 'Germination', 'action': 'Shallow sowing (3cm). Light irrigation if soil dry.'},
                {'week': 'Week 4-8', 'stage': 'Vegetative', 'action': 'Weed control important. No nitrogen fertilizer.'},
                {'week': 'Week 9-12', 'stage': 'Flowering/Podding', 'action': 'Avoid waterlogging. Watch for rust disease.'},
                {'week': 'Week 13+', 'stage': 'Harvest', 'action': 'Harvest when 80% pods turn brown. Thresh carefully.'}
            ]
        },
        'moong': {
            'duration': '60-90 days',
            'stages': [
                {'week': 'Week 1-2', 'stage': 'Germination', 'action': 'Sow after pre-monsoon rain. Thin if overcrowded.'},
                {'week': 'Week 3-5', 'stage': 'Vegetative', 'action': 'Weed by hand twice. No chemical nitrogen needed.'},
                {'week': 'Week 6-8', 'stage': 'Flowering/Podding', 'action': 'Quick pod formation. Protect from hairy caterpillar.'},
                {'week': 'Week 9+', 'stage': 'Harvest', 'action': 'Harvest when pods turn black. Dry in sun.'}
            ]
        },
        'urad': {
            'duration': '70-90 days',
            'stages': [
                {'week': 'Week 1-2', 'stage': 'Germination', 'action': 'Sow with first monsoon rains. Ensure drainage.'},
                {'week': 'Week 3-5', 'stage': 'Vegetative', 'action': 'Inter-culture weeding. No nitrogen needed.'},
                {'week': 'Week 6-8', 'stage': 'Flowering/Podding', 'action': 'Irrigate if 2-week dry spell. Watch for yellow mosaic.'},
                {'week': 'Week 9+', 'stage': 'Harvest', 'action': 'Harvest when 80% pods mature. Dry pods thoroughly.'}
            ]
        },
        'jute': {
            'duration': '120-150 days',
            'stages': [
                {'week': 'Week 1-3', 'stage': 'Sowing/Germination', 'action': 'Broadcast or line sow. Very light irrigation.'},
                {'week': 'Week 4-8', 'stage': 'Vegetative', 'action': 'Thin to 15cm spacing. Weed 2-3 times.'},
                {'week': 'Week 9-12', 'stage': 'Stem Elongation', 'action': 'Heavy nitrogen needed. Irrigate if rain fails.'},
                {'week': 'Week 13-16', 'stage': 'Flowering', 'action': 'Harvest at early flowering for best fiber.'},
                {'week': 'Week 17+', 'stage': 'Harvest/Retting', 'action': 'Cut at base, ret in water for 10-15 days.'}
            ]
        },
        'sunflower': {
            'duration': '90-110 days',
            'stages': [
                {'week': 'Week 1-2', 'stage': 'Germination', 'action': 'Sow 4cm deep. Maintain moisture.'},
                {'week': 'Week 3-6', 'stage': 'Vegetative', 'action': 'Thin to 30cm spacing. Side-dress nitrogen.'},
                {'week': 'Week 7-9', 'stage': 'Flowering/Head Formation', 'action': 'Peak water need - irrigate. Watch for birds.'},
                {'week': 'Week 10-12', 'stage': 'Seed Filling', 'action': 'Reduce irrigation when back of head turns yellow.'},
                {'week': 'Week 13+', 'stage': 'Harvest', 'action': 'Harvest when back turns lemon yellow. Dry to 9% moisture.'}
            ]
        },
        'soyabean': {
            'duration': '90-120 days',
            'stages': [
                {'week': 'Week 1-3', 'stage': 'Germination', 'action': 'Treat seeds with rhizobium. Sow 3-4cm deep.'},
                {'week': 'Week 4-7', 'stage': 'Vegetative', 'action': 'Inter-culture weeding. No nitrogen fertilizer.'},
                {'week': 'Week 8-11', 'stage': 'Flowering/Podding', 'action': 'Critical irrigation if dry. Watch for stem fly.'},
                {'week': 'Week 12-14', 'stage': 'Seed Filling', 'action': 'Reduce irrigation. Leaves turn yellow naturally.'},
                {'week': 'Week 15+', 'stage': 'Harvest', 'action': 'Harvest when 95% leaves drop. Thresh immediately.'}
            ]
        },
        'paddy': {
            'duration': '100-140 days',
            'stages': [
                {'week': 'Week 1-3', 'stage': 'Nursery', 'action': 'Same as rice. Raise seedlings in wet bed.'},
                {'week': 'Week 4-5', 'stage': 'Transplanting', 'action': 'Transplant 25-30 day seedlings. Apply DAP.'},
                {'week': 'Week 6-10', 'stage': 'Tillering/Panicle', 'action': 'Maintain 5cm water. Split nitrogen application.'},
                {'week': 'Week 11-14', 'stage': 'Flowering/Grain Filling', 'action': 'Drain field 10 days before harvest.'},
                {'week': 'Week 15+', 'stage': 'Harvest', 'action': 'Harvest at 20-22% moisture. Sun dry.'}
            ]
        },
        'groundnut': {
            'duration': '90-120 days',
            'stages': [
                {'week': 'Week 1-2', 'stage': 'Germination', 'action': 'Plant shelled kernels. Light irrigation.'},
                {'week': 'Week 3-5', 'stage': 'Vegetative', 'action': 'Gypsum application (400kg/acre) crucial at flowering.'},
                {'week': 'Week 6-8', 'stage': 'Flowering/Pegging', 'action': 'Pegs enter soil - keep loose. Irrigate if dry.'},
                {'week': 'Week 9-12', 'stage': 'Pod Development', 'action': 'Calcium is critical. Control leaf spot diseases.'},
                {'week': 'Week 13-14', 'stage': 'Pod Filling', 'action': 'Reduce irrigation. Check pod maturity.'},
                {'week': 'Week 15+', 'stage': 'Harvest', 'action': 'Harvest when leaves yellow. Dry pods to 8% moisture.'}
            ]
        },
        'rape': {
            'duration': '110-140 days',
            'stages': [
                {'week': 'Week 1-3', 'stage': 'Germination', 'action': 'Early sowing gives better yield. Shallow sowing.'},
                {'week': 'Week 4-8', 'stage': 'Rosette/Vegetative', 'action': 'Apply basal nitrogen. Control aphids.'},
                {'week': 'Week 9-12', 'stage': 'Stem Extension', 'action': 'Irrigate if winter is dry. Watch for sawfly.'},
                {'week': 'Week 13-16', 'stage': 'Flowering/Silique', 'action': 'Peak water need. Apply micronutrients.'},
                {'week': 'Week 17+', 'stage': 'Harvest', 'action': 'Harvest when 75% siliques turn yellow.'}
            ]
        },
        'onion': {
            'duration': '130-160 days',
            'stages': [
                {'week': 'Month 1-2', 'stage': 'Nursery/Germination', 'action': 'Raise seedlings in nursery. Transplant at 8 weeks.'},
                {'week': 'Month 3-4', 'stage': 'Vegetative/Bulbing', 'action': 'High nitrogen needed. Frequent light irrigation.'},
                {'week': 'Month 5', 'stage': 'Bulb Enlargement', 'action': 'Side-dress NPK. Stop irrigation 2 weeks before harvest.'},
                {'week': 'Month 6+', 'stage': 'Harvest/Curing', 'action': 'Harvest when tops fall. Cure for 10-15 days in sun.'}
            ]
        },
        'potato': {
            'duration': '90-120 days',
            'stages': [
                {'week': 'Week 1-3', 'stage': 'Sprouting/Emergence', 'action': 'Plant whole or cut seed tubers. Hill up soil.'},
                {'week': 'Week 4-6', 'stage': 'Vegetative/Stolon', 'action': 'Apply heavy nitrogen. Maintain moisture.'},
                {'week': 'Week 7-10', 'stage': 'Tuber Initiation', 'action': 'Critical for yield - avoid water stress.'},
                {'week': 'Week 11-14', 'stage': 'Tuber Bulking', 'action': 'Peak water need. Apply micronutrients.'},
                {'week': 'Week 15+', 'stage': 'Maturation/Harvest', 'action': 'Cut foliage 10 days before harvest. Store cool and dark.'}
            ]
        },
        'tomato': {
            'duration': '90-120 days',
            'stages': [
                {'week': 'Week 1-4', 'stage': 'Nursery/Germination', 'action': 'Raise seedlings in pro-trays. Harden at 4 weeks.'},
                {'week': 'Week 5-8', 'stage': 'Vegetative/Growth', 'action': 'Stake or trellis plants. Apply calcium nitrate.'},
                {'week': 'Week 9-12', 'stage': 'Flowering/Fruiting', 'action': 'Irrigate consistently. Control fruit borer.'},
                {'week': 'Week 13-16', 'stage': 'Harvest', 'action': 'Pick when firm-ripe. 8-10 harvests possible.'}
            ]
        },
        'apple': {
            'duration': 'Perennial - annual fruiting cycle',
            'stages': [
                {'week': 'Month 1-2', 'stage': 'Dormancy/Chilling', 'action': 'Prune in winter. Apply dormant spray for diseases.'},
                {'week': 'Month 3-4', 'stage': 'Bud Break/Bloom', 'action': 'Apply boron before bloom. Protect from frost.'},
                {'week': 'Month 5-7', 'stage': 'Fruit Set/Growth', 'action': 'Thin fruitlets to 15cm apart. Irrigate regularly.'},
                {'week': 'Month 8-9', 'stage': 'Maturation/Harvest', 'action': 'Harvest based on color and sugar content. Store in cold.'}
            ]
        },
        'orange': {
            'duration': 'Perennial - annual fruiting cycle',
            'stages': [
                {'week': 'Month 1-3', 'stage': 'Flowering/Fruit Set', 'action': 'Peak water need. Apply micronutrients (Zn, Fe, Mn).'},{'week': 'Month 4-8', 'stage': 'Fruit Growth', 'action': 'Irrigate deeply monthly. Control citrus psylla.'},
                {'week': 'Month 9-11', 'stage': 'Maturation/Coloring', 'action': 'Reduce irrigation. Apply potassium for sweetness.'},
                {'week': 'Month 12+', 'stage': 'Harvest', 'action': 'Harvest when sugar-acid ratio is optimal. 2-3 pickings.'}
            ]
        },
        'banana': {
            'duration': '12-15 months',
            'stages': [
                {'week': 'Month 1-4', 'stage': 'Vegetative/Suckering', 'action': 'Plant sword suckers. Heavy organic manure. Remove weeds.'},
                {'week': 'Month 5-8', 'stage': 'Shooting/Pseudostem', 'action': 'Monthly nitrogen application. Ensure drainage.'},
                {'week': 'Month 9-11', 'stage': 'Flowering/Bunch', 'action': 'Remove dry leaves. Support heavy bunches. Bag bunches.'},
                {'week': 'Month 12+', 'stage': 'Harvest', 'action': 'Harvest when 3/4 round. Cut with portion of pseudostem.'}
            ]
        },
        'papaya': {
            'duration': '8-12 months',
            'stages': [
                {'week': 'Month 1-3', 'stage': 'Seedling/Establishment', 'action': 'Plant 3-4 seeds per pit. Select 1 female and 1 male/hermaphrodite.'},
                {'week': 'Month 4-6', 'stage': 'Vegetative/Growth', 'action': 'Monthly nitrogen application. Protect from strong wind.'},
                {'week': 'Month 7-9', 'stage': 'Flowering/Fruiting', 'action': 'First flowering. Remove male plants (keep 1:10 ratio).'},{'week': 'Month 10+', 'stage': 'Harvest', 'action': 'Harvest when skin shows yellow streaks. Twice weekly picking.'}
            ]
        },
        'coffee': {
            'duration': 'Perennial - annual bearing cycle',
            'stages': [
                {'week': 'Month 1-2', 'stage': 'Post-Harvest/Pruning', 'action': 'Prune after harvest. Apply lime if pH low.'},
                {'week': 'Month 3-4', 'stage': 'Pre-Bloom', 'action': 'Irrigate if dry. First fertilizer dose (NPK).'},{'week': 'Month 5-6', 'stage': 'Bloom/Fruit Set', 'action': 'Peak irrigation need. Shade management crucial.'},
                {'week': 'Month 7-10', 'stage': 'Berry Development', 'action': 'Second fertilizer dose. Control berry borer.'},
                {'week': 'Month 11-12', 'stage': 'Maturation/Harvest', 'action': 'Pick ripe cherries only. Wet or dry processing.'}
            ]
        }
    }
    
    @classmethod
    def compute_factor_scores(cls, crop: str, nitrogen: float, phosphorous: float,
                              potassium: float, ph: float, temperature: float,
                              rainfall: float) -> Dict[str, float]:
        """Score each factor 0-100 based on deviation from crop's optimal range."""
        req = cls.CROP_REQUIREMENTS.get(crop.lower(), {})
        if not req:
            return {k: 50.0 for k in ['nitrogen','phosphorous','potassium','ph','temperature','rainfall']}

        def score(val, lo, hi):
            if lo == 0 and hi == 0:
                return 50.0
            if lo <= val <= hi:
                return 100.0
            band = max(hi - lo, 1.0)
            gap = (lo - val) if val < lo else (val - hi)
            raw = 100.0 - (gap / band) * 50.0
            return round(min(100.0, max(0.0, raw)), 1)

        return {
            'nitrogen': score(nitrogen, *req.get('nitrogen', (0, 0))),
            'phosphorous': score(phosphorous, *req.get('phosphorous', (0, 0))),
            'potassium': score(potassium, *req.get('potassium', (0, 0))),
            'ph': score(ph, *req.get('ph', (0, 0))),
            'temperature': score(temperature, *req.get('temperature', (0, 0))),
            'rainfall': score(rainfall, *req.get('rainfall', (0, 0))),
        }

    @classmethod
    def compute_xai_breakdown(cls, crop: str, nitrogen: float, phosphorous: float,
                              potassium: float, ph: float, temperature: float,
                              rainfall: float, humidity: float = None) -> Dict:
        """Full XAI breakdown: per-factor scores, grouped categories, strengths/weaknesses."""
        scores = cls.compute_factor_scores(crop, nitrogen, phosphorous, potassium, ph, temperature, rainfall)

        # Grouped category scores
        soil_factors = {k: scores[k] for k in ['nitrogen','phosphorous','potassium','ph']}
        climate_factors = {k: scores[k] for k in ['temperature','rainfall']}

        soil_avg = round(sum(soil_factors.values()) / len(soil_factors), 1)
        climate_avg = round(sum(climate_factors.values()) / len(climate_factors), 1)
        location_avg = round((soil_avg + climate_avg) / 2, 1)

        # Strengths (≥70) and weaknesses (<50)
        strengths = [k for k, v in scores.items() if v >= 70]
        weaknesses = [k for k, v in scores.items() if v < 50]

        # Actionable recommendations
        recommendations = []
        nutrient_labels = {
            'nitrogen': ('Nitrogen (N)', 'Add nitrogen-rich fertilizer like Urea or compost'),
            'phosphorous': ('Phosphorus (P)', 'Apply DAP, SSP, or bone meal'),
            'potassium': ('Potassium (K)', 'Add MOP (Muriate of Potash) or wood ash'),
            'ph': ('pH', 'Use lime to raise pH or sulfur/gypsum to lower it'),
            'temperature': ('Temperature', 'Adjust planting time or use shade nets'),
            'rainfall': ('Rainfall', 'Plan irrigation schedule or install drainage'),
        }
        for factor in weaknesses:
            label, fix = nutrient_labels.get(factor, (factor, 'Consult local agricultural officer'))
            recommendations.append(f"Improve {label}: {fix}")

        return {
            'factor_scores': scores,
            'category_scores': {
                'soil': {'score': soil_avg, 'factors': soil_factors},
                'climate': {'score': climate_avg, 'factors': climate_factors},
                'location_overall': location_avg,
            },
            'overall_match': round((sum(scores.values()) / len(scores)), 1),
            'strengths': strengths,
            'weaknesses': weaknesses,
            'recommendations': recommendations,
        }

    @classmethod
    def analyze_soil(cls, nitrogen: float, phosphorous: float, potassium: float, ph: float) -> Dict:
        """Analyze soil conditions in farmer-friendly terms."""
        analysis = {
            'nitrogen': cls._categorize_nutrient(nitrogen, 'nitrogen'),
            'phosphorous': cls._categorize_nutrient(phosphorous, 'phosphorous'),
            'potassium': cls._categorize_nutrient(potassium, 'potassium'),
            'ph': cls._categorize_ph(ph),
            'summary': []
        }
        
        # Add specific observations
        if analysis['nitrogen'] == 'High':
            analysis['summary'].append("✅ Your soil has good nitrogen for leafy crops")
        elif analysis['nitrogen'] == 'Low':
            analysis['summary'].append("⚠️ Nitrogen is low - add organic manure or urea")
        
        if analysis['ph'] == 'Acidic':
            analysis['summary'].append("🧪 Soil is slightly acidic - good for rice, potato, coffee")
        elif analysis['ph'] == 'Alkaline':
            analysis['summary'].append("🧪 Soil is alkaline - add gypsum if needed")
        
        return analysis
    
    @classmethod
    def _categorize_nutrient(cls, value: float, nutrient: str) -> str:
        """Categorize nutrient levels."""
        ranges = {
            'nitrogen': {'Low': (0, 40), 'Medium': (40, 80), 'High': (80, float('inf'))},
            'phosphorous': {'Low': (0, 25), 'Medium': (25, 55), 'High': (55, float('inf'))},
            'potassium': {'Low': (0, 35), 'Medium': (35, 75), 'High': (75, float('inf'))}
        }
        
        for level, (min_val, max_val) in ranges[nutrient].items():
            if min_val <= value < max_val:
                return level
        return 'High'
    
    @classmethod
    def _categorize_ph(cls, ph: float) -> str:
        """Categorize pH level."""
        if ph < 6.0:
            return 'Acidic'
        elif ph < 7.0:
            return 'Neutral-Slightly Acidic'
        elif ph < 7.5:
            return 'Neutral'
        else:
            return 'Alkaline'
    
    @classmethod
    def generate_explanation(cls, crop: str, nitrogen: float, phosphorous: float, 
                           potassium: float, ph: float, temperature: float, 
                           rainfall: float, confidence: float) -> str:
        """Generate farmer-friendly explanation for crop recommendation."""
        
        # Get crop requirements
        req = cls.CROP_REQUIREMENTS.get(crop.lower(), {})
        if not req:
            return f"{crop.capitalize()} is recommended based on your soil and climate conditions."
        
        # Build explanation points
        reasons = []
        
        # Check nitrogen match
        n_min, n_max = req.get('nitrogen', (0, 0))
        if n_min <= nitrogen <= n_max:
            reasons.append(f"✓ Your soil nitrogen ({nitrogen}) is ideal for {crop.capitalize()}")
        
        # Check pH match
        ph_min, ph_max = req.get('ph', (0, 0))
        if ph_min <= ph <= ph_max:
            reasons.append(f"✓ Soil pH ({ph}) matches {crop.capitalize()} needs")
        
        # Check rainfall/water
        r_min, r_max = req.get('rainfall', (0, 0))
        water = req.get('water_needs', '')
        if r_min <= rainfall <= r_max:
            reasons.append(f"✓ Expected rainfall ({rainfall}mm) suits {water.lower()} water needs")
        
        # Add crop-specific explanation
        if 'explanation' in req:
            reasons.append(f"\n💡 {req['explanation']}")
        
        # Add confidence context
        if confidence > 0.7:
            reasons.append(f"\n🎯 High confidence ({confidence*100:.1f}%) - This crop is a strong match!")
        
        return "\n".join(reasons) if reasons else req.get('explanation', f'{crop.capitalize()} is suitable for your conditions.')
    
    # Fertilizer requirements for each crop (NPK values in kg/acre and key fertilizers)
    FERTILIZER_GUIDANCE = {
        'rice': {'npk': {'N': 60, 'P': 30, 'K': 30}, 'fertilizers': ['Urea (46% N) - 130 kg/acre', 'DAP (18-46-0) - 65 kg/acre', 'MOP (60% K) - 50 kg/acre'], 'organic': 'FYM - 5-6 tons/acre'},
        'wheat': {'npk': {'N': 80, 'P': 40, 'K': 20}, 'fertilizers': ['Urea (46% N) - 175 kg/acre', 'DAP (18-46-0) - 87 kg/acre', 'MOP (60% K) - 33 kg/acre'], 'organic': 'Compost - 4-5 tons/acre'},
        'maize': {'npk': {'N': 100, 'P': 50, 'K': 50}, 'fertilizers': ['Urea (46% N) - 217 kg/acre', 'DAP (18-46-0) - 109 kg/acre', 'MOP (60% K) - 83 kg/acre'], 'organic': 'FYM - 6-8 tons/acre'},
        'cotton': {'npk': {'N': 80, 'P': 40, 'K': 40}, 'fertilizers': ['Urea (46% N) - 175 kg/acre', 'DAP (18-46-0) - 87 kg/acre', 'MOP (60% K) - 67 kg/acre'], 'organic': 'Compost - 5-6 tons/acre'},
        'sugarcane': {'npk': {'N': 120, 'P': 60, 'K': 60}, 'fertilizers': ['Urea (46% N) - 260 kg/acre', 'SSP (16% P) - 375 kg/acre', 'MOP (60% K) - 100 kg/acre'], 'organic': 'FYM - 8-10 tons/acre'},
        'paddy': {'npk': {'N': 60, 'P': 30, 'K': 30}, 'fertilizers': ['Urea (46% N) - 130 kg/acre', 'DAP (18-46-0) - 65 kg/acre', 'MOP (60% K) - 50 kg/acre'], 'organic': 'FYM - 5-6 tons/acre'},
        'groundnut': {'npk': {'N': 20, 'P': 40, 'K': 40}, 'fertilizers': ['DAP (18-46-0) - 87 kg/acre', 'Gypsum (18% Ca) - 200 kg/acre', 'MOP (60% K) - 67 kg/acre'], 'organic': 'FYM - 4-5 tons/acre'},
        'potato': {'npk': {'N': 100, 'P': 50, 'K': 100}, 'fertilizers': ['Urea (46% N) - 217 kg/acre', 'DAP (18-46-0) - 109 kg/acre', 'MOP (60% K) - 167 kg/acre'], 'organic': 'Compost - 6-8 tons/acre'},
        'tomato': {'npk': {'N': 80, 'P': 60, 'K': 80}, 'fertilizers': ['Urea (46% N) - 175 kg/acre', 'SSP (16% P) - 375 kg/acre', 'MOP (60% K) - 133 kg/acre'], 'organic': 'Vermicompost - 3-4 tons/acre'},
        'onion': {'npk': {'N': 100, 'P': 40, 'K': 60}, 'fertilizers': ['Urea (46% N) - 217 kg/acre', 'DAP (18-46-0) - 87 kg/acre', 'MOP (60% K) - 100 kg/acre'], 'organic': 'FYM - 6-8 tons/acre'},
        'soyabean': {'npk': {'N': 20, 'P': 60, 'K': 30}, 'fertilizers': ['SSP (16% P) - 375 kg/acre', 'DAP (18-46-0) - 65 kg/acre', 'MOP (60% K) - 50 kg/acre'], 'organic': 'FYM - 4-5 tons/acre'},
        'gram': {'npk': {'N': 15, 'P': 40, 'K': 20}, 'fertilizers': ['SSP (16% P) - 250 kg/acre', 'DAP (18-46-0) - 87 kg/acre'], 'organic': 'FYM - 3-4 tons/acre'},
        'moong': {'npk': {'N': 15, 'P': 40, 'K': 20}, 'fertilizers': ['SSP (16% P) - 250 kg/acre', 'DAP (18-46-0) - 87 kg/acre'], 'organic': 'FYM - 3-4 tons/acre'},
        'arhar': {'npk': {'N': 20, 'P': 50, 'K': 20}, 'fertilizers': ['SSP (16% P) - 312 kg/acre', 'DAP (18-46-0) - 109 kg/acre', 'MOP (60% K) - 33 kg/acre'], 'organic': 'FYM - 4-5 tons/acre'},
        'bajra': {'npk': {'N': 50, 'P': 25, 'K': 20}, 'fertilizers': ['Urea (46% N) - 109 kg/acre', 'DAP (18-46-0) - 54 kg/acre'], 'organic': 'FYM - 3-4 tons/acre'},
        'jowar': {'npk': {'N': 60, 'P': 30, 'K': 25}, 'fertilizers': ['Urea (46% N) - 130 kg/acre', 'DAP (18-46-0) - 65 kg/acre', 'MOP (60% K) - 42 kg/acre'], 'organic': 'FYM - 4-5 tons/acre'},
        'barley': {'npk': {'N': 60, 'P': 30, 'K': 20}, 'fertilizers': ['Urea (46% N) - 130 kg/acre', 'DAP (18-46-0) - 65 kg/acre'], 'organic': 'FYM - 3-4 tons/acre'},
        'rape': {'npk': {'N': 80, 'P': 40, 'K': 40}, 'fertilizers': ['Urea (46% N) - 175 kg/acre', 'DAP (18-46-0) - 87 kg/acre', 'MOP (60% K) - 67 kg/acre'], 'organic': 'FYM - 4-5 tons/acre'},
        'sunflower': {'npk': {'N': 60, 'P': 30, 'K': 30}, 'fertilizers': ['Urea (46% N) - 130 kg/acre', 'DAP (18-46-0) - 65 kg/acre', 'MOP (60% K) - 50 kg/acre'], 'organic': 'FYM - 4-5 tons/acre'},
        'safflower': {'npk': {'N': 40, 'P': 20, 'K': 20}, 'fertilizers': ['Urea (46% N) - 87 kg/acre', 'SSP (16% P) - 125 kg/acre', 'MOP (60% K) - 33 kg/acre'], 'organic': 'FYM - 3-4 tons/acre'},
        'niger': {'npk': {'N': 40, 'P': 20, 'K': 20}, 'fertilizers': ['Urea (46% N) - 87 kg/acre', 'DAP (18-46-0) - 43 kg/acre', 'MOP (60% K) - 33 kg/acre'], 'organic': 'FYM - 3-4 tons/acre'},
        'ragi': {'npk': {'N': 50, 'P': 25, 'K': 25}, 'fertilizers': ['Urea (46% N) - 109 kg/acre', 'DAP (18-46-0) - 54 kg/acre', 'MOP (60% K) - 42 kg/acre'], 'organic': 'FYM - 4-5 tons/acre'},
        'copra': {'npk': {'N': 80, 'P': 40, 'K': 120}, 'fertilizers': ['Urea (46% N) - 175 kg/acre', 'DAP (18-46-0) - 87 kg/acre', 'MOP (60% K) - 200 kg/acre'], 'organic': 'FYM - 5-6 tons/acre'},
        'sesamum': {'npk': {'N': 40, 'P': 20, 'K': 20}, 'fertilizers': ['Urea (46% N) - 87 kg/acre', 'SSP (16% P) - 125 kg/acre'], 'organic': 'FYM - 3-4 tons/acre'},
        'masoor': {'npk': {'N': 20, 'P': 40, 'K': 20}, 'fertilizers': ['SSP (16% P) - 250 kg/acre', 'DAP (18-46-0) - 87 kg/acre'], 'organic': 'FYM - 3-4 tons/acre'},
        'urad': {'npk': {'N': 20, 'P': 40, 'K': 20}, 'fertilizers': ['SSP (16% P) - 250 kg/acre', 'DAP (18-46-0) - 87 kg/acre'], 'organic': 'FYM - 3-4 tons/acre'},
        'jute': {'npk': {'N': 80, 'P': 40, 'K': 60}, 'fertilizers': ['Urea (46% N) - 175 kg/acre', 'DAP (18-46-0) - 87 kg/acre', 'MOP (60% K) - 100 kg/acre'], 'organic': 'FYM - 5-6 tons/acre'},
    }

    @classmethod
    def get_growth_guidance(cls, crop: str) -> Dict:
        """Get growth guidance and fertilizer requirements for a crop."""
        guidance = cls.GROWTH_GUIDANCE.get(crop.lower(), {})
        fertilizers = cls.FERTILIZER_GUIDANCE.get(crop.lower(), {
            'npk': {'N': 60, 'P': 30, 'K': 30}, 
            'fertilizers': ['Urea (46% N) - 130 kg/acre', 'DAP (18-46-0) - 65 kg/acre', 'MOP (60% K) - 50 kg/acre'], 
            'organic': 'FYM - 5-6 tons/acre'
        })
        
        if not guidance:
            return {
                'crop': crop, 
                'duration': '120-150 days', 
                'stages': [
                    {'week': 'Week 1-3', 'stage': 'Germination', 'action': 'Ensure proper seed depth (4-5cm). Irrigate if soil is dry.'},
                    {'week': 'Week 4-8', 'stage': 'Vegetative/Tillering', 'action': 'First irrigation at 21 days. Apply nitrogen fertilizer.'},
                    {'week': 'Week 9-12', 'stage': 'Stem Extension', 'action': 'Second irrigation. Watch for yellow rust disease.'},
                    {'week': 'Week 13-16', 'stage': 'Flowering/Heading', 'action': 'Critical irrigation stage. Apply micronutrients if needed.'},
                    {'week': 'Week 17-20', 'stage': 'Grain Filling', 'action': 'Final irrigation when grains are forming. Protect from birds.'},
                    {'week': 'Week 21+', 'stage': 'Harvest', 'action': 'Harvest when grain moisture is 12-14%. Store properly.'}
                ],
                'fertilizers': fertilizers
            }
        return {'crop': crop, **guidance, 'fertilizers': fertilizers}

# NEURAL NETWORK MODEL (from crop-prediction)
# ============================================================================

class Net_64_128_64(nn.Module):
    """Neural Network for Crop Prediction"""
    def __init__(self, input_size: int, num_classes: int):
        super(Net_64_128_64, self).__init__()
        self.fc1 = nn.Linear(input_size, 64)
        self.fc2 = nn.Linear(64, 128)
        self.fc3 = nn.Linear(128, 64)
        self.fc4 = nn.Linear(64, num_classes)

    def forward(self, x):
        x = F.selu(self.fc1(x))
        x = F.selu(self.fc2(x))
        x = F.selu(self.fc3(x))
        x = self.fc4(x)
        return F.softmax(x, dim=1)


# ============================================================================
# COMMODITY CLASS (from price prediction)
# ============================================================================

class Commodity:
    """Price prediction model for a single commodity"""
    
    def __init__(self, csv_name: str, data_dir: str):
        self.name = csv_name.replace('.csv', '')
        dataset = pd.read_csv(os.path.join(data_dir, csv_name))
        self.df = dataset
        self.X = dataset.iloc[:, :-1].values  # Month, Year, Rainfall
        self.Y = dataset.iloc[:, 3].values     # WPI
        
        # Train Decision Tree Regressor
        import random
        depth = random.randrange(7, 18)
        self.regressor = DecisionTreeRegressor(max_depth=depth)
        self.regressor.fit(self.X, self.Y)

        # Dependency-free exact SHAP explainer (training data = background)
        self.explainer = ShapExplainer(self.regressor, self.X, ["Month", "Year", "Rainfall"])
    
    def get_predicted_value(self, value: List[float]) -> float:
        """Get predicted WPI for [month, year, rainfall]"""
        if value[1] >= 2019:
            fsa = np.array(value).reshape(1, 3)
            return self.regressor.predict(fsa)[0]
        else:
            # Historical lookup
            c = self.X[:, 0:2]
            x = [i.tolist() for i in c]
            fsa = [value[0], value[1]]
            for i in range(len(x)):
                if x[i] == fsa:
                    return self.Y[i]
            return self.Y[0]  # Fallback

    def get_shap_values(self, value: List[float]) -> Dict[str, Any]:
        """Exact SHAP values for a [month, year, rainfall] input."""
        phi, expected_value, prediction = self.explainer.explain(np.array(value, dtype=float))
        return {
            "feature_names": ["Month", "Year", "Rainfall"],
            "values": [round(float(v), 4) for v in phi],
            "expected_value": round(float(expected_value), 4),
            "prediction": round(float(prediction), 4),
            "method": "exact-shap-interventional",
        }

    def get_price_history(self) -> List[Dict[str, Any]]:
        """Full WPI series: actual CSV data, model-estimated past months, and
        AI forecast for the rest of the current year.

        - ``source == 'actual'``: rows from the training CSV (projected=False).
        - ``source == 'estimated'``: model-generated values for months that
          have already passed since the CSV data ended (projected=False, so they
          join the historical line on the chart).
        - ``source == 'forecast'``: model-generated values for upcoming months
          of the current year (projected=True).
        """
        history = []
        for _, row in self.df.iterrows():
            history.append({
                "month": int(row.iloc[0]),
                "year": int(row.iloc[1]),
                "wpi": float(row.iloc[3]),
                "projected": False,
                "source": "actual",
            })
        now = datetime.now()
        cur_year, cur_month = now.year, now.month
        last_year = history[-1]["year"] if history else 0
        # Model-estimated past months (after CSV end up to the current month)
        for year in range(last_year + 1, cur_year + 1):
            end_month = cur_month if year == cur_year else 12
            for month in range(1, end_month + 1):
                try:
                    rainfall = ANNUAL_RAINFALL[month - 1]
                    pred = float(self.regressor.predict([[month, year, rainfall]])[0])
                    history.append({
                        "month": month,
                        "year": year,
                        "wpi": round(pred, 2),
                        "projected": False,
                        "source": "estimated",
                    })
                except Exception:
                    break
        # AI forecast for the remaining months of the current year
        for month in range(cur_month + 1, 13):
            try:
                rainfall = ANNUAL_RAINFALL[month - 1]
                pred = float(self.regressor.predict([[month, cur_year, rainfall]])[0])
                history.append({
                    "month": month,
                    "year": cur_year,
                    "wpi": round(pred, 2),
                    "projected": True,
                    "source": "forecast",
                })
            except Exception:
                break
        return history

    def get_crop_name(self) -> str:
        return self.name


# ============================================================================
# DEPENDENCY-FREE SHAP
# Exact SHAP (Shapley) values for a regression model, computed from the
# definition over all feature subsets, using the training data as the
# background distribution (interventional SHAP, same game as
# shap.TreeExplainer(feature_perturbation="interventional")).
# Pure numpy + model.predict — no external `shap` package required.
# ============================================================================

class ShapExplainer:
    """Exact interventional SHAP for small feature sets (pure numpy).

    For a model f and background matrix B, with instance x and subset S of
    features, define v(S) = mean_b f(x_S, b_{~S}) where features in S are
    fixed to the instance values and the rest are drawn from B. The SHAP
    value of feature j is then

        phi_j = sum_{S not containing j} |S|!(M-|S|-1)!/M! * (v(S ∪ {j}) - v(S))

    This enumerates all 2^M subsets, which is exact and fast when M is small
    (M = 3 for the price features Month, Year, Rainfall). Additivity holds:
    sum_j phi_j = f(x) - v(empty).
    """

    def __init__(self, model, background: np.ndarray, feature_names: List[str]):
        self.model = model
        self.background = np.asarray(background, dtype=np.float64)
        self.n_background = self.background.shape[0]
        self.n_features = self.background.shape[1]
        self.feature_names = list(feature_names)
        self.M = self.n_features
        # w[s] = s!(M-s-1)!/M! for subset sizes s = 0..M-1
        self.weights = np.array([
            math.factorial(s) * math.factorial(self.M - s - 1) / math.factorial(self.M)
            for s in range(self.M)
        ], dtype=np.float64)

    def _subset_expectations(self, x: np.ndarray) -> Dict[frozenset, float]:
        """v(S) for every subset S of features (2^M evaluations)."""
        x = np.asarray(x, dtype=np.float64).reshape(-1)
        values: Dict[frozenset, float] = {}
        cols = np.arange(self.M)
        for r in range(self.M + 1):
            for comb in itertools.combinations(range(self.M), r):
                S = frozenset(comb)
                keep = np.zeros(self.M, dtype=bool)
                keep[list(S)] = True
                X_rep = np.tile(x, (self.n_background, 1))
                X_rep[:, ~keep] = self.background[:, ~keep]
                values[S] = float(np.mean(self.model.predict(X_rep)))
        return values

    def explain(self, x: np.ndarray) -> Tuple[np.ndarray, float, float]:
        """Return (shap_values[n_features], expected_value, prediction)."""
        x = np.asarray(x, dtype=np.float64).reshape(-1)
        values = self._subset_expectations(x)
        phi = np.zeros(self.M)
        full = frozenset(range(self.M))
        for j in range(self.M):
            total = 0.0
            for S, v in values.items():
                if j in S:
                    continue
                total += self.weights[len(S)] * (values[S | frozenset([j])] - v)
            phi[j] = total
        expected_value = values[frozenset()]
        prediction = values[full]
        return phi, expected_value, prediction

# ============================================================================
# MODEL MANAGER
# ============================================================================

class ModelManager:
    """Manages both crop prediction and price prediction models"""
    
    def __init__(self):
        self.crop_model = None
        self.crop_encoder = None
        self.normalization = None
        self.commodities: Dict[str, Commodity] = {}
        self._load_models()
    
    def _load_models(self):
        """Load all models and data"""
        logger.info("Loading models...")
        
        # Load crop prediction model (41 crops) - optional, uses fallback if missing
        try:
            self.crop_model = Net_64_128_64(7, 41)
            crop_model_path = os.path.join(MODELS_DIR, "crop", "baseline_42crops.hdf5")
            if os.path.exists(crop_model_path):
                self.crop_model.load_state_dict(torch.load(crop_model_path, map_location='cpu'))
                self.crop_model.eval()
                logger.info("Loaded crop prediction model")
            else:
                logger.warning("Crop model not found, using rule-based prediction")
                self.crop_model = None
            
            # Load encoder
            encoder_path = os.path.join(MODELS_DIR, "crop", "encoder_42crops.pkl")
            if os.path.exists(encoder_path):
                with open(encoder_path, "rb") as file:
                    self.crop_encoder = pickle.load(file)
            else:
                self.crop_encoder = None
                
            # Load normalization parameters
            norm_path = os.path.join(MODELS_DIR, "crop", "normalization_42crops.npz")
            if os.path.exists(norm_path):
                self.normalization = np.load(norm_path)
            else:
                self.normalization = None
        except Exception as e:
            logger.warning(f"Could not load crop prediction models: {e}")
            self.crop_model = None
            self.crop_encoder = None
            self.normalization = None
        
        # Load price prediction commodities
        commodity_files = {
            "arhar": "Arhar.csv", "bajra": "Bajra.csv", "barley": "Barley.csv",
            "copra": "Copra.csv", "cotton": "Cotton.csv", "sesamum": "Sesamum.csv",
            "gram": "Gram.csv", "groundnut": "Groundnut.csv", "jowar": "Jowar.csv",
            "maize": "Maize.csv", "masoor": "Masoor.csv", "moong": "Moong.csv",
            "niger": "Niger.csv", "paddy": "Paddy.csv", "ragi": "Ragi.csv",
            "rape": "Rape.csv", "jute": "Jute.csv", "safflower": "Safflower.csv",
            "soyabean": "Soyabean.csv", "sugarcane": "Sugarcane.csv",
            "sunflower": "Sunflower.csv", "urad": "Urad.csv", "wheat": "Wheat.csv"
        }
        
        for name, filename in commodity_files.items():
            try:
                self.commodities[name] = Commodity(filename, PRICE_DATA_DIR)
                logger.info(f"Loaded price model for: {name}")
            except Exception as e:
                logger.warning(f"Failed to load {name}: {e}")
        
        logger.info(f"Loaded {len(self.commodities)} price models")
    
    def get_rainfall(self, state: str, district: str, month: str) -> float:
        """Get rainfall data for state/district/month"""
        df = pd.read_csv(RAINFALL_DATA_PATH)
        # Convert to uppercase for case-insensitive matching
        state_upper = state.upper()
        district_upper = district.upper()
        
        # Create uppercase versions for matching
        df['STATE_UPPER'] = df['STATE_UT_NAME'].str.upper()
        df['DISTRICT_UPPER'] = df['DISTRICT'].str.upper()
        
        row = df[(df['STATE_UPPER'] == state_upper) & (df['DISTRICT_UPPER'] == district_upper)]
        rainfall = row[month].values
        if rainfall.shape[0] == 0:
            available_states = df['STATE_UT_NAME'].unique().tolist()
            available_districts = df[df['STATE_UPPER'] == state_upper]['DISTRICT'].unique().tolist() if state_upper in df['STATE_UPPER'].unique() else []
            raise ValueError(
                f"Unable to match month:{month} with state:{state} district:{district}. "
                f"Available states: {available_states[:5]}... "
                f"Available districts for {state}: {available_districts[:5]}..."
            )
        return float(rainfall[0])
    
    def get_temperature_humidity(self, month: str, rainfall: float) -> Tuple[float, float]:
        """
        Estimate temperature and humidity based on month and rainfall.
        Uses Indian climate patterns - no external API needed.
        
        Args:
            month: 3-letter month code (JAN, FEB, etc.)
            rainfall: Monthly rainfall in mm
            
        Returns:
            Tuple of (temperature_celsius, humidity_percent)
        """
        month = month.upper()
        
        # Base temperature by month (Indian climate averages)
        # Peak summer: MAY-JUN (35-40°C), Winter: DEC-JAN (15-25°C)
        base_temps = {
            'JAN': 20, 'FEB': 23, 'MAR': 28, 'APR': 33,
            'MAY': 36, 'JUN': 34, 'JUL': 30, 'AUG': 29,
            'SEP': 29, 'OCT': 28, 'NOV': 24, 'DEC': 21
        }
        
        base_temp = base_temps.get(month, 25)
        
        # Adjust temperature based on rainfall (cooling effect)
        # More rainfall = slightly cooler, less rainfall = hotter
        if rainfall > 200:  # Heavy monsoon
            temp_adjustment = -3
        elif rainfall > 100:  # Moderate rain
            temp_adjustment = -1
        elif rainfall < 20:  # Very dry
            temp_adjustment = 2
        else:
            temp_adjustment = 0
            
        temperature = base_temp + temp_adjustment
        
        # Estimate humidity based on rainfall and month
        # Monsoon months (JUN-SEP) have higher humidity
        if month in ['JUN', 'JUL', 'AUG', 'SEP']:
            base_humidity = 75
        elif month in ['OCT', 'NOV']:
            base_humidity = 65
        elif month in ['DEC', 'JAN', 'FEB']:
            base_humidity = 55
        else:  # MAR-MAY (summer)
            base_humidity = 50
        
        # Adjust humidity based on rainfall
        if rainfall > 250:
            humidity_adjustment = 15
        elif rainfall > 150:
            humidity_adjustment = 10
        elif rainfall > 50:
            humidity_adjustment = 5
        else:
            humidity_adjustment = -5
            
        humidity = min(95, base_humidity + humidity_adjustment)  # Cap at 95%
        
        logger.info(f"Estimated climate for {month}: {temperature:.1f}°C, {humidity}% humidity (rainfall: {rainfall}mm)")
        
        return temperature, humidity
    
    def predict_crop(self, nitrogen: float, phosphorous: float, potassium: float,
                     temperature: float, humidity: float, ph: float, 
                     rainfall: float) -> Tuple[str, float, Dict[int, float]]:
        """
        Predict the best crop based on input features.
        Returns: (crop_name, confidence, all_probabilities)
        Uses ML model if available, otherwise falls back to rule-based recommendation.
        """
        logger.info(f"PREDICT CROP INPUT: N={nitrogen}, P={phosphorous}, K={potassium}, T={temperature}, H={humidity}, pH={ph}, Rain={rainfall}")
        
        # If ML model is not available, use rule-based fallback
        if self.crop_model is None or self.crop_encoder is None or self.normalization is None:
            logger.info("Using RULE-BASED prediction (ML model not available)")
            result = self._predict_crop_rule_based(nitrogen, phosphorous, potassium, temperature, humidity, ph, rainfall)
            logger.info(f"RULE-BASED RESULT: crop={result[0]}, confidence={result[1]}")
            return result
        
        x = (nitrogen, phosphorous, potassium, temperature, humidity, ph, rainfall)
        input_vector = torch.tensor(x, dtype=torch.float32)
        
        # Normalize
        mean = self.normalization["mean"]
        std = self.normalization["std"]
        input_vector = (input_vector - mean) / std
        
        # Predict
        with torch.no_grad():
            prediction = self.crop_model(input_vector.unsqueeze(0))
        
        # Get probabilities for all classes
        probabilities = prediction.squeeze().tolist()
        probs_dict = {i: prob for i, prob in enumerate(probabilities)}
        
        # Get top prediction
        predicted_idx = prediction.argmax().item()
        confidence = probabilities[predicted_idx]
        crop_name = self.crop_encoder.inverse_transform([predicted_idx])[0]
        
        return crop_name, confidence, probs_dict
    
    def _predict_crop_rule_based(self, nitrogen: float, phosphorous: float, potassium: float,
                                  temperature: float, humidity: float, ph: float, 
                                  rainfall: float) -> Tuple[str, float, Dict[int, float]]:
        """
        Rule-based crop recommendation when ML model is not available.
        Smart heuristic based on soil NPK, temperature, humidity, and rainfall.
        """
        logger.info(f"RULE-BASED INPUT: N={nitrogen}, P={phosphorous}, K={potassium}, T={temperature}, H={humidity}, pH={ph}, Rain={rainfall}")
        
        # Calculate NPK score for better classification
        npk_score = nitrogen + phosphorous + potassium
        npk_avg = npk_score / 3
        
        # Initialize all crops with suitability scores
        crop_scores = {}
        
        # Rice - needs high N, high rainfall, warm temperature
        rice_score = 0
        if nitrogen > 80: rice_score += 30
        if phosphorous > 40: rice_score += 20
        if potassium > 40: rice_score += 20
        if rainfall > 1000: rice_score += 30
        if temperature > 20 and temperature < 35: rice_score += 15
        if ph < 7.0: rice_score += 10
        crop_scores['rice'] = rice_score
        
        # Wheat - needs moderate N, moderate rainfall, cooler temperature
        wheat_score = 0
        if nitrogen > 60 and nitrogen < 120: wheat_score += 30
        if phosphorous > 30: wheat_score += 25
        if potassium > 20: wheat_score += 15
        if rainfall > 400 and rainfall < 800: wheat_score += 25
        if temperature > 15 and temperature < 25: wheat_score += 20
        crop_scores['wheat'] = wheat_score
        
        # Maize - needs high N, moderate rainfall, warm
        maize_score = 0
        if nitrogen > 70: maize_score += 35
        if phosphorous > 40: maize_score += 20
        if potassium > 40: maize_score += 15
        if rainfall > 500 and rainfall < 1000: maize_score += 25
        if temperature > 20 and temperature < 32: maize_score += 15
        crop_scores['maize'] = maize_score
        
        # Cotton - needs high P, good rainfall, warm
        cotton_score = 0
        if nitrogen > 50: cotton_score += 20
        if phosphorous > 50: cotton_score += 35
        if potassium > 30: cotton_score += 20
        if rainfall > 600 and rainfall < 1200: cotton_score += 25
        if temperature > 22 and temperature < 35: cotton_score += 20
        crop_scores['cotton'] = cotton_score
        
        # Groundnut - needs moderate N, high P, moderate rainfall
        groundnut_score = 0
        if nitrogen > 20 and nitrogen < 60: groundnut_score += 25
        if phosphorous > 40: groundnut_score += 30
        if potassium > 20: groundnut_score += 20
        if rainfall > 400 and rainfall < 800: groundnut_score += 20
        crop_scores['groundnut'] = groundnut_score
        
        # Sugarcane - needs very high NPK, high rainfall
        sugarcane_score = 0
        if nitrogen > 100: sugarcane_score += 35
        if phosphorous > 50: sugarcane_score += 25
        if potassium > 50: sugarcane_score += 20
        if rainfall > 1200: sugarcane_score += 30
        if temperature > 25: sugarcane_score += 10
        crop_scores['sugarcane'] = sugarcane_score
        
        # Pulses (Gram, Moong, Arhar) - low N requirement (nitrogen fixing)
        gram_score = 0
        if nitrogen < 40: gram_score += 35  # Low N needed
        if phosphorous > 30: gram_score += 30
        if potassium > 20: gram_score += 15
        if rainfall > 300 and rainfall < 700: gram_score += 20
        crop_scores['gram'] = gram_score
        
        moong_score = 0
        if nitrogen < 35: moong_score += 35
        if phosphorous > 25: moong_score += 25
        if potassium > 15: moong_score += 15
        if rainfall > 250 and rainfall < 600: moong_score += 25
        crop_scores['moong'] = moong_score
        
        arhar_score = 0
        if nitrogen < 40: arhar_score += 30
        if phosphorous > 35: arhar_score += 25
        if potassium > 20: arhar_score += 20
        if rainfall > 500 and rainfall < 900: arhar_score += 25
        crop_scores['arhar'] = arhar_score
        
        # Millets (Bajra, Jowar) - low NPK, low rainfall
        bajra_score = 0
        if nitrogen < 50: bajra_score += 30
        if phosphorous < 30: bajra_score += 20
        if rainfall < 400: bajra_score += 35
        if temperature > 25: bajra_score += 15
        crop_scores['bajra'] = bajra_score
        
        jowar_score = 0
        if nitrogen < 60: jowar_score += 25
        if phosphorous < 35: jowar_score += 20
        if rainfall > 300 and rainfall < 600: jowar_score += 25
        crop_scores['jowar'] = jowar_score
        
        # Additional Cereals
        barley_score = 0
        if nitrogen > 50 and nitrogen < 90: barley_score += 30
        if phosphorous > 25: barley_score += 25
        if rainfall > 350 and rainfall < 700: barley_score += 25
        if temperature > 12 and temperature < 22: barley_score += 20
        crop_scores['barley'] = barley_score
        
        ragi_score = 0
        if nitrogen > 40 and nitrogen < 80: ragi_score += 30
        if phosphorous > 25: ragi_score += 25
        if rainfall > 500 and rainfall < 1000: ragi_score += 25
        if temperature > 20 and temperature < 30: ragi_score += 20
        crop_scores['ragi'] = ragi_score
        
        # Oilseeds
        sesamum_score = 0
        if nitrogen < 40: sesamum_score += 30
        if phosphorous > 20: sesamum_score += 25
        if rainfall > 300 and rainfall < 600: sesamum_score += 25
        if temperature > 25: sesamum_score += 20
        crop_scores['sesamum'] = sesamum_score
        
        safflower_score = 0
        if nitrogen < 45: safflower_score += 30
        if phosphorous > 20: safflower_score += 25
        if rainfall < 400: safflower_score += 30
        if temperature > 20: safflower_score += 15
        crop_scores['safflower'] = safflower_score
        
        niger_score = 0
        if nitrogen < 40: niger_score += 30
        if phosphorous > 20: niger_score += 25
        if rainfall > 300 and rainfall < 700: niger_score += 25
        if temperature > 20: niger_score += 20
        crop_scores['niger'] = niger_score
        
        rape_score = 0
        if nitrogen > 60 and nitrogen < 100: rape_score += 30
        if phosphorous > 35: rape_score += 25
        if rainfall > 400 and rainfall < 800: rape_score += 25
        if temperature > 15 and temperature < 25: rape_score += 20
        crop_scores['rape'] = rape_score
        
        # Cash Crops
        jute_score = 0
        if nitrogen > 60: jute_score += 30
        if phosphorous > 35: jute_score += 20
        if rainfall > 1200: jute_score += 35
        if temperature > 25: jute_score += 15
        crop_scores['jute'] = jute_score
        
        copra_score = 0  # Coconut
        if nitrogen > 70: copra_score += 25
        if phosphorous > 35: copra_score += 20
        if potassium > 100: copra_score += 30
        if rainfall > 1500: copra_score += 25
        if temperature > 25: copra_score += 15
        crop_scores['copra'] = copra_score
        
        # Vegetables
        onion_score = 0
        if nitrogen > 70: onion_score += 30
        if phosphorous > 35: onion_score += 25
        if potassium > 70: onion_score += 25
        if rainfall > 400 and rainfall < 800: onion_score += 20
        crop_scores['onion'] = onion_score
        
        potato_score = 0
        if nitrogen > 70: potato_score += 30
        if phosphorous > 45: potato_score += 25
        if potassium > 90: potato_score += 30
        if rainfall > 400 and rainfall < 800: potato_score += 15
        if temperature > 15 and temperature < 22: potato_score += 15
        crop_scores['potato'] = potato_score
        
        tomato_score = 0
        if nitrogen > 90: tomato_score += 30
        if phosphorous > 55: tomato_score += 25
        if potassium > 110: tomato_score += 30
        if rainfall > 500 and rainfall < 1000: tomato_score += 15
        crop_scores['tomato'] = tomato_score
        
        # Fruits
        apple_score = 0
        if nitrogen > 40 and nitrogen < 80: apple_score += 25
        if phosphorous > 25: apple_score += 25
        if potassium > 50: apple_score += 25
        if rainfall > 800 and rainfall < 1500: apple_score += 25
        if temperature > 10 and temperature < 22: apple_score += 15
        crop_scores['apple'] = apple_score
        
        orange_score = 0
        if nitrogen > 50 and nitrogen < 100: orange_score += 25
        if phosphorous > 35: orange_score += 25
        if potassium > 50: orange_score += 25
        if rainfall > 800 and rainfall < 1400: orange_score += 25
        if temperature > 20 and temperature < 28: orange_score += 15
        crop_scores['orange'] = orange_score
        
        banana_score = 0
        if nitrogen > 100: banana_score += 30
        if phosphorous > 45: banana_score += 25
        if potassium > 140: banana_score += 35
        if rainfall > 1400: banana_score += 25
        if temperature > 26: banana_score += 15
        crop_scores['banana'] = banana_score
        
        papaya_score = 0
        if nitrogen > 70: papaya_score += 30
        if phosphorous > 35: papaya_score += 25
        if potassium > 90: papaya_score += 30
        if rainfall > 900 and rainfall < 1600: papaya_score += 25
        if temperature > 25: papaya_score += 15
        crop_scores['papaya'] = papaya_score
        
        # Additional Pulses
        masoor_score = 0
        if nitrogen < 35: masoor_score += 35
        if phosphorous > 25: masoor_score += 30
        if potassium > 15: masoor_score += 15
        if rainfall > 350 and rainfall < 750: masoor_score += 20
        crop_scores['masoor'] = masoor_score
        
        urad_score = 0
        if nitrogen < 35: urad_score += 35
        if phosphorous > 25: urad_score += 30
        if potassium > 15: urad_score += 15
        if rainfall > 450 and rainfall < 900: urad_score += 20
        crop_scores['urad'] = urad_score
        
        # Other crops
        coffee_score = 0
        if nitrogen > 60 and nitrogen < 120: coffee_score += 30
        if phosphorous > 30: coffee_score += 25
        if potassium > 50: coffee_score += 25
        if rainfall > 1000 and rainfall < 2000: coffee_score += 30
        if temperature > 18 and temperature < 28: coffee_score += 20
        crop_scores['coffee'] = coffee_score
        
        tea_score = 0
        if nitrogen > 80: tea_score += 30
        if phosphorous > 30: tea_score += 20
        if potassium > 40: tea_score += 20
        if rainfall > 1200: tea_score += 35
        if temperature > 18 and temperature < 28: tea_score += 15
        crop_scores['tea'] = tea_score
        
        # Rank crops by agronomic factor-match — the SAME 0-100 scoring shown in
        # the XAI breakdown — so the recommended crop always carries the highest
        # match % and the card/ring/confidence stay perfectly consistent.
        RULE_TO_REQ = {'rape': 'rapeseed'}
        match_rank = {}
        for cname in crop_scores:
            req_name = RULE_TO_REQ.get(cname, cname)
            if req_name in CropExplainability.CROP_REQUIREMENTS:
                fs = CropExplainability.compute_factor_scores(
                    req_name, nitrogen, phosphorous, potassium, ph, temperature, rainfall
                )
                match_rank[cname] = round(sum(fs.values()) / len(fs), 1)
            else:
                # No requirements table — cap the heuristic score at 75 so these
                # crops never win over a properly scored candidate.
                match_rank[cname] = min(75.0, crop_scores[cname])

        best_crop = max(match_rank, key=match_rank.get)
        best_score = match_rank[best_crop]

        # Confidence mirrors the factor match % (capped at 95%), same as the card/ring.
        confidence = min(0.95, best_score / 100.0)

        logger.info(f"RULE-BASED MATCH: {dict(sorted(match_rank.items(), key=lambda x: x[1], reverse=True))}")
        logger.info(f"SELECTED: {best_crop} with match {best_score}%, confidence {confidence}")
        
        # Create probability distribution
        all_crops = ["rice", "wheat", "maize", "cotton", "sugarcane", "groundnut", "bajra", "jowar",
                     "tur", "gram", "moong", "arhar", "masoor", "urad", "barley", "ragi",
                     "sunflower", "sesamum", "safflower", "niger", "rape", "soyabean", "jute",
                     "copra", "onion", "potato", "tomato", "apple", "orange", "banana", "papaya",
                     "coffee", "tea"]
        
        # Sort crops by match to get top 5
        sorted_crops = sorted(match_rank.items(), key=lambda x: x[1], reverse=True)
        top_5 = sorted_crops[:5]
        
        # Calculate probabilities — directly proportional to factor-match so the
        # ranking, the recommended crop, and the top-5 list all agree.
        probs_dict = {}
        
        for i, crop_name in enumerate(all_crops):
            if crop_name in match_rank:
                probs_dict[i] = min(0.95, match_rank[crop_name] / 100.0)
            else:
                probs_dict[i] = 0.01
        
        # Ensure best crop gets the pre-computed confidence
        selected_idx = all_crops.index(best_crop) if best_crop in all_crops else 0
        probs_dict[selected_idx] = confidence
        
        logger.info(f"TOP 5 CROPS: {top_5}")
        
        return best_crop, confidence, probs_dict
    
    def predict_price(self, crop_name: str, month: int, year: int, 
                      rainfall: float) -> Optional[Tuple[float, str]]:
        """
        Predict price for a crop using WPI proxy if needed.
        Now supports ALL 22 predicted crops!
        
        Returns:
            Tuple of (price in INR/quintal, proxy_info) or None if not available
            proxy_info indicates if a proxy model was used
        """
        crop_name_lower = crop_name.lower()
        
        # Check if crop has direct price model
        if crop_name_lower in self.commodities:
            commodity = self.commodities[crop_name_lower]
            wpi = commodity.get_predicted_value([float(month), year, rainfall])
            base_price = BASE_PRICES.get(crop_name.capitalize(), 0)
            price = (wpi * base_price) / 100
            return round(price, 2), "direct"
        
        # Check if crop has a proxy mapping
        if crop_name_lower in CROP_WPI_PROXY:
            proxy_crop = CROP_WPI_PROXY[crop_name_lower]
            if proxy_crop in self.commodities:
                commodity = self.commodities[proxy_crop]
                wpi = commodity.get_predicted_value([float(month), year, rainfall])
                base_price = BASE_PRICES.get(crop_name.capitalize(), 0)
                price = (wpi * base_price) / 100
                logger.info(f"Using {proxy_crop} WPI model for {crop_name} price prediction")
                return round(price, 2), f"proxy:{proxy_crop}"
        
        return None

    def get_price_commodity(self, crop_name: str) -> Optional[str]:
        """Return the commodity whose price model prices this crop (direct or proxy)."""
        name = crop_name.lower().strip()
        if name in self.commodities:
            return name
        proxy = CROP_WPI_PROXY.get(name)
        if proxy and proxy in self.commodities:
            return proxy
        mapped = CROP_TO_PRICE_MAPPING.get(name)
        if mapped and mapped in self.commodities:
            return mapped
        return None


# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

# Initialize model manager
model_manager = ModelManager()

# Create FastAPI app
app = FastAPI(
    title="Unified Crop Recommendation & Price Prediction API",
    description="Integrates crop suitability prediction with market price forecasting",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class CropPredictionInput(BaseModel):
    nitrogen: float = Field(..., ge=0, le=200, description="Nitrogen content in soil (mg/kg)")
    phosphorous: float = Field(..., ge=0, le=200, description="Phosphorous content in soil (mg/kg)")
    potassium: float = Field(..., ge=0, le=200, description="Potassium content in soil (mg/kg)")
    ph: float = Field(..., ge=0, le=14, description="pH level of soil")
    state: str = Field(..., description="Indian state name (e.g., 'KARNATAKA')")
    district: str = Field(..., description="District name (e.g., 'BANGALORE')")
    month: str = Field(..., description="3-letter month (e.g., 'JAN', 'FEB')")


class UnifiedPredictionInput(BaseModel):
    nitrogen: float = Field(..., ge=0, le=200, description="Nitrogen content in soil (mg/kg)")
    phosphorous: float = Field(..., ge=0, le=200, description="Phosphorous content in soil (mg/kg)")
    potassium: float = Field(..., ge=0, le=200, description="Potassium content in soil (mg/kg)")
    ph: float = Field(..., ge=0, le=14, description="pH level of soil")
    state: str = Field(..., description="Indian state name")
    district: str = Field(..., description="District name")
    month: str = Field(..., description="3-letter month (e.g., 'JAN')")
    year: int = Field(default_factory=lambda: datetime.now().year, description="Year for price prediction")


class UnifiedPredictionOutput(BaseModel):
    recommended_crop: str = Field(..., description="Best crop for given conditions")
    confidence: float = Field(..., description="Prediction confidence (0-1)")
    predicted_price: Optional[float] = Field(None, description="Predicted price in INR/quintal")
    price_available: bool = Field(..., description="Whether price prediction is available")
    explanation: str = Field(..., description="Farmer-friendly explanation of why this crop was recommended")
    soil_analysis: Dict[str, Any] = Field(..., description="Soil condition analysis in simple terms")
    growth_advice: Dict[str, Any] = Field(..., description="Week-by-week growth guidance for the crop")
    details: Dict[str, Any] = Field(..., description="Additional details")
    xai_breakdown: Optional[Dict[str, Any]] = Field(None, description="SHAP-style factor breakdown for the recommendation")
    price_history: Optional[Dict[str, Any]] = Field(None, description="Historical WPI series for the recommended crop")


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Health check endpoint - AgriSarathi AI"""
    return {
        "name": "AgriSarathi AI",
        "tagline": "Smart Crop Recommendation & Price Forecasting",
        "message": "Unified Crop Recommendation & Price Prediction API",
        "version": "2.0.0",
        "features": [
            "41-crop prediction model",
            "Price forecasting for all crops",
            "Top 5 crop recommendations",
            "Crop comparison & ranking"
        ],
        "crop_model_loaded": model_manager.crop_model is not None,
        "price_models_loaded": len(model_manager.commodities),
        "docs": "/docs"
    }


@app.get("/supported-crops")
async def get_supported_crops():
    """Get list of supported crops and their price availability"""
    # Get all predicted crops (if ML model is loaded) or use fallback list
    if model_manager.crop_encoder is not None:
        all_predicted_crops = list(model_manager.crop_encoder.classes_)
    else:
        # Fallback crop list when ML model is not available
        all_predicted_crops = ["rice", "cotton", "maize", "wheat", "groundnut", "gram", "moong", "bajra", "jute", "sugarcane"]
    
    # Get direct price models (23 crops)
    direct_models = list(model_manager.commodities.keys())
    
    # Get proxy mappings (for crops without direct WPI data)
    proxy_mappings = {crop: proxy for crop, proxy in CROP_WPI_PROXY.items() 
                     if crop not in ["cotton", "jute", "maize"]}  # Exclude direct matches
    
    return {
        "all_predicted_crops": all_predicted_crops,
        "total_predicted_crops": len(all_predicted_crops),
        "all_crops_have_price_prediction": True,
        "direct_price_models": direct_models,
        "proxy_mappings": proxy_mappings,
        "price_only_crops": PRICE_ONLY_CROPS,
        "base_prices_available": list(BASE_PRICES.keys()),
        "note": "All predicted crops now have price prediction via direct or proxy models!"
    }


@app.get("/locations")
async def get_locations():
    """
    Get all available states and their districts from the rainfall data.
    Used to populate dynamic dropdowns in the frontend.
    """
    try:
        import pandas as pd
        
        # Read the rainfall data
        df = pd.read_csv(RAINFALL_DATA_PATH)
        
        # Group by state and get districts
        locations = {}
        for state in df['STATE_UT_NAME'].unique():
            districts = df[df['STATE_UT_NAME'] == state]['DISTRICT'].unique().tolist()
            locations[state] = sorted(districts)
        
        return {
            "states": sorted(locations.keys()),
            "state_districts": locations,
            "total_states": len(locations),
            "total_districts": sum(len(d) for d in locations.values())
        }
    except Exception as e:
        logger.error(f"Error loading locations: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load location data: {str(e)}")


@app.post("/predict-crop")
async def predict_crop_only(input_data: CropPredictionInput):
    """
    Predict only the best crop (no price prediction).
    This is a standalone crop recommendation endpoint.
    """
    try:
        # Get environmental data
        rainfall = model_manager.get_rainfall(
            input_data.state, input_data.district, input_data.month
        )
        temperature, humidity = model_manager.get_temperature_humidity(input_data.month, rainfall)
        
        # Predict crop
        crop, confidence, all_probs = model_manager.predict_crop(
            input_data.nitrogen,
            input_data.phosphorous,
            input_data.potassium,
            temperature,
            humidity,
            input_data.ph,
            rainfall
        )
        
        # Get all crop probabilities
        crop_probs = {}
        if model_manager.crop_encoder is not None:
            for idx, prob in all_probs.items():
                crop_name = model_manager.crop_encoder.inverse_transform([idx])[0]
                crop_probs[crop_name] = round(prob, 4)
        else:
            # Fallback: use crop names from rule-based prediction
            fallback_crops = ["rice", "cotton", "maize", "wheat", "groundnut", "gram", "moong", "bajra", "jute", "sugarcane"]
            for i, crop in enumerate(fallback_crops):
                crop_probs[crop] = all_probs.get(i, 0.05)
        
        # Sort by probability
        sorted_crops = sorted(crop_probs.items(), key=lambda x: x[1], reverse=True)
        
        # Check price availability using new proxy system
        price_info = model_manager.predict_price(crop, 1, 2024, 50.0)  # Test with dummy values
        price_available = price_info is not None
        
        return {
            "recommended_crop": crop,
            "confidence": round(confidence, 4),
            "environmental_data": {
                "temperature": round(temperature, 2),
                "humidity": round(humidity, 2),
                "rainfall": round(rainfall, 2)
            },
            "all_predictions": sorted_crops[:5],  # Top 5
            "price_available": price_available,
            "all_crops_now_supported": True
        }
        
    except Exception as e:
        logger.error(f"Crop prediction error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/predict-price")
async def predict_price_only(crop: str, month: int, year: int, rainfall: Optional[float] = None):
    """
    Predict price for a specific crop.
    If rainfall is not provided, uses annual average.
    """
    try:
        # Map crop name if needed
        mapped_crop = CROP_TO_PRICE_MAPPING.get(crop.lower(), crop.lower())
        
        # Use annual rainfall if not provided
        if rainfall is None:
            rainfall = ANNUAL_RAINFALL[month - 1]
        
        price_result = model_manager.predict_price(mapped_crop, month, year, rainfall)
        
        if price_result is None:
            return {
                "crop": crop,
                "mapped_crop": mapped_crop,
                "price_available": False,
                "message": f"No price model available for {crop}."
            }
        
        price, method = price_result
        
        return {
            "crop": crop,
            "mapped_crop": mapped_crop,
            "month": month,
            "year": year,
            "rainfall": rainfall,
            "predicted_price_inr_per_quintal": price,
            "price_available": True,
            "price_method": method
        }
        
    except Exception as e:
        logger.error(f"Price prediction error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/price-history")
async def price_history(crop: str):
    """Return the historical WPI series for a commodity (drives the trend chart)."""
    name = crop.lower().strip()
    commodity = model_manager.commodities.get(name)
    if commodity is None:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown commodity '{crop}'. Available: {sorted(model_manager.commodities.keys())}"
        )
    return {
        "commodity": commodity.name,
        "feature_names": ["Month", "Year", "Rainfall"],
        "points": commodity.get_price_history(),
    }

@app.post("/predict", response_model=UnifiedPredictionOutput)
async def unified_predict(input_data: UnifiedPredictionInput):
    """
    Unified prediction endpoint:
    1. Predicts best crop based on soil and environmental conditions
    2. Predicts price for the recommended crop (if available)
    
    Returns combined result with fallback handling for crops without price data.
    """
    try:
        # Step 1: Get environmental data
        logger.info(f"API INPUT DATA: N={input_data.nitrogen}, P={input_data.phosphorous}, K={input_data.potassium}, pH={input_data.ph}")
        logger.info(f"LOCATION: {input_data.district}, {input_data.state}, MONTH: {input_data.month}, YEAR: {input_data.year}")
        
        rainfall = model_manager.get_rainfall(
            input_data.state, input_data.district, input_data.month
        )
        temperature, humidity = model_manager.get_temperature_humidity(input_data.month, rainfall)
        logger.info(f"ENV DATA: rainfall={rainfall}, temp={temperature}, humidity={humidity}")
        
        # Step 2: Predict crop
        logger.info("Running crop prediction model")
        crop, confidence, all_probs = model_manager.predict_crop(
            input_data.nitrogen,
            input_data.phosphorous,
            input_data.potassium,
            temperature,
            humidity,
            input_data.ph,
            rainfall
        )
        logger.info(f"PREDICTION RESULT: crop={crop}, confidence={confidence}")
        logger.info(f"ALL PROBS: {all_probs}")
        
        # CRITICAL DEBUG: Verify crop value immediately after prediction
        logger.info(f"DEBUG - CROP VALUE AFTER PREDICT: '{crop}' (type: {type(crop)})")
        
        # Step 3: Map to price model crop name
        mapped_crop = CROP_TO_PRICE_MAPPING.get(crop, None)
        price_available = mapped_crop is not None and mapped_crop in model_manager.commodities
        
        # Step 4: Predict price for ALL crops (now using proxy models)
        predicted_price = None
        price_method = None
        month_num = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", 
                     "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"].index(input_data.month.upper()) + 1
        
        # Predict price for the recommended crop (now ALL 22 crops have price support!)
        logger.info(f"Predicting price for {crop}")
        price_rainfall = ANNUAL_RAINFALL[month_num - 1]
        price_result = model_manager.predict_price(
            crop, month_num, input_data.year, price_rainfall
        )
        
        if price_result:
            predicted_price, price_method = price_result
            price_available = True
        
        # Get top 5 crops with full price details
        # Now ALL crops have price prediction (direct or proxy)
        crop_probs = {}
        if model_manager.crop_encoder is not None:
            for idx, prob in all_probs.items():
                crop_name = model_manager.crop_encoder.inverse_transform([idx])[0]
                # Check if crop has direct model OR proxy mapping
                has_price = (crop_name in CROP_TO_PRICE_MAPPING or 
                            crop_name.lower() in CROP_WPI_PROXY or
                            crop_name.lower() in model_manager.commodities)
                crop_probs[crop_name] = {"probability": round(prob, 4), "has_price_prediction": has_price}
        else:
            # Fallback: use crop names from rule-based prediction
            # Order MUST match _predict_crop_rule_based's all_crops list
            fallback_crops = ["rice", "wheat", "maize", "cotton", "sugarcane", "groundnut", "bajra", "jowar",
                             "tur", "gram", "moong", "arhar", "masoor", "urad", "barley", "ragi",
                             "sunflower", "sesamum", "safflower", "niger", "rape", "soyabean", "jute",
                             "copra", "onion", "potato", "tomato", "apple", "orange", "banana", "papaya",
                             "coffee", "tea"]
            for i, crop_name in enumerate(fallback_crops):
                prob = all_probs.get(i, 0.05)
                has_price = (crop_name in CROP_TO_PRICE_MAPPING or 
                            crop_name.lower() in CROP_WPI_PROXY or
                            crop_name.lower() in model_manager.commodities)
                crop_probs[crop_name] = {"probability": round(prob, 4), "has_price_prediction": has_price}
        
        sorted_crops = sorted(crop_probs.items(), key=lambda x: x[1]["probability"], reverse=True)
        top_alternatives = sorted_crops[:5]  # Top 5 instead of top 3
        
        # Get full details (including price) for top 5 crops
        top_5_with_prices = []
        for rank, (crop_name, data) in enumerate(top_alternatives, 1):
            # Get price for this crop
            crop_price = None
            crop_price_method = None
            try:
                price_result = model_manager.predict_price(crop_name, month_num, input_data.year, price_rainfall)
                if price_result:
                    crop_price, crop_price_method = price_result
            except Exception as e:
                logger.warning(f"Could not get price for {crop_name}: {e}")

            # Dependency-free exact SHAP explanation for the price prediction
            price_shap = None
            shap_commodity = model_manager.get_price_commodity(crop_name)
            if shap_commodity:
                try:
                    shap_commodity_obj = model_manager.commodities[shap_commodity]
                    shap_info = shap_commodity_obj.get_shap_values(
                        [float(month_num), float(input_data.year), float(price_rainfall)]
                    )
                    shap_info["commodity"] = shap_commodity
                    price_shap = shap_info
                except Exception as e:
                    logger.warning(f"Could not compute SHAP for {crop_name}: {e}")

            # Agronomic match % (0-100) — SAME scoring as the XAI breakdown
            # (compute_factor_scores), so the card percentage and the
            # "AI Decision Breakdown" ring always agree with each other.
            match_scores = CropExplainability.compute_factor_scores(
                crop_name, input_data.nitrogen, input_data.phosphorous,
                input_data.potassium, input_data.ph, temperature, rainfall
            )
            match_percent = round(sum(match_scores.values()) / len(match_scores), 1)

            # Determine recommendation tag
            if rank == 1:
                tag = "Best Choice"
            elif rank <= 3:
                tag = "Good Alternative"
            else:
                tag = "Alternative"
            
            top_5_with_prices.append({
                "rank": rank,
                "crop": crop_name,
                "confidence": round(match_percent / 100.0, 4),
                "confidence_percent": match_percent,
                "model_confidence": data["probability"],
                "predicted_price": crop_price,
                "price_method": crop_price_method,
                "price_available": crop_price is not None,
                "is_proxy_price": crop_price_method and crop_price_method.startswith("proxy") if crop_price_method else False,
                "price_shap": price_shap,
                "tag": tag
            })
        
        # Full historical WPI series for the recommended crop (trend chart source)
        price_history = None
        rec_commodity = model_manager.get_price_commodity(crop)
        if rec_commodity:
            try:
                history_points = model_manager.commodities[rec_commodity].get_price_history()
                actual_years = [p["year"] for p in history_points if p.get("source") == "actual"]
                price_history = {
                    "commodity": rec_commodity,
                    "points": history_points,
                    "actual_through": max(actual_years) if actual_years else None,
                }
            except Exception as e:
                logger.warning(f"Could not load price history for {rec_commodity}: {e}")
        
        # Generate XAI explanations
        soil_analysis = CropExplainability.analyze_soil(
            input_data.nitrogen, 
            input_data.phosphorous, 
            input_data.potassium, 
            input_data.ph
        )

        # Agronomic match % (0-100) for the recommended crop — single source of
        # truth shared by the top-level confidence, the crop card, and the XAI ring.
        rec_match_scores = CropExplainability.compute_factor_scores(
            crop, input_data.nitrogen, input_data.phosphorous,
            input_data.potassium, input_data.ph, temperature, rainfall
        )
        rec_match_percent = round(sum(rec_match_scores.values()) / len(rec_match_scores), 1)
        match_confidence = round(rec_match_percent / 100.0, 4)

        explanation = CropExplainability.generate_explanation(
            crop,
            input_data.nitrogen,
            input_data.phosphorous,
            input_data.potassium,
            input_data.ph,
            temperature,
            rainfall,
            match_confidence
        )
        
        growth_advice = CropExplainability.get_growth_guidance(crop)
        
        # Compute XAI breakdown
        xai_breakdown = CropExplainability.compute_xai_breakdown(
            crop, input_data.nitrogen, input_data.phosphorous,
            input_data.potassium, input_data.ph, temperature,
            rainfall, humidity
        )
        
        # CRITICAL DEBUG: Verify crop value right before building response
        logger.info(f"DEBUG - CROP VALUE BEFORE RESPONSE: '{crop}'")
        logger.info(f"DEBUG - CONFIDENCE BEFORE RESPONSE: {confidence}")
        
        # Build response
        response = {
            "recommended_crop": crop,
            "confidence": match_confidence,
            "predicted_price": predicted_price,
            "price_available": price_available,
            "explanation": explanation,
            "soil_analysis": soil_analysis,
            "growth_advice": growth_advice,
            "xai_breakdown": xai_breakdown,
            "details": {
                "input_features": {
                    "nitrogen": input_data.nitrogen,
                    "phosphorous": input_data.phosphorous,
                    "potassium": input_data.potassium,
                    "ph": input_data.ph,
                    "state": input_data.state,
                    "district": input_data.district,
                    "month": input_data.month,
                    "year": input_data.year
                },
                "environmental_data": {
                    "temperature_celsius": round(temperature, 2),
                    "humidity_percent": round(humidity, 2),
                    "rainfall_mm": round(rainfall, 2)
                },
                "top_5_recommendations": top_5_with_prices,
                "top_alternatives": [
                    {
                        "crop": name,
                        "confidence": data["probability"],
                        "price_available": data["has_price_prediction"]
                    }
                    for name, data in top_alternatives
                ],
                "crop_mapping": {
                    "predicted": crop,
                    "mapped_for_price": mapped_crop,
                    "mapping_exists": mapped_crop is not None
                },
                "price_calculation": {
                    "base_price": BASE_PRICES.get(crop.capitalize(), None),
                    "month_used": month_num,
                    "annual_rainfall_used": ANNUAL_RAINFALL[month_num - 1],
                    "price_method": price_method,
                    "is_proxy": price_method and price_method.startswith("proxy") if price_method else False
                } if predicted_price else None,
                "all_crops_have_price_prediction": True,
                "total_supported_crops": 22,
                "direct_price_models": list(model_manager.commodities.keys()),
                "proxy_mappings": {k: v for k, v in CROP_WPI_PROXY.items() if k not in ["cotton", "jute", "maize"]}
                # Note: All 22 predicted crops now have price prediction support!
            },
            "price_history": price_history
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Unified prediction error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# MULTILINGUAL AI CHATBOT
# ============================================================================

import urllib.request
import urllib.error
import os

class MultilingualChatbot:
    """Multilingual AI Chatbot for Indian Farmers"""
    
    # System prompt for agricultural assistant
    SYSTEM_PROMPT = """You are AgriSarathi AI, an expert agricultural assistant for Indian farmers. 

CAPABILITIES:
- Answer farming questions in simple, practical language
- Provide crop recommendations based on soil, climate, and season
- Give step-by-step guidance for planting, irrigation, fertilization, and pest control
- Explain soil health, NPK values, and pH levels
- Offer organic and chemical farming advice
- Share market price insights and selling strategies

RULES:
1. Always respond in the SAME LANGUAGE as the user's question
2. Use simple language that farmers can understand
3. Give practical, actionable advice with specific steps
4. Include quantities (kg, liters, acres) when relevant
5. Be encouraging and supportive
6. If unsure, suggest consulting local agricultural officers

SUPPORTED INDIAN LANGUAGES: Hindi, Tamil, Telugu, Kannada, Malayalam, Marathi, Gujarati, Bengali, Punjabi, Odia, and English.

Remember: Farmers may not be tech-savvy. Keep responses clear, concise, and immediately useful."""

    @staticmethod
    def get_ai_response(message: str, language: str = "en") -> str:
        """Get AI response from open-source model via OpenRouter"""
        import json as json_module  # Local import to ensure availability
        
        # Try OpenRouter API (free tier with open-source models)
        # Using mistralai/Mistral-7B-Instruct (free) or meta-llama/Llama-2-7b-chat
        OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
        
        # Debug logging
        print(f"DEBUG: API Key present: {bool(OPENROUTER_API_KEY)}")
        if OPENROUTER_API_KEY:
            print(f"DEBUG: API Key starts with: {OPENROUTER_API_KEY[:20]}...")
        
        # If no API key, use rule-based fallback with enhanced multilingual support
        if not OPENROUTER_API_KEY:
            print("DEBUG: No API key, using fallback response")
            return MultilingualChatbot._fallback_response(message, language)
        
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8080",
            "X-Title": "AgriSarathi AI"
        }
        
        payload = {
            "model": "mistralai/mistral-7b-instruct:free",  # Free open-source model
            "messages": [
                {"role": "system", "content": MultilingualChatbot.SYSTEM_PROMPT},
                {"role": "user", "content": message}
            ],
            "temperature": 0.7,
            "max_tokens": 500
        }
        
        try:
            req = urllib.request.Request(
                "https://openrouter.ai/api/v1/chat/completions",
                data=json_module.dumps(payload).encode('utf-8'),
                headers=headers,
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json_module.loads(response.read().decode('utf-8'))
                return data["choices"][0]["message"]["content"]
                
        except Exception as e:
            print(f"AI API Error: {e}")
            return MultilingualChatbot._fallback_response(message, language)
    
    @staticmethod
    def _fallback_response(message: str, language: str) -> str:
        """Enhanced fallback with multilingual support"""
        
        # Simple language detection and response
        message_lower = message.lower()
        
        # Multilingual responses
        responses = {
            "en": {
                "greeting": "Hello! I'm AgriSarathi AI. Ask me about crops, soil, or farming! 🌾",
                "crop": "To recommend crops, I need:\n1. Your state and district\n2. Soil NPK values\n3. Current month\nUse the form above! 🎯",
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
            },
            "ta": {
                "greeting": "வணக்கம்! நான் அக்ரிசாரதி AI. பயிர்கள், மண் அல்லது விவசாயம் பற்றி கேளுங்கள்! 🌾",
                "crop": "பயிர்கள் பரிந்துரைக்க:\n1. மாநிலம் மற்றும் மாவட்டம்\n2. மண் NPK மதிப்புகள்\n3. தற்போதைய மாதம்\nமேலே உள்ள படிவத்தை பயன்படுத்தவும்! 🎯",
                "soil": "🧪 மண் குறிப்புகள்:\n• நைட்ரஜன் - யூரியா அல்லது உரம் சேர்க்க\n• பாஸ்பரஸ் - DAP பயன்படுத்தவும்\n• பொட்டாசியம் - பொட்டாஷ் சேர்க்க\n• pH 6.0-7.5 பெரும்பாலான பயிர்களுக்கு ஏற்றது",
                "water": "💧 பாசன குறிப்புகள்:\n• காலை (6-9 மணி) நீர் பாய்ச்சவும்\n• டிரிப் 40% தண்ணீர் சேமிக்கிறது\n• பூக்கும் கட்டத்தில் முக்கியம்\n• அதிக நீர் வேண்டாம்!",
                "pest": "🐛 பூச்சி கட்டுப்பாடு:\n• வேப்ப ஸ்ப்ரே (5ml/L தண்ணீர்)\n• பூண்டு-மிளகாய் ஸ்ப்ரே\n• மஞ்சள் ஒட்டும் வலை\n• சாமந்தி தோழ பயிர்",
                "fertilizer": "🌱 உரங்கள்:\n• யூரியா (46% N) - 40-60 கிலோ/ஏக்கர்\n• DAP (18-46-0) - 25-50 கிலோ/ஏக்கர்\n• வெர்மிகம்போஸ்ட் - 2-4 டன்/ஏக்கர்",
                "default": "நான் உதவ முடியும்:\n🌱 பயிர் தேர்வு\n🧪 மண் ஆலோசனை\n💧 பாசனம்\n🐛 பூச்சி கட்டுப்பாடு\n💰 சந்தை விலை\n\nஎதில் உதவ வேண்டும்?"
            },
            "te": {
                "greeting": "నమస్కారం! నేను అగ్రిసారథి AI. పంటలు, నేల లేదా వ్యవసాయం గురించి అడగండి! 🌾",
                "default": "నేను సహాయం చేయగలను:\n🌱 పంట ఎంపిక\n🧪 నేల సలహా\n💧 సాగు నీరు\n🐛 పీడల నియంత్రణ\n💰 మార్కెట్ ధర\n\nఏ విషయంలో సహాయం కావాలి?"
            },
            "kn": {
                "greeting": "ನಮಸ್ಕಾರ! ನಾನು ಅಗ್ರಿಸಾರಥಿ AI. ಬೆಳೆಗಳು, ಮಣ್ಣು ಅಥವಾ ಕೃಷಿ ಬಗ್ಗೆ ಕೇಳಿ! 🌾",
                "default": "ನಾನು ಸಹಾಯ ಮಾಡಬಲ್ಲೆ:\n🌱 ಬೆಳೆ ಆಯ್ಕೆ\n🧪 ಮಣ್ಣು ಸಲಹೆ\n💧 ನೀರಾವರಿ\n🐛 ಕೀಟ ನಿಯಂತ್ರಣ\n💰 ಮಾರುಕಟ್ಟೆ ಬೆಲೆ\n\nಯಾವ ಬಗ್ಗೆ ಸಹಾಯ ಬೇಕು?"
            },
            "mr": {
                "greeting": "नमस्कार! मी अग्रीसारथी AI आहे. पिके, जमीन किंवा शेतीबद्दल विचारा! 🌾",
                "default": "मी मदत करू शकतो:\n🌱 पीक निवड\n🧪 जमीन सल्ला\n💧 सिंचन\n🐛 कीड नियंत्रण\n💰 बाजार भाव\n\nकशाबद्दल मदत हवी?"
            },
            "gu": {
                "greeting": "નમસ્તે! હું અગ્રિસારથી AI છું. પાક, માટી અથવા ખેતી વિશે પૂછો! 🌾",
                "default": "હું મદદ કરી શકું:\n🌱 પાક પસંદગી\n🧪 માટી સલાહ\n💧 સિંચાઈ\n🐛 જીવાત નિયંત્રણ\n💰 બજાર ભાવ\n\nશામાં મદદ જોઈએ?"
            },
            "bn": {
                "greeting": "নমস্কার! আমি অগ্রিসারথি AI. ফসল, মাটি বা কৃষি সম্পর্কে জিজ্ঞাসা করুন! 🌾",
                "default": "আমি সাহায্য করতে পারি:\n🌱 ফসল নির্বাচন\n🧪 মাটির পরামর্শ\n💧 সেচ\n🐛 কীটপতঙ্গ নিয়ন্ত্রণ\n💰 বাজার দর\n\nকী বিষয়ে সাহায্য চান?"
            },
            "pa": {
                "greeting": "ਸਤ ਸ੍ਰੀ ਅਕਾਲ! ਮੈਂ ਅਗ੍ਰੀਸਾਰਥੀ AI ਹਾਂ। ਫਸਲਾਂ, ਮਿੱਟੀ ਜਾਂ ਖੇਤੀ ਬਾਰੇ ਪੁੱਛੋ! 🌾",
                "default": "ਮੈਂ ਮਦਦ ਕਰ ਸਕਦਾ ਹਾਂ:\n🌱 ਫਸਲ ਚੋਣ\n🧪 ਮਿੱਟੀ ਸਲਾਹ\n💧 ਸਿੰਚਾਈ\n🐛 ਕੀੜਾ ਨਿਯੰਤਰਣ\n💰 ਮੰਡੀ ਭਾਅ\n\nਕਿਸ ਬਾਰੇ ਮਦਦ ਚਾਹੀਦੀ ਹੈ?"
            },
            "ml": {
                "greeting": "നമസ്കാരം! ഞാൻ അഗ്രിസാരഥി AI ആണ്. വിളകൾ, മണ്ണ് അല്ലെങ്കിൽ കൃഷിയെക്കുറിച്ച് ചോദിക്കൂ! 🌾",
                "default": "ഞാൻ സഹായിക്കാൻ കഴിയും:\n🌱 വിള തിരഞ്ഞെടുപ്പ്\n🧪 മണ്ണ് നിർദ്ദേശം\n💧 നനീക്കൽ\n🐛 പests നിയന്ത്രണം\n💰 മാർക്കറ്റ് വില\n\nഎന്തിലാണ് സഹായം വേണ്ടത്?"
            }
        }
        
        # Simple keyword detection
        lang = language if language in responses else "en"
        
        if any(kw in message_lower for kw in ['hi', 'hello', 'hey', 'namaste', 'नमस्ते', 'வணக்கம்', 'నమస్కారం', 'നമസ്കാരം']):
            return responses[lang]["greeting"]
        elif any(kw in message_lower for kw in ['crop', 'which crop', 'what crop', 'which crop', 'फसल', 'பயிர்', 'పంట', 'ਪੀਕ', 'ফসল']):
            return responses[lang]["crop"]
        elif any(kw in message_lower for kw in ['soil', 'nitrogen', 'phosphorus', 'fertilizer', 'मिट्टी', 'மண்', 'నేల', 'ಮಣ್ಣು', 'माती', 'মাটি']):
            return responses[lang]["soil"]
        elif any(kw in message_lower for kw in ['water', 'irrigation', 'पानी', 'தண்ணீர்', 'నీరు', 'ನೀರು', 'পানি']):
            return responses[lang]["water"]
        elif any(kw in message_lower for kw in ['pest', 'insect', 'disease', 'कीट', 'பூச்சி', 'పీడ', 'ಕೀಟ', 'কীট']):
            return responses[lang]["pest"]
        elif any(kw in message_lower for kw in ['fertilizer', 'urea', 'dap', 'urvarak', 'உரம்', 'ఎరువు', 'खत', 'సారం']):
            return responses[lang]["fertilizer"]
        else:
            return responses[lang]["default"]


class ChatbotRequest(BaseModel):
    """Chatbot request model"""
    message: str = Field(..., description="User message")
    language: str = Field(default="en", description="Language code (en, hi, ta, te, kn, mr, gu, bn, pa, ml)")
    history: list = Field(default=[], description="Chat history")


class ChatbotResponse(BaseModel):
    """Chatbot response model"""
    response: str = Field(..., description="AI response")
    language: str = Field(..., description="Language used")
    is_ai_generated: bool = Field(default=False, description="Whether response is from AI API")


@app.post("/chatbot", response_model=ChatbotResponse)
def chatbot_endpoint(request: ChatbotRequest):
    """
    Multilingual AI Chatbot for farmers
    
    Supports: English, Hindi, Tamil, Telugu, Kannada, Malayalam, 
    Marathi, Gujarati, Bengali, Punjabi
    
    To use with OpenRouter AI (free tier):
    Set environment variable: OPENROUTER_API_KEY=your_key_here
    Get free key at: https://openrouter.ai/keys
    """
    try:
        # Get AI response
        ai_response = MultilingualChatbot.get_ai_response(
            request.message, 
            request.language
        )
        
        # Check if it's from AI or fallback
        is_ai = not ai_response.startswith("Hello") and "AI API Error" not in ai_response
        
        return ChatbotResponse(
            response=ai_response,
            language=request.language,
            is_ai_generated=is_ai
        )
        
    except Exception as e:
        return ChatbotResponse(
            response=f"Sorry, I encountered an error. Please try again. (Error: {str(e)})",
            language=request.language,
            is_ai_generated=False
        )


@app.get("/chatbot/languages")
async def get_supported_languages():
    """Get list of supported languages for chatbot"""
    return {
        "languages": [
            {"code": "en", "name": "English", "native": "English"},
            {"code": "hi", "name": "Hindi", "native": "हिंदी"},
            {"code": "ta", "name": "Tamil", "native": "தமிழ்"},
            {"code": "te", "name": "Telugu", "native": "తెలుగు"},
            {"code": "kn", "name": "Kannada", "native": "ಕನ್ನಡ"},
            {"code": "ml", "name": "Malayalam", "native": "മലയാളം"},
            {"code": "mr", "name": "Marathi", "native": "मराठी"},
            {"code": "gu", "name": "Gujarati", "native": "ગુજરાતી"},
            {"code": "bn", "name": "Bengali", "native": "বাংলা"},
            {"code": "pa", "name": "Punjabi", "native": "ਪੰਜਾਬੀ"}
        ],
        "note": "Set OPENROUTER_API_KEY environment variable for AI-powered responses. Without API key, uses intelligent fallback system."
    }


# ============================================================================
# AI CHATBOT MODULE - Import from separate module
# ============================================================================
from app.chatbot import router as chatbot_router
app.include_router(chatbot_router)

# ============================================================================
# FARMER MESSAGE ALERT SYSTEM - Import from separate module
# ============================================================================
from app.alerts import router as alerts_router, start_background_task as start_alert_service
app.include_router(alerts_router)


@app.on_event("startup")
async def _start_alert_service_startup():
    """Start the periodic farmer-alert generator in the background."""
    try:
        start_alert_service()
    except Exception as e:
        logger.warning(f"Alerts: background task failed to start: {e}")

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)
