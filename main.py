import os
import sys
import asyncio
import importlib.util
import logging
import concurrent.futures
import aiohttp
from dotenv import load_dotenv

def check_or_create_env():
    if getattr(sys, 'frozen', False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))

    env_path = os.path.join(base, ".env")

    # GUI rejimida input() mutlaqo ishlatilmaydi! 
    # Agar fayl bo'lmasa, shunchaki standart namuna yaratiladi.
    if not os.path.exists(env_path):
        with open(env_path, "w") as f:
            f.write("ADMIN_PASSWORD=darling\n")
            f.write("NURI_INNER_PASSWORD=root\n")
            f.write("GROQ_API_KEY=YOUR_GROQ_KEY_HERE\n")
            f.write("GROQ_API_KEY_1=YOUR_GROQ_KEY_HERE\n")
            f.write("GEMINI_API_KEY=YOUR_GEMINI_KEY_HERE\n")
    
    load_dotenv(env_path)

# Dastur import bo'lishi bilanoq .env xavfsiz yuklanadi
check_or_create_env()

from ai_engine import AIEngine
from keyboard_module import KeyboardModule
from telegram_module import TelegramModule
import voice_engine as ve
import identity_engine as ie
import memory_module as mm

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NURICore:
    def __init__(self):
        print("\n[NURI.SYSTEM] Ishga tushmoqda...")
        mm.init_db()
        ie.setup_identity()
        self.ai = AIEngine()
        self.keyboard = KeyboardModule()
        self.telegram = TelegramModule(core_processor=self._process_command_sync)
        self.current_user = "stranger"
        self.current_role = "stranger"
        self.plugins = {}
        self._load_plugins()
        print("[NURI.SYSTEM] Tayyor ✅\n")

    def _load_plugins(self):
        if getattr(sys, 'frozen', False):
            base = os.path.dirname(sys.executable)
        else:
            base = os.path.dirname(os.path.abspath(__file__))

        plugins_dir = os.path.join(base, "plugins")
        os.makedirs(plugins_dir, exist_ok=True)

        for filename in sorted(os.listdir(plugins_dir)):
            if filename.endswith(".py") and not filename.startswith("_"):
                try:
                    spec = importlib.util.spec_from_file_location(
                        filename[:-3], os.path.join(plugins_dir, filename)
                    )
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        self.plugins[filename[:-3]] = module
                except Exception as e:
                    logger.error(f"Plugin {filename}: {e}")

    async def speak_and_print(self, text: str):
        if text and text.strip():
            print(f"\n[NURI]: {text}")
            try:
                await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(None, ve.text_to_speech, text),
                    timeout=5.0
                )
            except Exception:
                pass

    def _process_command_sync(self, command: str) -> str:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                future = asyncio.run_coroutine_threadsafe(self.process_command(command), loop)
                return future.result(timeout=45)
            return loop.run_until_complete(self.process_command(command))
        except concurrent.futures.TimeoutError:
            return "Vaqt tugadi."
        except Exception as e:
            logger.error(f"Sync error: {e}")
            return f"Xatolik: {str(e)[:80]}"

    async def process_command(self, command: str) -> str:
        if not command or not command.strip():
            return ""

        cmd = command.strip()
        lower = cmd.lower()

        if lower.startswith(("admin:", "user:")):
            prefix = lower.split(":", 1)[0]
            password = cmd.split(":", 1)[1].strip()
            admin_pass = os.getenv("ADMIN_PASSWORD")

            if prefix == "admin" and password == admin_pass:
                self.current_role = "admin"
                self.current_user = "admin"
                msg = "Admin sifatida qayta kirdingiz!"
                mm.save_conversation("admin", cmd, msg)
                await self.speak_and_print(msg)
                return msg
            elif prefix == "user" and ie.verify_user_password(password):
                self.current_user = ie.get_username_by_password(password) or "user"
                self.current_role = "user"
                msg = f"User sifatida kirdingiz ({self.current_user})!"
                mm.save_conversation(self.current_user, cmd, msg)
                await self.speak_and_print(msg)
                return msg
            return "Parol xato!"

        if self.current_role == "stranger":
            return "Avval parol kiriting!"

        if self.current_role == "admin":
            if any(kw in lower for kw in ["status", "holat"]):
                ai_status = await self.ai.get_status()
                response = (
                    f"NURI STATUS\n"
                    f"Foydalanuvchi: {self.current_user}\n"
                    f"AI Engines: {ai_status['total_engines']}\n"
                    f"Groq kalitlar: {ai_status['groq_keys']}\n"
                    f"Gemini: {'✅' if ai_status['gemini_available'] else '❌'}\n"
                    f"Plugins: {len(self.plugins)}"
                )
                mm.save_conversation(self.current_user, cmd, response)
                await self.speak_and_print(response)
                return response

            if "plugin" in lower and "qayta yukla" in lower:
                self.plugins.clear()
                self._load_plugins()
                await self.speak_and_print("Plugins qayta yuklandi")
                return "OK"

        try:
            history = mm.get_history(self.current_user, limit=5) or ""
            if len(history) > 2000:
                history = history[-2000:]
            full_prompt = f"{history}\nFoydalanuvchi: {cmd}" if history else cmd
            ai_response = await asyncio.wait_for(
                self.ai.generate_response(full_prompt), timeout=35.0
            )
            result = ai_response if ai_response else "Bo'sh javob"
            mm.save_conversation(self.current_user, cmd, result)
            
            # Ovoz interfeysni qotirmasligi uchun async fonda chaqiriladi
            asyncio.create_task(self.speak_and_print(result))
            return result
        except Exception as e:
            msg = f"AI xatosi: {str(e)[:80]}"
            mm.save_conversation(self.current_user, cmd, msg)
            return msg
