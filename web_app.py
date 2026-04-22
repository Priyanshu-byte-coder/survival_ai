"""
Flask web application for Survival AI.
Provides browser interface for offline survival assistant.
"""

import logging
import sys
import base64
import json
from flask import Flask, render_template, request, jsonify, Response
from flask_cors import CORS
from agent.brain import SurvivalBrain
from interface.speech import SpeechInput
from interface.display import Display
from interface.messaging import MeshMessaging
from config.config import (
    OLLAMA_BASE_URL, LLM_MODEL, STT_MODEL,
    DISPLAY_MODE, MESSAGE_STORE_DIR
)

app = Flask(__name__)
CORS(app)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger(__name__)

brain = None
speech = None
display = None
messaging = None


def initialize_systems():
    """Initialize all AI systems."""
    global brain, speech, display, messaging

    logger.info("Initializing Survival AI...")
    brain = SurvivalBrain()
    speech = SpeechInput()
    display = Display()
    messaging = MeshMessaging()

    status = brain.check_systems()
    status["speech"] = speech.is_available()
    status["messaging"] = messaging.is_available()
    status["display"] = DISPLAY_MODE

    logger.info(f"System status: {status}")
    return status


@app.route('/')
def index():
    """Serve main interface."""
    return render_template('index.html')


@app.route('/api/status', methods=['GET'])
def get_status():
    """Check system status."""
    global brain, speech, messaging

    if brain is None:
        status = initialize_systems()
    else:
        status = brain.check_systems()
        status["speech"] = speech.is_available()
        status["messaging"] = messaging.is_available()
        status["display"] = DISPLAY_MODE

    return jsonify({
        "status": status,
        "ollama_url": OLLAMA_BASE_URL,
        "model": LLM_MODEL,
        "stt_model": STT_MODEL
    })


@app.route('/api/chat', methods=['POST'])
def chat():
    """Process chat message."""
    global brain, display

    if brain is None:
        initialize_systems()

    data = request.json
    user_message = data.get('message', '').strip()

    if not user_message:
        return jsonify({"error": "Empty message"}), 400

    try:
        # Get sources
        sources = brain.get_sources(user_message)

        # Generate response
        response = brain.process(user_message)

        # Display output
        source_text = sources[0]["source"] if sources else None
        display.show(response, source_text)

        return jsonify({
            "response": response,
            "sources": sources
        })
    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/api/chat_stream', methods=['POST'])
def chat_stream():
    """Process chat message with streaming response."""
    global brain, display

    if brain is None:
        initialize_systems()

    data = request.json
    user_message = data.get('message', '').strip()

    if not user_message:
        return jsonify({"error": "Empty message"}), 400

    def generate():
        try:
            # Get sources
            sources = brain.get_sources(user_message)
            if sources:
                yield f"data: {json.dumps({'type': 'sources', 'sources': sources})}\n\n"

            # Stream response
            response_generator = brain.process(user_message, stream=True)

            for token in response_generator:
                yield f"data: {json.dumps({'type': 'token', 'token': token})}\n\n"

            # Get full response for display
            # (in streaming mode, we can't get full text easily - simplified here)

            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    return Response(generate(), mimetype='text/event-stream')


@app.route('/api/speech/listen', methods=['POST'])
def speech_listen():
    """Listen for speech input."""
    global speech

    if speech is None:
        initialize_systems()

    if not speech.is_available():
        return jsonify({"error": "Speech input not available"}), 400

    try:
        text = speech.listen(timeout=10)
        if text:
            return jsonify({"text": text, "success": True})
        else:
            return jsonify({"error": "No speech detected", "success": False})
    except Exception as e:
        logger.error(f"Speech error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/messages', methods=['GET'])
def get_messages():
    """Get recent messages."""
    global messaging

    if messaging is None:
        initialize_systems()

    return jsonify({"messages": messaging.get_messages()})


@app.route('/api/messages/send', methods=['POST'])
def send_message():
    """Send a mesh message."""
    global messaging

    if messaging is None:
        initialize_systems()

    data = request.json
    message = data.get('message', '').strip()
    target = data.get('target')  # None for broadcast

    if not message:
        return jsonify({"error": "Empty message"}), 400

    try:
        success = messaging.send(message, target)
        return jsonify({"success": success})
    except Exception as e:
        logger.error(f"Send error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/messages/receive', methods=['POST'])
def receive_message():
    """Listen for incoming mesh message."""
    global messaging

    if messaging is None:
        initialize_systems()

    timeout = request.json.get('timeout', 10)

    try:
        msg = messaging.receive(timeout=timeout)
        if msg:
            return jsonify({"message": msg, "success": True})
        return jsonify({"message": None, "success": False})
    except Exception as e:
        logger.error(f"Receive error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/display', methods=['POST'])
def display_output():
    """Display text on screen."""
    global display

    if display is None:
        initialize_systems()

    data = request.json
    text = data.get('text', '')

    display.show(text)
    return jsonify({"success": True})


@app.route('/api/display/clear', methods=['POST'])
def display_clear():
    """Clear display."""
    global display

    if display is None:
        initialize_systems()

    display.clear()
    return jsonify({"success": True})


if __name__ == '__main__':
    logger.info("Starting Survival AI Web Application...")
    logger.info("Access at: http://localhost:5000")
    logger.info(f"Or from another device: http://<raspberry-pi-ip>:5000")

    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)