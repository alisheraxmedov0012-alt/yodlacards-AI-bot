from aiogram import types
from aiogram.utils.keyboard import (
    ReplyKeyboardBuilder,
    InlineKeyboardBuilder
)


# ======================================================
# MAIN MENU
# ======================================================

def main_menu():
    kb = ReplyKeyboardBuilder()

    kb.row(
        types.KeyboardButton(text="âž• So'z qo'shish"),
        types.KeyboardButton(text="ðŸ“š Lug'at")
    )

    kb.row(
        types.KeyboardButton(text="ðŸŽ´ Flashkartalar"),
        types.KeyboardButton(text="ðŸŒ— Kunlik Test")  # <-- Mana shu yangi qo'shildi
    )

    kb.row(
        types.KeyboardButton(text="ðŸ§  AI Teacher"),
        types.KeyboardButton(text="ðŸ“Š Statistics")
    )

    kb.row(
        types.KeyboardButton(text="ðŸ‘¤ Profil"),
        types.KeyboardButton(text="ðŸ† Leaderboard")
    )

    kb.row(
        types.KeyboardButton(text="ðŸ”— Referal"),
        types.KeyboardButton(text="ðŸŽ Daily Bonus")
    )

    kb.row(
        types.KeyboardButton(text="ðŸª Do'kon"),
        types.KeyboardButton(text="âš™ï¸ Sozlamalar")
    )

    return kb.as_markup(resize_keyboard=True)  

# ======================================================
# SETS KEYBOARD
# ======================================================

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
            text="ðŸ”™ Orqaga"
        )
    )

    return kb.as_markup(
        resize_keyboard=True
    )


# ======================================================
# WORDS COUNT
# ======================================================

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
            text="ðŸ”™ Orqaga"
        )
    )

    return kb.as_markup(
        resize_keyboard=True
    )


# ======================================================
# RETRY KEYBOARD
# ======================================================

def retry_keyboard():

    kb = InlineKeyboardBuilder()

    kb.row(
        types.InlineKeyboardButton(
            text="ðŸ” Xatolarni qayta takrorlash",
            callback_data="retry_wrong"
        )
    )

    kb.row(
        types.InlineKeyboardButton(
            text="âœ… Tugatish",
            callback_data="finish_retry"
        )
    )

    return kb.as_markup()


# ======================================================
# SHOP KEYBOARD
# ======================================================

def shop_keyboard():

    kb = InlineKeyboardBuilder()

    kb.row(
        types.InlineKeyboardButton(
            text="ðŸ§  AI Limit +50",
            callback_data="buy_ai_limit"
        )
    )

    kb.row(
        types.InlineKeyboardButton(
            text="ðŸ“š IELTS Premium Set",
            callback_data="buy_ielts_pack"
        )
    )

    kb.row(
        types.InlineKeyboardButton(
            text="ðŸš€ XP Booster",
            callback_data="buy_xp_boost"
        )
    )

    return kb.as_markup()


# ======================================================
# FLASHCARD BUTTONS
# ======================================================

def flashcard_keyboard():

    kb = InlineKeyboardBuilder()

    kb.row(
        types.InlineKeyboardButton(
            text="ðŸ‘ Tarjimani ko'rish",
            callback_data="reveal"
        )
    )

    return kb.as_markup()


# ======================================================
# KNOW / DONT KNOW
# ======================================================

def remember_keyboard():

    kb = InlineKeyboardBuilder()

    kb.row(
        types.InlineKeyboardButton(
            text="âœ… Bildim",
            callback_data="know"
        ),

        types.InlineKeyboardButton(
            text="âŒ Bilmadim",
            callback_data="dont"
        )
    )

    return kb.as_markup()
