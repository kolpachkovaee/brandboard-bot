"""
Конфигурация бота
Заполните своими API ключами
"""

import os

# ── Обязательные ──────────────────────────────────────────────────────────────

# Telegram Bot Token — получить у @BotFather
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN_HERE")

# Google Gemini API Key — получить БЕСПЛАТНО на https://aistudio.google.com/app/apikey
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY_HERE")

# Модель (gemini-1.5-flash — бесплатная и быстрая)
GEMINI_MODEL = "gemini-1.5-flash"
