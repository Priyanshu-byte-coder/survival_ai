"""
Central configuration for the Survival AI system.
Offline-first AI for core survival scenarios.
"""

import os
from pathlib import Path

# --- Project Paths ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
KNOWLEDGE_BASE_DIR = DATA_DIR / "knowledge_base"
MAPS_DIR = DATA_DIR / "maps"
STUDY_GUIDES_DIR = DATA_DIR / "study_guides"
MESSAGE_STORE_DIR = DATA_DIR / "messages"

# --- LLM Configuration ---
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
LLM_MODEL = os.getenv("LLM_MODEL", "phi3:mini")  # Best speed/quality for RPI 8GB
LLM_TEMPERATURE = 0.2  # Focused, factual responses
LLM_MAX_TOKENS = 150  # More detailed for survival info
LLM_NUM_CTX = 2048  # Larger context for knowledge retrieval
LLM_NUM_THREAD = 4
LLM_TIMEOUT = 300

# --- STT Configuration (Speech-to-Text) ---
STT_MODEL = os.getenv("STT_MODEL", "whisper")  # or "vosk"
STT_LANGUAGE = "en"
STT_TIMEOUT = 30

# --- TTS Configuration (Text-to-Speech) ---
TTS_ENABLED = os.getenv("TTS_ENABLED", "true").lower() == "true"
TTS_MODEL = os.getenv("TTS_MODEL", "espeak")  # Fast, offline TTS

# --- RAG / Knowledge Base Configuration ---
KNOWLEDGE_TOP_K = 3  # Number of relevant documents to retrieve
RAG_ENABLED = True

# --- Offline Map Configuration ---
MAP_PROVIDER = "offline"  # Pre-downloaded tiles
MAP_CACHE_DIR = MAPS_DIR / "tiles"
MAP_BOUNDS = {}  # Will be populated with downloaded region

# --- Offline Messaging Configuration ---
MESH_NETWORK_ENABLED = True
MESSAGE_MAX_DISTANCE_KM = 80  # ~50 miles LoRa range
MESSAGE_STORE_DAYS = 7

# --- Display Configuration ---
DISPLAY_MODE = os.getenv("DISPLAY_MODE", "terminal")  # "terminal" or "eink" or "tft"
TERMINAL_WIDTH = 80

# --- System Prompt ---
SYSTEM_PROMPT = """You are SURVIVOR, an offline AI survival assistant.
Provide factual, actionable survival guidance. Always cite sources when possible.
Keep responses concise but informative. Prioritize safety and practical solutions.
Never hallucinate - if unsure, say so and suggest consulting local resources."""

# --- Ensure data directories exist ---
for d in [DATA_DIR, KNOWLEDGE_BASE_DIR, MAPS_DIR, STUDY_GUIDES_DIR, MESSAGE_STORE_DIR]:
    d.mkdir(parents=True, exist_ok=True)