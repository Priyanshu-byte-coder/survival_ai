"""
Display Module - Multiple output options for survival scenarios.
Supports terminal, TFT display, and e-ink displays.
"""

import logging
import sys
from typing import Optional
from config.config import DISPLAY_MODE, TERMINAL_WIDTH

logger = logging.getLogger(__name__)


class Display:
    """Handles output display to various screens."""

    def __init__(self, mode: str = DISPLAY_MODE):
        self.mode = mode
        self._display = None

        if mode == "tft":
            self._init_tft()
        elif mode == "eink":
            self._init_eink()

    def _init_tft(self):
        """Initialize TFT display (GPIO)."""
        try:
            # Common TFT displays: ILI9341, ST7789
            import digitalio
            import board
            import adafruit_rgb_display.ili9341 as ili9341
            import adafruit_rgb_display.st7789 as st7789

            # Setup SPI
            cs_pin = digitalio.DigitalInOut(board.CE0)
            dc_pin = digitalio.DigitalInOut(board.D22)
            rst_pin = digitalio.DigitalInOut(board.D27)
            spi = board.SPI()

            # Try ST7789 (common 240x240)
            try:
                self._display = st7789.ST7789(
                    spi, cs_pin, dc_pin, rst_pin,
                    width=240, height=240, rotation=180
                )
                logger.info("ST7789 TFT initialized")
                return
            except:
                pass

            # Try ILI9341 (common 320x240)
            try:
                self._display = ili9341.ILI9341(
                    spi, cs_pin, dc_pin, rst_pin,
                    width=320, height=240
                )
                logger.info("ILI9341 TFT initialized")
            except Exception as e:
                logger.warning(f"TFT init failed: {e}")
                self._display = None

        except ImportError:
            logger.warning("TFT display libraries not installed")
        except Exception as e:
            logger.error(f"TFT initialization failed: {e}")

    def _init_eink(self):
        """Initialize e-ink display."""
        try:
            # Common e-ink: Waveshare e-Paper
            import board
            import displayio
            import adafruit_epd.epd2in9 as epd

            self._display = epd.Adafruit_EPD()
            logger.info("E-ink display initialized")
        except ImportError:
            logger.warning("E-ink display libraries not installed")
        except Exception as e:
            logger.error(f"E-ink initialization failed: {e}")

    def show(self, text: str, source: Optional[str] = None):
        """Display text on configured output."""
        if self.mode == "terminal":
            self._show_terminal(text, source)
        elif self.mode == "tft" and self._display:
            self._show_tft(text)
        elif self.mode == "eink" and self._display:
            self._show_eink(text)

    def _show_terminal(self, text: str, source: Optional[str] = None):
        """Display to terminal with formatting."""
        print("\n" + "=" * TERMINAL_WIDTH)
        print(text)
        if source:
            print(f"\n[SOURCE: {source}]")
        print("=" * TERMINAL_WIDTH + "\n")

    def _show_tft(self, text: str):
        """Display on TFT screen."""
        if not self._display:
            return

        try:
            self._display.fill(0x000000)
            self._display.text(text, 10, 10, 0xFFFFFF)
            self._display.display()
        except Exception as e:
            logger.error(f"TFT display failed: {e}")

    def _show_eink(self, text: str):
        """Display on e-ink screen."""
        if not self._display:
            return

        try:
            self._display.fill(0xFFFFFF)
            self._display.text(text, 10, 10, 0x000000)
            self._display.display()
        except Exception as e:
            logger.error(f"E-ink display failed: {e}")

    def clear(self):
        """Clear the display."""
        if self.mode == "terminal":
            print("\033[2J\033[H")  # ANSI clear
        elif self.mode == "tft" and self._display:
            self._display.fill(0x000000)
            self._display.display()
        elif self.mode == "eink" and self._display:
            self._display.fill(0xFFFFFF)
            self._display.display()