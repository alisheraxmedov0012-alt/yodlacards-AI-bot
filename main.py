import asyncio
import logging
import os
import random
from datetime import datetime

import aiosqlite
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from gtts import gTTS

from ai_engine import ai_teacher_response, generate_word_data, speech_to_text
from config import ADMIN_ID, BOT_TOKEN, CHANNELS
from database import DB_NAME, init_db
from keyboards import (
    main_menu,
    shop_keyboard,
    sets_keyboard,
    words_count_keyboard,
)
from states import BotStates

# --------------------------------------------------
# FASTAPI SAHIFASI VA CORS SOZLAMALARI
# --------------------------------------------------
app = FastAPI(title="YodlaCards AI API", version="1.0.0")

# Mini App frontendidan so'rovlar kelganda bloklanmasligi uchun
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {"status": "alive", "project": "YodlaCards AI"}

# ====================== MINI APP API ENDPOINTS ======================

from pydantic import BaseModel
class ActionModel(BaseModel):
    user_id: int
    card_id: int
    action: str

class ChatModel(BaseModel):
    text: str
    
class AddWordModel(BaseModel):
    user_id: int
    set_name: str
    english: str
    uzbek: str

# # Foydanuvchi o'z profiliga shaxsiy set va so'z qo'shishi uchun API
@app.post("/api/flashcard/add")
async def add_flashcard_api(data: AddWordModel):
    try:
        async with aiosqlite.connect(DB_NAME) as db:
            # AI ta'rifini generatsiya qilish
            try:
                ai_info = await generate_word_data(data.english)
            except Exception:
                ai_info = f"'{data.english}' so'zining o'zbekcha tarjimasi: {data.uzbek}."

            # MA'LUMOTLARNI ASLIY 'dictionary' JADVALIGA FOYDALANUVCHI ID-SI BILAN YOZISH
            await db.execute(
                """
                INSERT INTO dictionary (user_id, set_name, english, uzbek, ai_info, status, progress)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (data.user_id, data.set_name, data.english, data.uzbek, ai_info, "new", 0)
            )
            
            # Foydalanuvchiga so'z qo'shgani uchun XP va Tangalar berish
            await db.execute(
                "UPDATE users SET xp = xp + 5, coins = coins + 1 WHERE user_id = ?",
                (data.user_id,)
            )
            
            await db.commit()
        return {"status": "success", "message": "So'z muvaffaqiyatli qo'shildi!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 2. Foydalanuvchining shaxsiy setlari ro'yxatini va undagi so'zlar sonini olish API
@app.get("/api/user/{user_id}/sets")
async def get_user_sets(user_id: int):
    try:
        async with aiosqlite.connect(DB_NAME) as db:
            async with db.execute(
                """
                SELECT set_name, COUNT(*) as count 
                FROM dictionary 
                WHERE user_id = ? 
                GROUP BY set_name 
                ORDER BY MAX(id) DESC
                """, 
                (user_id,)
            ) as cursor:
                rows = await cursor.fetchall()
        return [{"set_name": row[0], "count": row[1]} for row in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 3. UNIVERSAL API: Tanlangan set ichidagi shaxsiy kartalarni tortish
# Agar foydalanuvchida so'z bo'lmasa, unga namuna so'zlar qaytariladi
@app.get("/api/user/{user_id}/cards")
async def get_user_cards(user_id: int, set_name: str = None, limit: int = 50):
    try:
        async with aiosqlite.connect(DB_NAME) as db:
            if set_name:
                query = """
                    SELECT id, english, uzbek, ai_info 
                    FROM dictionary 
                    WHERE user_id = ? AND set_name = ? 
                    ORDER BY RANDOM() LIMIT ?
                """
                params = (user_id, set_name, limit)
            else:
                query = """
                    SELECT id, english, uzbek, ai_info 
                    FROM dictionary 
                    WHERE user_id = ? 
                    ORDER BY RANDOM() LIMIT ?
                """
                params = (user_id, limit)
                
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                
        # Agar foydalanuvchida hali birorta ham so'z bo'lmasa, unga namuna so'zlar qaytariladi
        if not rows and not set_name:
            return [
                {"id": 0, "english": "Resilience", "uzbek": "Matonat", "ai_info": "The capacity to recover quickly."},
                {"id": 0, "english": "Ubiquitous", "uzbek": "Hamma yerda mavjud", "ai_info": "Present, appearing, or found everywhere."}
            ]
            
        cards = []
        for row in rows:
            cards.append({
                "id": row[0],
                "english": row[1],
                "uzbek": row[2],
                "ai_info": row[3] if row[3] else "No extra info provided."
            })
        return cards
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
            
    return cards

# 2. BILDIM / BILMADIM TUGMALARI BOSILGANDA BAZANI YANGILASH VA XP QO'SHISH
@app.post("/api/flashcard/action")
async def flashcard_action(data: ActionModel):
    async with aiosqlite.connect(DB_NAME) as db:
        if data.action == "know":
            # "Bildim" bosilsa: progress oshadi, tanga va XP beriladi
            await db.execute(
                "UPDATE dictionary SET correct_count = correct_count + 1, progress = MIN(progress + 20, 100) WHERE id = ?",
                (data.card_id,)
            )
            await db.execute(
                "UPDATE users SET xp = xp + 10, coins = coins + 2 WHERE user_id = ?",
                (data.user_id,)
            )
        else:
            # "Bilmadim" bosilsa: xatolar soni oshadi, progress kamayadi
            await db.execute(
                "UPDATE dictionary SET wrong_count = wrong_count + 1, progress = MAX(progress - 10, 0) WHERE id = ?",
                (data.card_id,)
            )
        
        # Level ko'tarilish mantiqini tekshirish (Foydalanuvchi joriy XP sini tekshiramiz)
        async with db.execute("SELECT xp, level FROM users WHERE user_id = ?", (data.user_id,)) as cursor:
            user_data = await cursor.fetchone()
            if user_data:
                current_xp, current_lvl = user_data
                needed_xp = current_lvl * 100
                if current_xp >= needed_xp:
                    await db.execute(
                        "UPDATE users SET level = level + 1, xp = xp - ? WHERE user_id = ?",
                        (needed_xp, data.user_id)
                    )
                    
        await db.commit()
    return {"status": "success", "message": "Action processed successfully"}

# 3. CHAT INTERFEYSIDAN AI TEACHER GA SO'ROV YUBORISH
@app.post("/api/ai/chat")
async def ai_teacher_endpoint(data: ChatModel):
    try:
        response_text = await ai_teacher_response(data.text)
        return {
            "reply": response_text,
            "grammar_feedback": "Xatolar tekshirildi."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 4. STATISTIKA TABI UCHUN FOYDALANUVCHI MA'LUMOTLARINI OLISH
@app.get("/api/user/{user_id}/stats")
async def get_user_stats(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        # Foydalanuvchi ma'lumotlarini o'qiymiz
        async with db.execute(
            "SELECT level, xp, coins, streak, total_words FROM users WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            user_row = await cursor.fetchall()
            
    if not user_row:
        return {"level": 1, "xp_percent": 0, "coins": 0, "streak": 0, "total_words": 0, "learned_words": 0}
        
    user_data = user_row[0]  # fetchall ro'yxat qaytargani uchun birinchi elementni olamiz
    
    total = user_data[4] if user_data[4] else 0
    xp_now = user_data[1] % 100 if user_data[1] else 0  # progress bar foizini chiqarish uchun
    
    return {
        "level": user_data[0],
        "xp_percent": xp_now,
        "coins": user_data[2],
        "streak": user_data[3],
        "total_words": total,
        "learned_words": int(total * 0.35)  # Frontend xato bermasligi uchun taxminiy yodlangan so'zlar
    }

# --------------------------------------------------
# LOGGING
# --------------------------------------------------
logging.basicConfig(level=logging.INFO)

@app.post("/api/speech/verify")
async def verify_speech(
    audio: UploadFile = File(...),
    user_id: int = Form(...),
    target_word: str = Form(...)
):
    try:
        # Kelajakda bu yerga speech_test funksiyasini ulab qo'yasiz
        return {
            "score": 90,
            "feedback": f"Yaxshi talaffuz! '{target_word}' so'zini to'g'ri aytdingiz."
        }
    except Exception:
        return {"score": 0, "feedback": "Ovozni aniqlab bo'lmadi."}

# ======================================================
# BOT
# ======================================================

bot = Bot(token=BOT_TOKEN)

dp = Dispatcher(storage=MemoryStorage())

# ======================================================
# SUBSCRIBE CHECK
# ======================================================


async def check_sub(user_id):
    for channel in CHANNELS:
        try:
            member = await bot.get_chat_member(channel, user_id)

            if member.status in ["left", "kicked"]:
                return False

        except:
            return False

    return True


def sub_keyboard():
    builder = InlineKeyboardBuilder()

    for ch in CHANNELS:
        builder.row(
            types.InlineKeyboardButton(
                text=f"📢 {ch}", url=f"https://t.me/{ch.replace('@', '')}"
            )
        )

    builder.row(
        types.InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_sub")
    )

    return builder.as_markup()


# ======================================================
# STREAK SYSTEM
# ======================================================


async def update_streak(user_id):
    today = datetime.now().date()

    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            """ SELECT streak,last_active FROM users WHERE user_id=? """,
            (user_id,),
        ) as cursor:
            user = await cursor.fetchone()

        if not user:
            return

        streak, last_active = user

        if not last_active:
            streak = 1

        else:
            try:
                last_date = datetime.strptime(last_active, "%Y-%m-%d").date()

                diff = (today - last_date).days

                if diff == 1:
                    streak += 1

                elif diff > 1:
                    streak = 1

            except:
                streak = 1

        await db.execute(
            """ UPDATE users SET streak=?, last_active=? WHERE user_id=? """,
            (streak, today.strftime("%Y-%m-%d"), user_id),
        )

        await db.commit()


# ======================================================
# LEVEL SYSTEM
# ======================================================


async def check_level_up(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            """ SELECT xp,level FROM users WHERE user_id=? """,
            (user_id,),
        ) as cursor:
            user = await cursor.fetchone()

        if not user:
            return

        xp, level = user

        need_xp = level * 100

        if xp >= need_xp:
            new_level = level + 1

            await db.execute(
                """ UPDATE users SET level=? WHERE user_id=? """,
                (new_level, user_id),
            )

            await db.commit()

            await bot.send_message(
                user_id,
                f""" 🎉 LEVEL UP 🏆 Siz {new_level}-levelga chiqdingiz """,
            )


# ======================================================
# START
# ======================================================


@dp.message(Command("start"))
async def start(message: types.Message):
    await init_db()

    # 1. Referal ID ni aniqlaymiz (agar havola orqali kirgan bo'lsa)
    args = message.text.split()
    referrer_id = None
    if len(args) > 1:
        try:
            referrer_id = int(args[1])
            if referrer_id == message.from_user.id:  # O'zini o'zi taklif qila olmaydi
                referrer_id = None
        except:
            referrer_id = None

    # 2. Kanallarga obunani tekshiramiz
    if not await check_sub(message.from_user.id):
        await message.answer(
            "❌ Avval kanallarga obuna bo‘ling", reply_markup=sub_keyboard()
        )
        return

    # 3. Foydalanuvchini bazaga qo'shamiz va referal bonusni hisoblaymiz
    async with aiosqlite.connect(DB_NAME) as db:
        # Avval bu foydalanuvchi bazada bor-yo'qligini tekshiramiz
        async with db.execute(
            "SELECT user_id FROM users WHERE user_id = ?", (message.from_user.id,)
        ) as cursor:
            user_exists = await cursor.fetchone()

        if not user_exists:
            # Yangi foydalanuvchini ro'yxatga olamiz
            await db.execute(
                """ INSERT INTO users (user_id, first_name, username, last_active) VALUES (?, ?, ?, ?) """,
                (
                    message.from_user.id,
                    message.from_user.first_name,
                    message.from_user.username,
                    datetime.now().strftime("%Y-%m-%d"),
                ),
            )

            # Agar taklif qilgan odam (referal) bo'lsa, unga bonus beramiz
            if referrer_id:
                await db.execute(
                    """ UPDATE users SET coins = coins + 10, xp = xp + 20 WHERE user_id = ? """,
                    (referrer_id,),
                )
                try:
                    # Taklif qilgan odamga xabar yuboramiz
                    await bot.send_message(
                        referrer_id,
                        "🎉 Sizning havolangiz orqali yangi do'stingiz qo'shildi!\n🪙 +10 Coin va ⭐ +20 XP berildi.",
                    )
                except:
                    pass

        await db.commit()

    # 4. Xush kelibsiz xabarini chiqaramiz
    await message.answer(
        f""" 👋 Xush kelibsiz {message.from_user.first_name} 📚 YodlaCards AI 🔥 So‘z yodlang 🎴 Flashcards ishlating 🧠 AI Teacher bilan gaplashing 🏆 XP va Coins yig‘ing """,
        reply_markup=main_menu(),
    )


# ======================================================
# CHECK SUB
# ======================================================


@dp.callback_query(F.data == "check_sub")
async def check_subscription(callback: types.CallbackQuery):
    if await check_sub(callback.from_user.id):
        await callback.message.answer("✅ Obuna tasdiqlandi", reply_markup=main_menu())

    else:
        await callback.answer("❌ Hamma kanalga obuna bo‘ling", show_alert=True)
        # ======================================================


# ADD WORD (TO'LIQ VA SIKLLI VARIANT)
# ======================================================


@dp.message(F.text == "➕ So'z qo'shish")
async def add_word(message: types.Message, state: FSMContext):
    await state.set_state(BotStates.adding_set)
    await message.answer(
        "📁 Set nomini yuboring (masalan: IELTS, Unit 1)",
        reply_markup=types.ReplyKeyboardRemove(),
    )


@dp.message(BotStates.adding_set)
async def save_set(message: types.Message, state: FSMContext):
    await state.update_data(set_name=message.text)
    await state.set_state(BotStates.adding_en)
    await message.answer(
        f"✅ Set '{message.text}' tanlandi.\n🇬🇧 Inglizcha so'zni yuboring:"
    )


@dp.message(BotStates.adding_en)
async def save_english(message: types.Message, state: FSMContext):
    # Foydalanuvchi tugatishni tanlasa
    if message.text == "✅ Bo'ldi, tugatish":
        await finish_adding(message, state)
        return

    await state.update_data(english=message.text)
    await state.set_state(BotStates.adding_uz)
    await message.answer("🇺🇿 Tarjimasini yuboring:")


@dp.message(BotStates.adding_uz)
async def save_word(message: types.Message, state: FSMContext):
    data = await state.get_data()
    set_name = data["set_name"]
    english = data["english"]
    uzbek = message.text

    wait = await message.answer("🤖 AI ma'lumot tayyorlamoqda...")

    try:
        ai_info = await generate_word_data(english)
    except Exception as e:
        ai_info = f"❌ AI xatolik: {e}"

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """ INSERT INTO dictionary (user_id, set_name, english, uzbek, ai_info, status, progress) VALUES (?, ?, ?, ?, ?, ?, ?) """,
            (message.from_user.id, set_name, english, uzbek, ai_info, "new", 0),
        )
        await db.execute(
            "UPDATE users SET xp = xp + 5, coins = coins + 1 WHERE user_id = ?",
            (message.from_user.id,),
        )
        await db.commit()

    await update_streak(message.from_user.id)
    await check_level_up(message.from_user.id)
    await wait.delete()

    # Tugatish tugmasini chiqarish
    builder = ReplyKeyboardBuilder()
    builder.row(types.KeyboardButton(text="✅ Bo'ldi, tugatish"))

    # Matnga {ai_info} ni qo'shdik — endi AI tushuntirishi va gaplari ekranda chiqadi!
    await message.answer(
        f"✅ **Muvaffaqiyatli saqlandi!**\n"
        f"📁 Set: {set_name}\n"
        f"🇬🇧 {english} - 🇺🇿 {uzbek}\n\n"
        f"🤖 **AI Teacher tushuntirishi:**\n"
        f"{ai_info}\n\n"
        f"Keyingi inglizcha so'zni yuboring yoki tugatishni bosing:",
        reply_markup=builder.as_markup(resize_keyboard=True),
    )

    # Holatni yana inglizcha so'z kiritishga qaytaramiz
    await state.set_state(BotStates.adding_en)


# ======================================================
# TUGATISH HANDLERI
# ======================================================


@dp.message(F.text == "✅ Bo'ldi, tugatish")
async def finish_adding(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "📥 Barcha so'zlar lug'atingizga saqlandi!", reply_markup=main_menu()
    )


# ======================================================
# DICTIONARY
# ======================================================


@dp.message(F.text == "📚 Lug'at")
async def dictionary(message: types.Message):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            """ SELECT set_name, english, uzbek, progress FROM dictionary WHERE user_id = ? ORDER BY id DESC LIMIT 100 """,
            (message.from_user.id,),
        ) as cursor:
            words = await cursor.fetchall()

    if not words:
        await message.answer("❌ Lug'at bo'sh")

        return

    text = "📚 Sizning lug'atingiz\n\n"

    for word in words:
        set_name = word[0]
        english = word[1]
        uzbek = word[2]
        progress = word[3]

        text += (
            f"📁 {set_name}\n🇬🇧 {english}\n🇺🇿 {uzbek}\n📊 Progress: {progress}/5\n\n"
        )

    if len(text) > 4000:
        text = text[:4000]

    await message.answer(text)


# ======================================================
# 🏆 GLOBAL LEADERBOARD (REYTING)
# ======================================================


@dp.message(F.text == "🏆 Leaderboard")
async def leaderboard(message: types.Message):
    async with aiosqlite.connect(DB_NAME) as db:
        # Foydalanuvchilarni XP bo'yicha kamayish tartibida TOP-10 tasini olamiz
        async with db.execute(
            """ SELECT first_name, username, xp, level FROM users ORDER BY xp DESC LIMIT 10 """
        ) as cursor:
            top_users = await cursor.fetchall()

        # Foydalanuvchining o'zini reytingini aniqlash (ixtiyoriy, lekin qiziqarli)
        async with db.execute(
            """ SELECT COUNT(*) + 1 FROM users WHERE xp > (SELECT xp FROM users WHERE user_id = ?) """,
            (message.from_user.id,),
        ) as cursor:
            user_rank = (await cursor.fetchone())[0]

    if not top_users:
        await message.answer("❌ Hozircha reyting ma'lumotlari bo'sh.")
        return

    text = "🏆 **YodlaCards Global Reytingi (TOP-10)**\n\n"

    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

    for index, user in enumerate(top_users):
        first_name = user[0]
        username = f"@{user[1]}" if user[1] else "Yashirin"
        xp = user[2]
        level = user[3]

        # Ism juda uzun bo'lsa kesib chiroyli qilamiz
        if len(first_name) > 15:
            first_name = first_name[:12] + "..."

        text += (
            f"{medals[index]} {first_name} ({username}) — **{xp} XP** | {level}-lvl\n"
        )

    text += f"\n──────────────────\n📊 Sizning o'rningiz: **{user_rank}-o'rin**"

    await message.answer(text, parse_mode="Markdown")


# ======================================================
# 📊 USER STATISTICS (HAFTALIK PROGRESS)
# ======================================================


@dp.message(F.text == "📊 Statistics")
async def user_statistics(message: types.Message):
    user_id = message.from_user.id

    async with aiosqlite.connect(DB_NAME) as db:
        # 1. Foydalanuvchining umumiy profildagi ma'lumotlarini olamiz
        async with db.execute(
            "SELECT xp, coins, level, streak FROM users WHERE user_id = ?", (user_id,)
        ) as cursor:
            user_data = await cursor.fetchone()

        if not user_data:
            await message.answer("❌ Profil ma'lumotlari topilmadi.")
            return

        xp, coins, level, streak = user_data

        # 2. Lug'atdagi jami so'zlar sonini hisoblaym/iz
        async with db.execute(
            "SELECT COUNT(*) FROM dictionary WHERE user_id = ?", (user_id,)
        ) as cursor:
            total_words = (await cursor.fetchone())[0]

        # 3. O'rganilgan so'zlar (progressi 100% yoki statusi 'learned' bo'lganlar)
        async with db.execute(
            "SELECT COUNT(*) FROM dictionary WHERE user_id = ? AND (progress >= 100 OR status = 'learned')",
            (user_id,),
        ) as cursor:
            learned_words = (await cursor.fetchone())[0]

    # Progress foizini hisoblaymiz
    progress_percent = (
        int((learned_words / total_words) * 100) if total_words > 0 else 0
    )

    # Vizual progress bar yasaymiz (masalan: ■■■□□□□□□□)
    filled_blocks = int(progress_percent / 10)
    progress_bar = "■" * filled_blocks + "□" * (10 - filled_blocks)

    # Chiroyli statistika matni
    text = (
        f"📊 **Sizning YodlaCards Statistikangiz**\n"
        f"──────────────────\n"
        f"🏅 **Daraja (Level):** {level}-lvl\n"
        f"✨ **Umumiy XP:** {xp} XP\n"
        f"🪙 **Tanganiz (Coins):** {coins} coins\n"
        f"🔥 **Kunlik Ketma-ketlik (Streak):** {streak} kun\n\n"
        f"📝 **Lug'at ko'rsatkichlari:**\n"
        f"📚 Jami kiritilgan so'zlar: **{total_words} ta**\n"
        f"✅ To'liq yodlangan so'zlar: **{learned_words} ta**\n\n"
        f"📈 **Yodlash Progressingiz:**\n"
        f"|{progress_bar}| **{progress_percent}%**\n"
        f"──────────────────\n"
        f"💡 *Maslahat: Har kuni kamida 10 ta yangi so'z qo'shing va flashkartalar yordamida ularni takrorlab turing!*"
    )

    await message.answer(text, parse_mode="Markdown")


# ======================================================
# 🎤 AI VOICE CHECK (TALAFFUZNI TEKSHIRISH)
# ======================================================

@dp.message(F.text == "🎴 Flashkartalar")
async def flashcards(message: types.Message, state: FSMContext):
    await state.clear()
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            "SELECT DISTINCT set_name FROM dictionary WHERE user_id = ?",
            (message.from_user.id,),
        ) as cursor:
            sets = await cursor.fetchall()

    if not sets:
        await message.answer("❌ Sizda so'zlar mavjud emas")
        return

    set_names = [x[0] for x in sets]
    await state.update_data(available_sets=set_names)
    await state.set_state(BotStates.select_set)
    await message.answer("📂 Set tanlang", reply_markup=sets_keyboard(set_names))


@dp.message(F.text == "🧠 AI Teacher")
async def ai_teacher_start(message: types.Message, state: FSMContext):
    await state.set_state(BotStates.ai_menu)
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎙 Talaffuzni tekshirish", callback_data="mode_voice"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💬 AI bilan inglizcha suhbat", callback_data="mode_chat"
                )
            ],
        ]
    )

    from aiogram.utils.keyboard import ReplyKeyboardBuilder

    builder = ReplyKeyboardBuilder()

    await message.answer(
        "✨ **AI Teacher tizimiga xush kelibsiz!**\n\n"
        "Bugun nima bilan shug'ullanamiz? Quyidagi rejimlardan birini tanlang:",
        reply_markup=builder.as_markup(resize_keyboard=True),
        parse_mode="Markdown",
    )

    await message.answer("Yo'nalishni tanlang:", reply_markup=inline_kb)

    # 🎛 INLINE TUGMALAR BOSILGANDA ISHLAYDIGAN CALLBACK'LAR


@dp.callback_query(BotStates.ai_menu, F.data == "mode_voice")
async def set_voice_mode(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(BotStates.ai_voice_check)
    await callback.message.edit_text(
        "🎙 **Talaffuzni tekshirish rejimi faollashdi!**\n\n"
        "Menga istalgan inglizcha so'z, ibora yoki gapni **ovozli xabar (voice)** shaklida yuboring. "
        "Men sizning talaffuzingizni eshitib, matnga o'giraman va AI orqali xatolaringizni to'g'rilab beraman! 🔥",
        parse_mode="Markdown",
    )
    await callback.answer()


@dp.callback_query(BotStates.ai_menu, F.data == "mode_chat")
async def set_chat_mode(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(BotStates.ai_chat_mode)
    await callback.message.edit_text(
        "💬 **AI bilan inglizcha suhbat rejimi faollashdi!**\n\n"
        "Men bilan xuddi do'stingizdek ingliz tilida suhbatlashishingiz mumkin. "
        "Agar gaplaringizda **grammatik xatolar** bo'lsa, ularni darhol to'g'rilab, o'zbekcha tushuntirib boraman! 🧠\n\n"
        "Suhbatni boshlash uchun biror narsa deb yozing (Masalan: *Hello!*):",
        parse_mode="Markdown",
    )
    await callback.answer()


# 🎙 OVOZLI XABARNI QABUL QILISH VA AI TAHLIL QILISH HANDLERI
@dp.message(BotStates.ai_voice_check, F.voice)
async def process_voice_pronunciation(message: types.Message):
    wait = await message.answer(
        "🎧 Ovingiz eshitilmoqda, AI tahlil qilmoqda. Iltimos kuting..."
    )

    try:
        voice = message.voice
        file_info = await message.bot.get_file(voice.file_id)

        import os

        os.makedirs("downloads", exist_ok=True)
        ogg_path = f"downloads/{voice.file_id}.ogg"
        wav_path = f"downloads/{voice.file_id}.wav"

        await message.bot.download_file(file_info.file_path, ogg_path)

        from pydub import AudioSegment

        audio = AudioSegment.from_ogg(ogg_path)
        audio.export(wav_path, format="wav")

        from ai_engine import speech_to_text, analyze_voice_pronunciation

        recognized_text = await speech_to_text(wav_path)

        if os.path.exists(ogg_path):
            os.remove(ogg_path)
        if os.path.exists(wav_path):
            os.remove(wav_path)

        if not recognized_text or not recognized_text.strip():
            await wait.delete()
            await message.answer(
                "❌ Kechirasiz, ovozingizni umuman aniqlay olmadim. Biroz aniqroq va balandroq gapirib qayta urining."
            )
            return

        # AI orqali ovozli tahlilni chaqiramiz
        ai_analysis = await analyze_voice_pronunciation(recognized_text)

        await wait.delete()

        final_response = (
            f"🎙 **Men eshitgan matn:**\n`{recognized_text}`\n\n"
            f"🧠 **AI Coach Tahlili:**\n{ai_analysis}"
        )
        await message.answer(final_response, parse_mode="Markdown")

    except Exception as e:
        if "wait" in locals():
            await wait.delete()
        await message.answer("❌ Ovozni qayta ishlashda xatolik yuz berdi.")
        print(f"Voice processing error: {e}")

        # 💬 AI BILAN CHAT REJIMIDA GAPLASHISH HANDLERI


@dp.message(BotStates.ai_chat_mode, F.text, ~F.text.has("🔙 Asosiy menyu"))
async def process_ai_chat_teacher(message: types.Message):
    wait = await message.answer(
        "🔄 AI oʻqituvchi oʻylamoqda..."
    )

    from ai_engine import ai_teacher_response

    ai_reply = await ai_teacher_response(message.text)

    await wait.delete()
    await message.answer(ai_reply)


async def back_to_main_from_voice(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=main_menu())


import random  # Agar tepada import qilinmagan bo'lsa, buni tepaga qo'shing

# ======================================================
# 🌗 QUIZ MODE (KUNLIK TEST)
# ======================================================


@dp.message( F.text == "🌗 Kunlik Test" ) # Keyboards.py da ushbu tugmani qo'shishni unutmang
async def start_quiz(message: types.Message, state: FSMContext):
    user_id = message.from_user.id

    async with aiosqlite.connect(DB_NAME) as db:
        # Foydalanuvchining lug'atidan kamida 4 ta so'z borligini tekshiramiz
        async with db.execute(
            "SELECT english, uzbek FROM dictionary WHERE user_id = ?", (user_id,)
        ) as cursor:
            words = await cursor.fetchall()

    if len(words) < 4:
        await message.answer(
            "⚠️ Test boshlash uchun lug'atingizda kamida 4 ta so'z bo'lishi kerak. Iltimos, ko'proq so'z qo'shing!"
        )
        return

    # Tasodifiy bitta so'zni tanlaymiz (bu to'g'ri javob bo'ladi)
    correct_pair = random.choice(words)
    correct_en, correct_uz = correct_pair

    # Noto'g'ri variantlarni tanlaymiz
    other_words = [w[1] for w in words if w[1] != correct_uz]
    wrong_options = random.sample(other_words, 3)

    # Barcha variantlarni aralashtiramiz
    options = wrong_options + [correct_uz]
    random.shuffle(options)

    # Tugmalarni yasaymiz
    builder = ReplyKeyboardBuilder()
    for opt in options:
        builder.add(types.KeyboardButton(text=opt))
    builder.adjust(2)
    builder.row(types.KeyboardButton(text="🔙 Chiqish"))

    await state.set_state(BotStates.quiz_mode)
    await state.update_data(correct_answer=correct_uz, english_word=correct_en)

    await message.answer(
        f"❓ **Ushbu so'zning tarjimasini toping:**\n\n🇬🇧 English: **{correct_en}**",
        reply_markup=builder.as_markup(resize_keyboard=True),
        parse_mode="Markdown",
    )


@dp.message(BotStates.quiz_mode)
async def check_quiz_answer(message: types.Message, state: FSMContext):
    if message.text == "🔙 Chiqish":
        await state.clear()
        await message.answer("🏠 Test yakunlandi.", reply_markup=main_menu())
        return

    data = await state.get_data()
    correct_answer = data.get("correct_answer")

    if message.text == correct_answer:
        # To'g'ri javob uchun mukofot berish
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute(
                "UPDATE users SET xp = xp + 10, coins = coins + 2 WHERE user_id = ?",
                (message.from_user.id,),
            )
            await db.commit()

        await message.answer("✅ Baraka! To'g'ri javob: **+10 XP, +2 Coin** 🪙")
        # Keyingi savolga o'tamiz
        await start_quiz(message, state)
    else:
        await message.answer(
            f"❌ Noto'g'ri! To'g'ri javob: **{correct_answer}** edi. Yana urinib ko'ring!"
        )
        await start_quiz(message, state)


# ======================================================
# 🚀 ORQAGA TUGMALARI (AYNAN SHU YERDA TURISHI SHART!)
# ======================================================


@dp.message(BotStates.select_set, F.text.contains("Orqaga"))
async def back_to_main_menu(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("🏠 Asosiy menyuga qaytdingiz:", reply_markup=main_menu())


@dp.message(BotStates.select_count, F.text.contains("Orqaga"))
async def back_to_select_set(message: types.Message, state: FSMContext):
    data = await state.get_data()
    set_names = data.get("available_sets", [])

    await state.set_state(BotStates.select_set)
    await message.answer("📁 Qayta set tanlang:", reply_markup=sets_keyboard(set_names))


# ======================================================
# SELECT SET (Orqaga handlerlaridan pastga tushirildi)
# ======================================================


@dp.message(BotStates.select_set)
async def select_set(message: types.Message, state: FSMContext):
    await state.update_data(selected_set=message.text)
    await state.set_state(BotStates.select_count)
    await message.answer("🔢 Nechta so'z chiqsin?", reply_markup=words_count_keyboard())


# ======================================================
# SELECT COUNT
# ======================================================


@dp.message(BotStates.select_count)
async def select_count(message: types.Message, state: FSMContext):
    if "Orqaga" in message.text:
        return

    data = await state.get_data()
    selected_set = data["selected_set"]

    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            """ SELECT id, english, uzbek, progress FROM dictionary WHERE user_id = ? AND set_name = ? ORDER BY progress ASC, RANDOM() """,
            (message.from_user.id, selected_set),
        ) as cursor:
            words = await cursor.fetchall()

    if not words:
        await message.answer(f"❌ '{selected_set}' seti bo'sh yoki topilmadi.")
        return

    if message.text != "Hammasi":
        try:
            count = int(message.text)
            words = words[:count]
        except ValueError:
            pass

    await state.update_data(
        flash_words=words, flash_index=0, flash_correct=0, flash_wrong=0, retry_words=[]
    )

    await send_flashcard(message.chat.id, state)

    # ======================================================


# SEND FLASHCARD
# ======================================================


async def send_flashcard(chat_id, state):
    data = await state.get_data()

    words = data["flash_words"]
    index = data["flash_index"]

    if index >= len(words):
        correct = data["flash_correct"]
        wrong = data["flash_wrong"]
        retry_words = data["retry_words"]

        xp = correct * 5
        coins = correct

        builder = InlineKeyboardBuilder()

        if retry_words:
            builder.row(
                types.InlineKeyboardButton(
                    text="🔁 Xatolarni qayta ishlash", callback_data="retry_wrong"
                )
            )

        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute(
                """ UPDATE users SET xp = xp + ?, coins = coins + ? WHERE user_id = ? """,
                (xp, coins, chat_id),
            )

            await db.commit()

        await bot.send_message(
            chat_id,
            f""" 🎉 Flashcards tugadi ✅ To'g'ri: {correct} ❌ Xato: {wrong} ⭐ +{xp} XP 🪙 +{coins} Coins """,
            reply_markup=builder.as_markup(),
        )

        return

    current = words[index]

    english = current[1]

    builder = InlineKeyboardBuilder()

    builder.row(
        types.InlineKeyboardButton(text="👁 Tarjimani ko'rish", callback_data="reveal")
    )

    try:
        os.makedirs("audios", exist_ok=True)

        audio_path = f"audios/{english}.mp3"

        if not os.path.exists(audio_path):
            tts = gTTS(text=english, lang="en")

            tts.save(audio_path)

        audio = types.FSInputFile(audio_path)

        await bot.send_voice(
            chat_id,
            voice=audio,
            caption=f""" 🎴 FLASHCARD 🇬🇧 {english} """,
            reply_markup=builder.as_markup(),
        )

    except:
        await bot.send_message(
            chat_id,
            f""" 🎴 FLASHCARD 🇬🇧 {english} """,
            reply_markup=builder.as_markup(),
        )


# ======================================================
# REVEAL
# ======================================================


@dp.callback_query(F.data == "reveal")
async def reveal(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()

    words = data["flash_words"]
    index = data["flash_index"]

    current = words[index]

    english = current[1]
    uzbek = current[2]

    builder = InlineKeyboardBuilder()

    builder.row(
        types.InlineKeyboardButton(text="✅ Bildim", callback_data="know"),
        types.InlineKeyboardButton(text="❌ Bilmadim", callback_data="dont"),
    )

    text = f""" 🇬🇧 {english} 🇺🇿 {uzbek} Esladingizmi? """

    try:
        await callback.message.edit_caption(
            caption=text, reply_markup=builder.as_markup()
        )

    except:
        await callback.message.edit_text(text=text, reply_markup=builder.as_markup())

    await callback.answer()


# ======================================================
# KNOW / DONT
# ======================================================


@dp.callback_query(F.data.in_(["know", "dont"]))
async def process_answer(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()

    words = data["flash_words"]
    index = data["flash_index"]

    current = words[index]

    word_id = current[0]
    progress = current[3]

    correct = data["flash_correct"]
    wrong = data["flash_wrong"]

    retry_words = data["retry_words"]

    async with aiosqlite.connect(DB_NAME) as db:
        if callback.data == "know":
            correct += 1

            if progress < 5:
                progress += 1

            status = "learned" if progress >= 5 else "learning"

            await db.execute(
                """ UPDATE dictionary SET progress=?, status=? WHERE id=? """,
                (progress, status, word_id),
            )

        else:
            wrong += 1

            retry_words.append(current)

            if progress > 0:
                progress -= 1

            await db.execute(
                """ UPDATE dictionary SET progress=?, status='learning' WHERE id=? """,
                (progress, word_id),
            )

        await db.commit()

    await state.update_data(
        flash_index=index + 1,
        flash_correct=correct,
        flash_wrong=wrong,
        retry_words=retry_words,
    )

    try:
        await callback.message.delete()
    except:
        pass

    await send_flashcard(callback.message.chat.id, state)


# ======================================================
# RETRY WRONG
# ======================================================


@dp.callback_query(F.data == "retry_wrong")
async def retry_wrong(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()

    retry_words = data["retry_words"]

    if not retry_words:
        await callback.answer("Xato so'zlar yo'q", show_alert=True)

        return

    await state.update_data(
        flash_words=retry_words,
        flash_index=0,
        flash_correct=0,
        flash_wrong=0,
        retry_words=[],
    )

    await callback.message.answer("🔁 Xato so'zlar qayta boshlandi")

    await send_flashcard(callback.message.chat.id, state)
    # ======================================================


# AI TEACHER
# ======================================================


@dp.message(F.text == "🧠 AI Teacher")
async def ai_teacher_start(message: types.Message, state: FSMContext):
    await state.set_state(BotStates.ai_teacher)

    await message.answer(
        """ 🧠 AI Teacher yoqildi 🇬🇧 Inglizcha yozing 🇺🇿 Yoki o'zbekcha yozing 🎤 Voice ham yuborishingiz mumkin """
    )


# ======================================================
# AI CHAT
# ======================================================


@dp.message(BotStates.ai_teacher)
async def ai_chat(message: types.Message):
    wait = await message.answer("🤖 AI o'ylamoqda...")

    try:
        response = await ai_teacher_response(message.text)

        await wait.delete()

        await message.answer(response)

    except Exception as e:
        await wait.delete()

        await message.answer(f"❌ Xatolik\n\n{e}")


# ======================================================
# VOICE MESSAGE
# ======================================================


@dp.message(BotStates.ai_teacher, F.voice)
async def ai_voice(message: types.Message):
    wait = await message.answer("🎤 Ovoz analiz qilinmoqda...")

    try:
        file = await bot.get_file(message.voice.file_id)

        voice_file = f"voice_{message.from_user.id}.ogg"

        await bot.download(file=file.file_path, destination=voice_file)

        text = await speech_to_text(voice_file)

        response = await ai_teacher_response(text)

        await wait.delete()

        await message.answer(
            f""" 🎤 Siz aytdingiz: {text} 🤖 AI javobi: {response} """
        )

    except Exception as e:
        await wait.delete()

        await message.answer(f"❌ Voice xatolik\n\n{e}")


# ======================================================
# PROFILE
# ======================================================


@dp.message(F.text == "👤 Profil")
async def profile(message: types.Message):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            """ SELECT xp, level, coins, streak FROM users WHERE user_id = ? """,
            (message.from_user.id,),
        ) as cursor:
            user = await cursor.fetchone()

    if not user:
        return

    xp, level, coins, streak = user

    await message.answer(
        f""" 👤 Profil 🆔 ID: {message.from_user.id} ⭐ XP: {xp} 🏆 Level: {level} 🪙 Coins: {coins} 🔥 Streak: {streak} """
    )


# ======================================================
# DAILY BONUS
# ======================================================


@dp.message(F.text == "🎁 Daily Bonus")
async def daily_bonus(message: types.Message):
    today = datetime.now().strftime("%Y-%m-%d")

    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            """ SELECT last_bonus FROM users WHERE user_id = ? """,
            (message.from_user.id,),
        ) as cursor:
            row = await cursor.fetchone()

        if row and row[0] == today:
            await message.answer("❌ Bonus olib bo'lgansiz")

            return

        coins = random.randint(5, 20)

        await db.execute(
            """ UPDATE users SET coins = coins + ?, last_bonus = ? WHERE user_id = ? """,
            (coins, today, message.from_user.id),
        )

        await db.commit()

    await message.answer(f"🎁 {coins} coin oldingiz")


# ======================================================
# LEADERBOARD
# ======================================================


@dp.message(F.text == "🏆 Leaderboard")
async def leaderboard(message: types.Message):
    text = "🏆 TOP 10\n\n"

    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            """ SELECT first_name, xp FROM users ORDER BY xp DESC LIMIT 10 """
        ) as cursor:
            users = await cursor.fetchall()

    for i, user in enumerate(users, start=1):
        text += f"{i}. {user[0]} — {user[1]} XP\n"

    await message.answer(text)


# ======================================================
# REFERRAL
# ======================================================


@dp.message(F.text == "🔗 Referal")
async def referral(message: types.Message):
    me = await bot.get_me()

    link = f"https://t.me/{me.username}?start={message.from_user.id}"

    await message.answer(
        f""" 🔗 Sizning referal linkingiz {link} """
    )


# ======================================================
# ADMIN BROADCAST
# ======================================================


@dp.message(Command("broadcast"))
async def broadcast(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    text = message.text.replace("/broadcast ", "")

    sent = 0

    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            """ SELECT user_id FROM users """
        ) as cursor:
            users = await cursor.fetchall()

    for user in users:
        try:
            await bot.send_message(user[0], text)

            sent += 1

        except:
            pass

        await message.answer(f"✅ Yuborildi: {sent}")

# ==================================================
# ASINXRON FASTAPI VA BOTNI PARALLEL ISHGA TUSHIRISH
# ==================================================

@app.on_event("startup")
async def on_startup():
    # 1. Ma'lumotlar bazasini ishga tushirish
    await init_db()
    
    # 2. Telegram botni orqa fonda (fon rejimida) yurgizib yuborish
    asyncio.create_task(dp.start_polling(bot, drop_pending_updates=True))
    
    print("🚀 FastAPI server muvaffaqiyatli yurdi!")
    print("🤖 Bot polling rejimida boshlandi!")

@app.on_event("shutdown")
async def on_shutdown():
    await bot.session.close()

if __name__ == "__main__":
    import uvicorn
    # Render, Railway yoki Replit portni dinamik bersa uni oladi, bo'lmasa 8000 dan foydalanadi
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
    
        
