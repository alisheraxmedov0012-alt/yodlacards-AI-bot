import aiosqlite

DB_NAME = "english_ai_bot.db"


async def init_db():

    async with aiosqlite.connect(DB_NAME) as db:

        await db.execute(""" CREATE TABLE IF NOT EXISTS users ( id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER UNIQUE, first_name TEXT, username TEXT, referred_by INTEGER DEFAULT 0, xp INTEGER DEFAULT 0, level INTEGER DEFAULT 1, coins INTEGER DEFAULT 0, streak INTEGER DEFAULT 0, score INTEGER DEFAULT 0, ai_limit INTEGER DEFAULT 20, premium INTEGER DEFAULT 0, total_words INTEGER DEFAULT 0, learned_words INTEGER DEFAULT 0, last_bonus TEXT DEFAULT '', last_active TEXT DEFAULT '', created_at TEXT DEFAULT CURRENT_TIMESTAMP ) """)

        await db.execute(""" CREATE TABLE IF NOT EXISTS dictionary ( id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, set_name TEXT, english TEXT, uzbek TEXT, ai_info TEXT DEFAULT '', status TEXT DEFAULT 'new', progress INTEGER DEFAULT 0, difficulty INTEGER DEFAULT 1, review_count INTEGER DEFAULT 0, correct_count INTEGER DEFAULT 0, wrong_count INTEGER DEFAULT 0, last_reviewed TEXT DEFAULT '', next_review TEXT DEFAULT '', created_at TEXT DEFAULT CURRENT_TIMESTAMP ) """)

        await db.execute(""" CREATE TABLE IF NOT EXISTS referrals ( id INTEGER PRIMARY KEY AUTOINCREMENT, inviter_id INTEGER, invited_id INTEGER, created_at TEXT DEFAULT CURRENT_TIMESTAMP ) """)

        await db.execute(""" CREATE TABLE IF NOT EXISTS achievements ( id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, achievement_name TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP ) """)

        await db.execute(""" CREATE TABLE IF NOT EXISTS premium_sets ( id INTEGER PRIMARY KEY AUTOINCREMENT, set_name TEXT, description TEXT, price INTEGER DEFAULT 100 ) """)

        await db.execute(""" CREATE TABLE IF NOT EXISTS shop_purchases ( id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, item_name TEXT, price INTEGER, created_at TEXT DEFAULT CURRENT_TIMESTAMP ) """)

        await db.commit()
