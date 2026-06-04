import os
import subprocess
import socket
import platform

def get_ip_info() -> str:
    try:
        if platform.system() == "Windows":
            result = subprocess.run(["ipconfig"], capture_output=True, text=True, timeout=5)
        else:
            result = subprocess.run(["ip", "addr"], capture_output=True, text=True, timeout=5)
        return result.stdout
    except Exception as e:
        return f"Xato: {e}"

def ping_host(host: str, count: int = 4) -> str:
    try:
        if platform.system() == "Windows":
            result = subprocess.run(["ping", "-n", str(count), host], capture_output=True, text=True, timeout=15)
        else:
            result = subprocess.run(["ping", "-c", str(count), host], capture_output=True, text=True, timeout=15)
        return result.stdout if result.stdout else f"Xato: {result.stderr}"
    except subprocess.TimeoutExpired:
        return f"{host} ga ping vaqti tugadi."
    except Exception as e:
        return f"Xato: {e}"

def get_active_connections() -> str:
    try:
        if platform.system() == "Windows":
            result = subprocess.run(["netstat", "-an"], capture_output=True, text=True, timeout=5)
        else:
            result = subprocess.run(["ss", "-tuln"], capture_output=True, text=True, timeout=5)
        return result.stdout
    except Exception as e:
        return f"Xato: {e}"

def dns_lookup(domain: str) -> str:
    try:
        ip = socket.gethostbyname(domain)
        return f"{domain} → {ip}"
    except Exception as e:
        return f"Xato: {e}"

def get_network_stats() -> str:
    try:
        if platform.system() == "Windows":
            result = subprocess.run(["netstat", "-e"], capture_output=True, text=True, timeout=5)
        else:
            result = subprocess.run(["cat", "/proc/net/dev"], capture_output=True, text=True, timeout=5)
        return result.stdout
    except Exception as e:
        return f"Xato: {e}"

def check_internet() -> str:
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return "Internet ulanish mavjud."
    except Exception:
        return "Internet ulanish yo'q."

def process_network_command(text: str) -> str:
    text_lower = text.lower()

    if "ip" in text_lower and ("ko'rsat" in text_lower or "tekshir" in text_lower):
        return get_ip_info()
    elif "ping" in text_lower:
        parts = text.split()
        for part in parts:
            if "." in part or part.isalpha():
                if part.lower() not in ["ping", "ni", "ga", "bajar"]:
                    return ping_host(part)
        return ping_host("8.8.8.8")
    elif "ulanish" in text_lower or "connection" in text_lower:
        return get_active_connections()
    elif "dns" in text_lower:
        parts = text.split()
        for part in parts:
            if "." in part:
                return dns_lookup(part)
        return "DNS tekshirish uchun domen kiriting."
    elif "internet" in text_lower:
        return check_internet()
    elif "tarmoq" in text_lower and "statistika" in text_lower:
        return get_network_stats()

    return "Tarmoq buyrug'i tushunilmadi."
