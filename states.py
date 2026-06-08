from aiogram.fsm.state import (
    StatesGroup,
    State
)


class BotStates(StatesGroup):

    # =========================
    # WORD ADDING
    # =========================

    adding_set = State()

    adding_en = State()

    adding_uz = State()

    # =========================
    # FLASHCARDS
    # =========================

    select_set = State()

    select_count = State()

    flashcards = State()

    retry_flashcards = State()

    quiz_mode = State()

    # =========================
    # AI TEACHER
    # =========================

    ai_teacher = State()

    ai_teacher_voice = State()
    
    ai_menu = State()          # AI tanlov menyusi uchun holat
    ai_voice_check = State()   # Talaffuz tekshirish holati
    ai_chat_mode = State()     # AI bilan chat suhbat holati


    # =========================
    # SHOP
    # =========================

    shop = State()

    # =========================
    # PREMIUM
    # =========================

    premium = State()

    # =========================
    # SETTINGS
    # =========================

    settings = State()

    # =========================
    # ADMIN
    # =========================

    broadcast = State()
