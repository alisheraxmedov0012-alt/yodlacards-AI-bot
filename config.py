import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot sozlamalari
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "8434095954"))

CHANNELS = [
    "@YodlaCards",
    "@Samarqandkvartiralarelonlari"
]

# AI Provayder sozlamalari (OpenRouter)
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_URL = "https://openrouter.ai/api/v1/chat/completions"

# Yangi ishlaydigan bepul AI modeli
AI_MODEL = "openai/gpt-oss-120b:free"

# Qo'shimcha narxlar va sozlamalar
AI_LIMIT_PRICE = 30
IELTS_PACK_PRICE = 100
XP_BOOST_PRICE = 50
