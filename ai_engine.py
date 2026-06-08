import aiohttp
import logging

from config import (
    DEEPSEEK_API_KEY,
    DEEPSEEK_URL,
    AI_MODEL
)

try:
    import whisper
    _whisper_model = whisper.load_model("base")
    WHISPER_AVAILABLE = True
except Exception:
    _whisper_model = None
    WHISPER_AVAILABLE = False
    logging.warning("Whisper/torch not available. Voice transcription will be disabled.")

async def generate_word_data(word):
    prompt = f""" You are an English teacher. Explain this English word in BOTH English and Uzbek. Word: {word} Answer format: 🇬🇧 English explanation: ... 🇺🇿 Uzbek explanation: ... 📌 Example sentence: ... """

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": AI_MODEL,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(DEEPSEEK_URL, headers=headers, json=payload) as response:
                data = await response.json()
                
                if "error" in data:
                    logging.error(f"DeepSeek API Error: {data['error']}")
                    return f"❌ AI Server xatoligi: {data['error'].get('message', 'Noma\'lum xato')}"
                
                return data["choices"][0]["message"]["content"]
    except Exception as e:
        logging.error(f"Xatolik yuz berdi: {e}")
        return f"❌ AI bilan bog'lanishda xatolik yuz berdi."


async def ai_teacher_response(text):
    prompt = f""" You are a professional English teacher. Talk with the student in BOTH English and Uzbek. Correct grammar mistakes. Explain difficult words. User message: {text} """

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": AI_MODEL,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(DEEPSEEK_URL, headers=headers, json=payload) as response:
                data = await response.json()
                
                if "error" in data:
                    logging.error(f"DeepSeek API Error: {data['error']}")
                    return f"❌ AI Server xatoligi: {data['error'].get('message', 'Noma\'lum xato')}"
                    
                return data["choices"][0]["message"]["content"]
    except Exception as e:
        logging.error(f"Xatolik yuz berdi: {e}")
        return f"❌ AI bilan bog'lanishda xatolik yuz berdi."


async def speech_to_text(file_path):
    if not WHISPER_AVAILABLE or _whisper_model is None:
        return None
    result = _whisper_model.transcribe(file_path)
    return result["text"]
    async def analyze_voice_pronunciation(recognized_text):
        prompt = f"""You are an expert English pronunciation coach and phonetics teacher. The student just sent a voice message, and our Speech-to-Text system transcribed it as: "{recognized_text}" Analyze this result and reply to the student in BOTH English and Uzbek. 1. If the text looks grammatically correct and correctly pronounced, praise them and give a short tip. 2. If the transcribed text looks like a common mispronunciation (e.g., they wanted to say "Laptop" but it got recognized as something else due to accent, or the sentence has bad grammar), gently point out what might be wrong and provide the correct pronunciation or spelling rules. Keep the response encouraging, structured, and easy to understand for an English learner. """

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": AI_MODEL,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(DEEPSEEK_URL, headers=headers, json=payload) as response:
                data = await response.json()

                if "error" in data:
                    logging.error(f"DeepSeek API Error: {data['error']}")
                    return f"❌ AI Server xatoligi: {data['error'].get('message', 'Noma’lum xato')}"

                return data["choices"][0]["message"]["content"]

    except Exception as e:
        logging.error(f"Xatolik yuz berdi: {e}")
        return "❌ AI bilan bog‘lanishda xatolik yuz berdi."
        
    
