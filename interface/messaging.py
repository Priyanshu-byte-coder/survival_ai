"""
Mesh Messaging Module - Offline device-to-device communication.
Supports LoRa radio modules for long-range (50+ mile) messaging without cell service.
"""

import logging
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from config.config import MESSAGE_STORE_DIR, MESSAGE_MAX_DISTANCE_KM, MESSAGE_STORE_DAYS

logger = logging.getLogger(__name__)


class MeshMessaging:
    """Handles offline mesh networking via LoRa for survival communication."""

    def __init__(self, device_id: str = "survival-01"):
        self.device_id = device_id
        self.store_dir = MESSAGE_STORE_DIR
        self.store_dir.mkdir(parents=True, exist_ok=True)
        self._radio = None

        self._init_radio()
        self._cleanup_old_messages()

    def _init_radio(self):
        """Initialize LoRa radio module."""
        try:
            # Common LoRa modules: RFM95W, SX1276
            import board
            import digitalio
            import adafruit_rfm9x

            # Pin configuration (adjust for your setup)
            CS = digitalio.DigitalInOut(board.CE1)
            RESET = digitalio.DigitalInOut(board.D25)

            spi = board.SPI()

            # Initialize RFM95W at 915MHz (US)
            self._radio = adafruit_rfm9x.RFM9x(spi, CS, RESET, 915.0)
            self._radio.tx_power = 23  # Max power

            logger.info("LoRa radio initialized")
        except ImportError:
            logger.warning("LoRa radio libraries not installed")
        except Exception as e:
            logger.error(f"Radio init failed: {e}")

    def send(self, message: str, target_id: Optional[str] = None) -> bool:
        """
        Send a message via LoRa.
        If target_id is None, broadcast to all.
        """
        if not self._radio:
            logger.warning("Radio not available")
            return False

        try:
            payload = {
                "from": self.device_id,
                "to": target_id or "broadcast",
                "message": message,
                "timestamp": datetime.now().isoformat()
            }

            data = json.dumps(payload).encode('utf-8')
            self._radio.send(data)

            # Store locally
            self._store_message(payload)

            logger.info(f"Sent message to {target_id or 'broadcast'}")
            return True

        except Exception as e:
            logger.error(f"Send failed: {e}")
            return False

    def receive(self, timeout: float = 30.0) -> Optional[dict]:
        """
        Listen for incoming messages.
        Returns message dict or None.
        """
        if not self._radio:
            return None

        try:
            # Check for packet
            packet = self._radio.receive(timeout=timeout)
            if packet is None:
                return None

            # Parse message
            try:
                payload = json.loads(packet.decode('utf-8'))
                self._store_message(payload)
                return payload
            except json.JSONDecodeError:
                logger.warning("Received invalid packet")
                return None

        except Exception as e:
            logger.error(f"Receive failed: {e}")
            return None

    def _store_message(self, message: dict):
        """Store message to local database."""
        try:
            msg_id = f"{message['timestamp']}_{message['from']}"
            msg_file = self.store_dir / f"{msg_id}.json"
            msg_file.write_text(json.dumps(message, indent=2), encoding='utf-8')
        except Exception as e:
            logger.error(f"Failed to store message: {e}")

    def get_messages(self, limit: int = 50) -> list[dict]:
        """Get recent messages from local storage."""
        messages = []

        try:
            for msg_file in sorted(self.store_dir.glob("*.json"), reverse=True)[:limit]:
                try:
                    msg = json.loads(msg_file.read_text(encoding='utf-8'))
                    messages.append(msg)
                except:
                    continue
        except Exception as e:
            logger.error(f"Failed to read messages: {e}")

        return messages

    def get_messages_from(self, sender_id: str, limit: int = 20) -> list[dict]:
        """Get messages from a specific sender."""
        all_msgs = self.get_messages(limit=100)
        return [m for m in all_msgs if m.get('from') == sender_id]

    def _cleanup_old_messages(self):
        """Remove messages older than MESSAGE_STORE_DAYS."""
        try:
            cutoff = datetime.now() - timedelta(days=MESSAGE_STORE_DAYS)

            for msg_file in self.store_dir.glob("*.json"):
                try:
                    msg_time = datetime.fromisoformat(msg_file.stem.split('_')[0])
                    if msg_time < cutoff:
                        msg_file.unlink()
                except:
                    continue
        except Exception as e:
            logger.warning(f"Cleanup failed: {e}")

    def is_available(self) -> bool:
        """Check if mesh messaging is available."""
        return self._radio is not None

    def get_device_id(self) -> str:
        """Get this device's ID."""
        return self.device_id

    def set_device_id(self, device_id: str):
        """Set this device's ID."""
        self.device_id = device_id