# SURVIVAL AI

Offline AI survival assistant for Raspberry Pi. Provides survival knowledge, offline messaging, and voice interface.

## Features

| Feature | Status | Description |
|---------|--------|-------------|
| **Speech Input** | ✅ STT ready | Vosk/Whisper for offline voice |
| **Knowledge Base** | ✅ RAG | Local markdown docs with retrieval |
| **Sources** | ✅ | Cites knowledge sources |
| **Offline Maps** | ⚠️ Config | Ready for offline tile cache |
| **Study Guides** | ✅ | Included: first aid, water, fire, shelter, navigation, food |
| **Mesh Messaging** | ✅ LoRa ready | Device-to-device via radio |
| **Display** | ✅ | Terminal, TFT, e-ink |

## Model Selection (from benchmark)

| Model | Size | Avg Response | Quality |
|-------|------|--------------|---------|
| **phi3:mini** | 2GB | 3.68s | 8.56 |
| gemma:2b | 1.5GB | 3.36s | 8.11 |
| tinyllama | 0.6GB | 2.66s | 8.41 |

**Selected: phi3:mini** — Best speed/quality for RPI 8GB

## Quick Start

```bash
# Install Ollama and pull model
ollama pull phi3:mini

# Create venv
python -m venv venv
source venv/bin/activate  # Linux
# or: venv\Scripts\activate.bat  # Windows

# Install deps
pip install -r requirements.txt

# Run web interface
python main.py --mode web
# Or terminal mode
python main.py --mode terminal
```

## Hardware Options

### Required
- Raspberry Pi 4 or 5 (8GB RAM recommended)
- Ollama running locally

### Optional
- **STT**: USB microphone + (Vosk or Whisper)
- **TTS**: espeak or festival
- **Display**: TFT (ILI9341/ST7789) or e-ink (Waveshare)
- **Mesh Radio**: LoRa module (RFM95W) for 50+ mile messaging
- **Offline Maps**: Pre-downloaded map tiles in `data/maps/`

## Knowledge Base

Add `.md` files to `data/knowledge_base/` for custom survival info. Currently included:
- `first_aid.md` — Bleeding, shock, burns, CPR, fractures
- `water.md` — Finding, collecting, purifying water
- `navigation.md` — Sun, stars, compass, natural signs
- `fire.md` — Tinder, friction methods, fire types
- `shelter.md` — Debris hut, snow cave, location selection
- `food.md` — Edible plants, insects, foraging rules

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/status` | GET | System status |
| `/api/chat` | POST | Process message |
| `/api/chat_stream` | POST | Stream response |
| `/api/speech/listen` | POST | Voice input |
| `/api/messages` | GET | Get mesh messages |
| `/api/messages/send` | POST | Send mesh message |
| `/api/display` | POST | Show on screen |

## Architecture

```
survival_ai/
├── agent/
│   └── brain.py      # LLM + RAG logic
├── interface/
│   ├── speech.py     # STT (Vosk/Whisper)
│   ├── display.py    # Terminal/TFT/e-ink
│   └── messaging.py  # LoRa mesh
├── config/
│   └── config.py     # Settings
├── data/
│   └── knowledge_base/  # Survival guides
├── templates/
│   └── index.html    # Web UI
├── web_app.py        # Flask server
└── main.py           # CLI entry
```

## Competitive Features

| Competitor Feature | Our Implementation |
|-------------------|-------------------|
| Provides sources | ✅ RAG + citation |
| World map offline | ⚠️ Ready for tiles |
| Study guides offline | ✅ Included |
| Offline texting (50mi) | ⚠️ LoRa hardware needed |

## Troubleshooting

- **Ollama not connecting**: Check `OLLAMA_BASE_URL` in config
- **No speech**: Install sox/rec, check microphone
- **No mesh messages**: Requires LoRa hardware (RFM95W)
- **Knowledge not found**: Add `.md` files to knowledge_base/