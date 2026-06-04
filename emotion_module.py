import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

try:
    GROQ_KEY = os.getenv("GROQ_API_KEY_1") or os.getenv("GROQ_API_KEY")
    groq_client = Groq(api_key=GROQ_KEY) if GROQ_KEY else None
    GROQ_AVAILABLE = bool(groq_client)
except Exception:
    GROQ_AVAILABLE = False
    groq_client = None

EMOTION_PROMPT = """Sen foydalanuvchi matnidan hissiyotni aniqlaydigan mutaxassissan.
Quyidagi hissiyotlardan birini aniqla: Xursand, g'amgin, g'azablangan, qo'rqqan, hayron, bezovta, tinch.
Qisqa javob ber."""

def detect_emotion(text: str) -> dict:
    if not GROQ_AVAILABLE:
        return {"emotion": "noaniq", "level": "o'rta", "advice": ""}
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": EMOTION_PROMPT},
                {"role": "user", "content": f"Matndan hissiyotni aniqla:\n{text}"}
            ],
            max_tokens=200
        )
        result = response.choices[0].message.content
        return {"emotion": result, "level": "o'rta", "advice": result}
    except Exception as e:
        return {"emotion": "noaniq", "level": "o'rta", "advice": str(e)}

def adapt_response(text: str, response: str) -> str:
    if not GROQ_AVAILABLE:
        return response
    try:
        emotion_data = detect_emotion(text)
        emotion = emotion_data.get("emotion", "")
        prompt = f"Foydalanuvchi hissiyoti: {emotion}\nAsl javob: {response}\nJavobni hissiyotga mos qayta yoz. Qisqa bo'lsin."
        adapted = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500
        )
        return adapted.choices[0].message.content
    except Exception:
        return response

def get_emotion_response(emotion: str) -> str:
    responses = {
        "xursand": "Sizning kayfiyatingiz zo'r! Bugun nima yaxshi bo'ldi?",
        "g'amgin": "Tushunaman, ba'zida qiyin bo'ladi. Yordam bera olamanmi?",
        "g'azablangan": "Sakin bo'ling, muammoni birga hal qilamiz.",
        "qo'rqqan": "Xavotir olmang, men yordamchingizman.",
        "hayron": "Qiziqarli savol! Birga o'ylaymiz.",
        "bezovta": "Hamma narsa yaxshi bo'ladi. Nima bezovta qilyapti?",
        "tinch": "Yaxshi kayfiyat! Qanday yordam kerak?",
    }
    for key, val in responses.items():
        if key in emotion.lower():
            return val
    return ""

def process_emotion_command(text: str) -> str:
    result = detect_emotion(text)
    return f"Hissiyot: {result.get('emotion', 'noaniq')}"
