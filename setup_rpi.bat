@echo off
REM Setup script for Survival AI on Windows

echo === SURVIVAL AI SETUP ===

REM Create venv
python -m venv venv
call venv\Scripts\activate.bat

REM Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

REM Pull model via Ollama
echo Pulling survival model...
ollama pull phi3:mini

echo === SETUP COMPLETE ===
echo Run: call venv\Scripts\activate.bat ^&^& python main.py --mode web
pause