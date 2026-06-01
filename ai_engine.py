import os
import asyncio
from groq import Groq

try:
    from google import genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

from dotenv import load_dotenv
load_dotenv()


class AIEngine:
    def __init__(self):
        """NURI 4-lik Gibrid AI (Groq x3 + Gemini)"""

        self.groq_keys = []
        for g_key in ["GROQ_API_KEY_1", "GROQ_API_KEY_2", "GROQ_API_KEY_3"]:
            val = os.getenv(g_key)
            if val:
                clean = val.strip().strip('"').strip("'").strip()
                if clean:
                    self.groq_keys.append(clean)

        raw_gemini = os.getenv("GEMINI_KEY")
        self.gemini_key = raw_gemini.strip().strip('"').strip("'").strip() if raw_gemini else None

        self.engines_order = ["groq_1", "groq_2", "groq_3", "gemini"]
        self.current_engine_index = 0
        self.groq_client = None
        self.gemini_client = None

        self.setup_current_engine()

    def setup_current_engine(self):
        if self.current_engine_index >= len(self.engines_order):
            print("[NURI.AI] Tizimda ishlaydigan API kalit qolmadi!")
            return

        engine = self.engines_order[self.current_engine_index]

        if engine.startswith("groq"):
            idx = int(engine.split("_")[1]) - 1
            if idx < len(self.groq_keys):
                print(f"[NURI.AI] Groq Kalit-{id