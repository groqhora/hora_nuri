import os
import asyncio
from groq import Groq

try:
    import sounddevice as sd
    import scipy.io.wavfile as wav
    AUDIO_AVAILABLE = True
except Exception:
    AUDIO_AVAILABLE = False

class VoiceEngine:
    def __init__(self):
        raw_key = os.getenv("GROQ_API_KEY_1") or os.getenv("GROQ_API_KEY")
        self.api_key = raw_key.strip('"').strip("'") if raw_key else None
        self.temp_audio_file = "temp_voice.wav"
        self.groq_client = None

        if self.api_key and AUDIO_AVAILABLE:
            try:
                self.groq_client = Groq(api_key=self.api_key)
                print("[NURI.VOICE] Groq Whisper va Audio drayverlar faol.")
            except Exception as e:
                print(f"[NURI.VOICE] Groq audio mijozida xato: {e}")
        else:
            print("[NURI.VOICE] Ovozli rejim vaqtincha nofaol.")

    async def speak(self, text: str):
        if not text or not text.strip():
            return
        await asyncio.to_thread(text_to_speech, text)

    async def listen_groq_whisper(self, duration: int = 4) -> str:
        if not self.groq_client or not AUDIO_AVAILABLE:
            await asyncio.sleep(1.5)
            return ""

        fs = 16000
        try:
            loop = asyncio.get_event_loop()

            def record_audio():
                try:
                    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
                    sd.wait()
                    return recording
                except Exception:
                    return None

            recording = await loop.run_in_executor(None, record_audio)
            if recording is None:
                await asyncio.sleep(1.0)
                return ""

            wav.write(self.temp_audio_file, fs, recording)

            def call_whisper_api():
                with open(self.temp_audio_file, "rb") as file:
                    transcription = self.groq_client.audio.transcriptions.create(
                        file=(self.temp_audio_file, file.read()),
                        model="whisper-large-v3",
                        language="uz",
                        response_format="text"
                    )
                return str(transcription).strip()

            response_text = await loop.run_in_executor(None, call_whisper_api)

            if os.path.exists(self.temp_audio_file):
                os.remove(self.temp_audio_file)

            return response_text

        except Exception:
            if os.path.exists(self.temp_audio_file):
                try:
                    os.remove(self.temp_audio_file)
                except:
                    pass
            await asyncio.sleep(1.0)
            return ""


def text_to_speech(text: str):
    if not text or not text.strip():
        return
    try:
        import edge_tts
        import tempfile

        async def _speak():
            communicate = edge_tts.Communicate(text, voice="uz-UZ-SardorNeural")
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                tmp = f.name
            await communicate.save(tmp)
            if os.name == "nt":
                os.system(f'start /min "" "{tmp}"')
            else:
                os.system(f"mpg123 '{tmp}' 2>/dev/null &")

        asyncio.run(_speak())
    except Exception:
        pass
