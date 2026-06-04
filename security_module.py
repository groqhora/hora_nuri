import os
import subprocess
import socket
import hashlib
import platform
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

SECURITY_PROMPT = """Sen kiberxavfsizlik bo'yicha mutaxassissan.
Xavfsizlik savollarga aniq, amaliy va qisqa javob ber."""

def scan_ports(host: str, ports: list = None) -> str:
    if ports is None:
        ports = [21, 22, 23, 25, 80, 443, 3306, 5432, 8080]
    try:
        open_ports = []
        for port in ports:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            if sock.connect_ex((host, port)) == 0:
                open_ports.append(port)
            sock.close()
        return f"{host} da ochiq portlar: {open_ports}" if open_ports else f"{host} da ochiq port topilmadi."
    except Exception as e:
        return f"Xato: {e}"

def check_network() -> str:
    try:
        if platform.system() == "Windows":
            result = subprocess.run(["ipconfig"], capture_output=True, text=True, timeout=5)
        else:
            result = subprocess.run(["ip", "addr"], capture_output=True, text=True, timeout=5)
        return result.stdout
    except Exception as e:
        return f"Xato: {e}"

def hash_text(text: str, algorithm: str = "sha256") -> str:
    try:
        if algorithm == "md5":
            return hashlib.md5(text.encode()).hexdigest()
        elif algorithm == "sha1":
            return hashlib.sha1(text.encode()).hexdigest()
        return hashlib.sha256(text.encode()).hexdigest()
    except Exception as e:
        return f"Xato: {e}"

def security_advice(question: str) -> str:
    if not GROQ_AVAILABLE:
        return "Kiberxavfsizlik AI hozircha ishlamayapti."
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SECURITY_PROMPT},
                {"role": "user", "content": question}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Xato: {e}"

def process_security_command(text: str) -> str:
    text_lower = text.lower()

    if "port" in text_lower and ("skan" in text_lower or "tekshir" in text_lower):
        parts = text.split()
        for part in parts:
            if "." in part or part.isdigit():
                return scan_ports(part)
        return scan_ports("localhost")
    elif "tarmoq" in text_lower and "tekshir" in text_lower:
        return check_network()
    elif "hash" in text_lower:
        parts = text.split("hash", 1)
        if len(parts) > 1:
            return hash_text(parts[1].strip())
        return "Hash qilinadigan matnni kiriting."
    elif any(word in text_lower for word in ["xavfsizlik", "hujum", "himoya", "zaiflik", "exploit", "hack", "virus", "malware"]):
        return security_advice(text)

    return "Kiberxavfsizlik buyrug'i tushunilmadi."
