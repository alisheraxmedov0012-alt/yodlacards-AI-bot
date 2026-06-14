import os
import aiohttp
import logging

# OpenRouter API kalitini xavfsiz oʻqib olish
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

WHISPER_AVAILABLE = False

async def generate_word_data(word):
    prompt = f"""
You are an English teacher.
Explain this English word in BOTH English and Uzbek.

Word: {word}

Answer format:
🇬🇧 English explanation:
...
🇺🇿 Uzbek explanation:
...
📌 Example sentence:
...
"""
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "google/gemma-4-31b-it:free", # To'liq va to'g'ri bepul model ID'si
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                data = await response.json()
                if "error" in data:
                    logging.error(f"OpenRouter Error: {data['error']}")
                    return "❌ Sun'iy intellekt xatolik berdi."
                
                return data["choices"][0]["message"]["content"]
    except Exception as e:
        logging.error(f"Xatolik yuz berdi: {e}")
        return "❌ AI bilan bogʻlanishda xatolik yuz berdi."

async def ai_teacher_response(text):
    prompt = f"""
You are a professional English teacher.
Talk with the student in BOTH English and Uzbek.
Correct grammar mistakes.
Explain difficult words.

User message:
{text}
"""
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "google/gemma-4-31b-it:free", # Bu yerda ham aniq ID nomi
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                data = await response.json()
                if "error" in data:
                    logging.error(f"OpenRouter Error: {data['error']}")
                    return "❌ Sun'iy intellekt xatolik berdi."
                
                return data["choices"][0]["message"]["content"]
    except Exception as e:
        logging.error(f"Xatolik yuz berdi: {e}")
        return "❌ AI bilan bogʻlanishda xatolik yuz berdi."

async def speech_to_text(file_path):
    return None

async def analyze_voice_pronunciation(recognized_text):
    return "Ovozli funksiya hozircha faol emas."
    
