#!/bin/bash
# Setup script for Survival AI on Raspberry Pi

set -e

echo "=== SURVIVAL AI SETUP ==="

# Create venv
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install Ollama (if not present)
if ! command -v ollama &> /dev/null; then
    echo "Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
fi

# Pull survival model
echo "Pulling survival model (phi3:mini)..."
ollama pull phi3:mini

# Install system deps
echo "Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y sox libsox-fmt-mp3

# Optional: Install Vosk for offline STT
# echo "Installing Vosk..."
# mkdir -p data/vosk-model-small-en-us
# wget -q -O data/vosk-model-small-en-us/model.zip https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
# unzip -o data/vosk-model-small-en-us/model.zip -d data/vosk-model-small-en-us/
# rm data/vosk-model-small-en-us/model.zip

echo "=== SETUP COMPLETE ==="
echo "Run: source venv/bin/activate && python main.py --mode terminal"
echo "Or: source venv/bin/activate && python main.py --mode web"