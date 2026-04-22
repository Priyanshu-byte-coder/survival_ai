"""
Speech Input Module - Offline STT using Whisper or Vosk.
Designed for Raspberry Pi with minimal resources.
"""

import logging
import subprocess
import tempfile
import os
from typing import Optional
from config.config import STT_MODEL, STT_TIMEOUT, STT_LANGUAGE

logger = logging.getLogger(__name__)


class SpeechInput:
    """Handles offline speech-to-text input."""

    def __init__(self, model: str = STT_MODEL):
        self.model = model
        self._vosk_model = None

        if self.model == "vosk":
            self._init_vosk()

    def _init_vosk(self):
        """Initialize Vosk model for offline STT."""
        try:
            from vosk import Model
            # Use small model for RPI
            model_path = os.path.join(os.path.dirname(__file__), "..", "data", "vosk-model-small-en-us")
            if os.path.exists(model_path):
                self._vosk_model = Model(model_path)
                logger.info("Vosk model loaded")
            else:
                logger.warning(f"Vosk model not found at {model_path}")
        except ImportError:
            logger.warning("Vosk not installed")
        except Exception as e:
            logger.error(f"Vosk init failed: {e}")

    def listen(self, timeout: int = STT_TIMEOUT) -> Optional[str]:
        """
        Listen for speech input and return transcribed text.
        Uses system microphone via arecord or sox.
        """
        try:
            # Record audio
            audio_file = self._record_audio(timeout)
            if not audio_file:
                return None

            # Transcribe
            text = self._transcribe(audio_file)

            # Cleanup
            try:
                os.remove(audio_file)
            except:
                pass

            return text

        except Exception as e:
            logger.error(f"Speech input failed: {e}")
            return None

    def _record_audio(self, timeout: int) -> Optional[str]:
        """Record audio from microphone."""
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                audio_file = f.name

            # Use arecord (Linux) or sox
            cmd = [
                "arecord", "-f", "cd", "-t", "wav",
                "-d", str(timeout), audio_file
            ]

            # Fallback to sox if arecord not available
            if subprocess.run(["which", "arecord"], capture_output=True).returncode != 0:
                cmd = [
                    "rec", "-q", "-r", "16000", "-c", "1",
                    "-b", "16", "-e", "signed-integer",
                    "-t", "wav", audio_file
                ]

            result = subprocess.run(cmd, capture_output=True, timeout=timeout + 5)
            if result.returncode == 0 and os.path.exists(audio_file):
                return audio_file
            return None

        except subprocess.TimeoutExpired:
            logger.warning("Audio recording timed out")
            return None
        except Exception as e:
            logger.error(f"Audio recording failed: {e}")
            return None

    def _transcribe(self, audio_file: str) -> Optional[str]:
        """Transcribe audio file to text."""
        if self.model == "vosk" and self._vosk_model:
            return self._transcribe_vosk(audio_file)
        else:
            return self._transcribe_whisper(audio_file)

    def _transcribe_vosk(self, audio_file: str) -> Optional[str]:
        """Transcribe using Vosk."""
        try:
            import wave
            import json
            from vosk import Recognizer

            rec = Recognizer(self._vosk_model, 16000)

            with wave.open(audio_file, "rb") as wf:
                if wf.getnchannels() != 1:
                    # Convert to mono
                    # For simplicity, just try to recognize
                    pass

                data = wf.readframes(wf.getnframes())
                rec.AcceptWaveform(data)

            result = json.loads(rec.FinalResult())
            return result.get("text", "").strip()

        except Exception as e:
            logger.error(f"Vosk transcription failed: {e}")
            return None

    def _transcribe_whisper(self, audio_file: str) -> Optional[str]:
        """Transcribe using Whisper via Ollama or command-line."""
        try:
            # Try whisper.cpp first (fastest for offline)
            result = subprocess.run(
                ["whisper", "-m", "ggml-base.bin", "-f", audio_file, "--no-verbose"],
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0 and result.stdout:
                return result.stdout.strip()

            # Fallback: try via Ollama if whisper available there
            # This is handled by the main app calling Ollama's whisper endpoint
            logger.warning("Whisper transcription not available")

        except FileNotFoundError:
            logger.warning("whisper command not found")
        except Exception as e:
            logger.error(f"Whisper transcription failed: {e}")

        return None

    def is_available(self) -> bool:
        """Check if speech input is available."""
        # Check if we have recording capability
        try:
            result = subprocess.run(
                ["which", "arecord"],
                capture_output=True
            )
            if result.returncode == 0:
                return True

            result = subprocess.run(
                ["which", "rec"],
                capture_output=True
            )
            return result.returncode == 0
        except:
            return False