from aiogram import types
from aiogram.utils.keyboard import (
    ReplyKeyboardBuilder,
    InlineKeyboardBuilder
)
# 1. Telegram Mini App ochilishi uchun WebAppInfo klassini import qildik
from aiogram.types import WebAppInfo

# --------------------------------------------------
# MAIN MENU
# --------------------------------------------------

def main_menu():
    kb = ReplyKeyboardBuilder()
    
    # 2. Mini App-ni ochadigan professional katta tugmani eng tepaga joylashtirdik
    # (Kelajakda buni o'zingizning real Vercel/Netlify havolangizga almashtirasiz)
    mini_app_url = "https://yodlacards-app.netlify.app"
    
    kb.row(
        types.KeyboardButton(
            text="YodlaCards AI Ilovasi 🚀",
            web_app=WebAppInfo(url=mini_app_url)
        )
    )
    
    # Quyida sizning barcha mavjud tugmalaringiz o'z holaticha qoldi
    kb.row(
        types.KeyboardButton(text="➕ So'z qo'shish"),
        types.KeyboardButton(text="📚 Lug'at")
    )
    
    kb.row(
        types.KeyboardButton(text="🎴 Flashkartalar"),
        types.KeyboardButton(text="🧠 Kunlik Test")
    )
    
    kb.row(
        types.KeyboardButton(text="🧠 AI Teacher"),
        types.KeyboardButton(text="📊 Statistics")
    )
    
    kb.row(
        types.KeyboardButton(text="👤 Profil"),
        types.KeyboardButton(text="🏆 Leaderboard")
    )
    
    kb.row(
        types.KeyboardButton(text="🔗 Referral"),
        types.KeyboardButton(text="🎁 Daily Bonus")
    )
    
    kb.row(
        types.KeyboardButton(text="🏪 Do'kon"),
        types.KeyboardButton(text="⚙️ Sozlamalar")
    )
    
    return kb.as_markup(resize_keyboard=True)

# --------------------------------------------------
# SETS KEYBOARD
# --------------------------------------------------

def sets_keyboard(sets):
    kb = ReplyKeyboardBuilder()
    
    for set_name in sets:
        kb.row(
            types.KeyboardButton(
                text=set_name
            )
        )
        
    kb.row(
        types.KeyboardButton(
            text="🔙 Orqaga"
        )
    )
    
    return kb.as_markup(
        resize_keyboard=True
    )

# --------------------------------------------------
# WORDS COUNT
# --------------------------------------------------

def words_count_keyboard():
    kb = ReplyKeyboardBuilder()
    
    kb.row(
        types.KeyboardButton(text="10"),
        types.KeyboardButton(text="20")
    )
    
    kb.row(
        types.KeyboardButton(text="50"),
        types.KeyboardButton(text="Hammasi")
    )
    
    kb.row(
        types.KeyboardButton(
            text="🔙 Orqaga"
        )
    )
    
    return kb.as_markup(
        resize_keyboard=True
    )

# --------------------------------------------------
# RETRY KEYBOARD
# --------------------------------------------------

def retry_keyboard():
    kb = InlineKeyboardBuilder()
    
    kb.row(
        types.InlineKeyboardButton(
            text="🔄 Xatolarni qayta takrorlash",
            callback_data="retry_wrong"
        )
    )
    
    kb.row(
        types.InlineKeyboardButton(
            text="✅ Tugatish",
            callback_data="finish_retry"
        )
    )
    
    return kb.as_markup()

# --------------------------------------------------
# SHOP KEYBOARD
# --------------------------------------------------

def shop_keyboard():
    kb = InlineKeyboardBuilder()
    
    kb.row(
        types.InlineKeyboardButton(
            text="🧠 AI Limit +50",
            callback_data="buy_ai_limit"
        )
    )
    
    kb.row(
        types.InlineKeyboardButton(
            text="📚 IELTS Premium Set",
            callback_data="buy_ielts_pack"
        )
    )
    
    kb.row(
        types.InlineKeyboardButton(
            text="🚀 XP Booster",
            callback_data="buy_xp_boost"
        )
    )
    
    return kb.as_markup()

# --------------------------------------------------
# FLASHCARD BUTTONS
# --------------------------------------------------

def flashcard_keyboard():
    kb = InlineKeyboardBuilder()
    
    kb.row(
        types.InlineKeyboardButton(
            text="👁️ Tarjimani ko'rish",
            callback_data="reveal"
        )
    )
    
    return kb.as_markup()

# --------------------------------------------------
# KNOW / DONT KNOW
# --------------------------------------------------

def remember_keyboard():
    kb = InlineKeyboardBuilder()
    
    kb.row(
        types.InlineKeyboardButton(
            text="✅ Bildim",
            callback_data="know"
        ),
        types.InlineKeyboardButton(
            text="❌ Bilmadim",
            callback_data="dont"
        )
    )
    
    return kb.as_markup()
    
