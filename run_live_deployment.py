import subprocess
import sys
import time
import re
import os
from pathlib import Path

CLOUDFLARED_PATH = Path(os.environ.get("LOCALAPPDATA", "")) / "Temp" / "cloudflared.exe"

def start_live_deployment():
    print("🚀 Step 1: Starting ReviewLens Web Application Server...")
    server_proc = subprocess.Popen(
        [sys.executable, "run.py"],
        cwd=str(Path(__file__).resolve().parent),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    time.sleep(2)

    print("🌐 Step 2: Creating Cloudflare Public HTTPS Tunnel...")
    tunnel_cmd = [str(CLOUDFLARED_PATH), "tunnel", "--url", "http://127.0.0.1:8000"]
    tunnel_proc = subprocess.Popen(
        tunnel_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    public_url = None
    start_wait = time.time()
    
    # Read output until trycloudflare url is printed
    while time.time() - start_wait < 25:
        line = tunnel_proc.stdout.readline()
        if not line:
            time.sleep(0.1)
            continue
        
        # Look for https://*.trycloudflare.com
        match = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", line)
        if match:
            public_url = match.group(0)
            break

    if public_url:
        print("\n" + "="*60)
        print("🎉 YOUR LIVE PUBLIC DEPLOYMENT IS READY!")
        print(f"👉 PUBLIC URL: {public_url}")
        print("="*60 + "\n")
        
        # Save URL to a text file for easy reference
        with open("DEPLOYED_URL.txt", "w", encoding="utf-8") as f:
            f.write(public_url + "\n")
            
        print("App is running live in the background. Anyone with this link can access ReviewLens!")
    else:
        print("⚠️ Tunnel started, checking connection...")

    # Keep running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping services...")
        tunnel_proc.terminate()
        server_proc.terminate()

if __name__ == "__main__":
    start_live_deployment()
