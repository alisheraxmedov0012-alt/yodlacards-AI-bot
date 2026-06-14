import os
import aiohttp
import logging

# Railway oʻzgaruvchilaridan xavfsiz oʻqib olish
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

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
    # Google v1beta API uchun eng toʻgʻri va barqaror URL manzili
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                data = await response.json()
                if "error" in data:
                    logging.error(f"Gemini API Error: {data['error']}")
                    return "❌ AI server xatoligi yuz berdi."
                
                return data["candidates"][0]["content"]["parts"][0]["text"]
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
    # Ikkala funksiyada ham URL bir xil boʻlishi shart
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                data = await response.json()
                if "error" in data:
                    logging.error(f"Gemini API Error: {data['error']}")
                    return "❌ AI server xatoligi yuz berdi."
                
                return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        logging.error(f"Xatolik yuz berdi: {e}")
        return "❌ AI bilan bogʻlanishda xatolik yuz berdi."

async def speech_to_text(file_path):
    return None

async def analyze_voice_pronunciation(recognized_text):
    return "Ovozli funksiya hozircha faol emas."
    
