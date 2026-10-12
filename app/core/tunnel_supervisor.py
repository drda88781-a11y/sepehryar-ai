"""
Tunnel Supervisor for Sepehryar AI Enterprise.
Maintains persistent connection for https://sepehryarai.loca.lt with auto-reconnect.
"""
import time
import subprocess
import urllib.request
from pathlib import Path

PORT = 8080
SUBDOMAIN = "sepehryarai"
CHECK_URL = f"https://{SUBDOMAIN}.loca.lt/health"


def is_local_healthy() -> bool:
    try:
        req = urllib.request.Request(f"http://127.0.0.1:{PORT}/health")
        with urllib.request.urlopen(req, timeout=2) as resp:
            return resp.status == 200
    except Exception:
        return False


def is_tunnel_healthy() -> bool:
    try:
        req = urllib.request.Request(CHECK_URL, headers={"bypass-tunnel-reminder": "true", "User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status == 200
    except Exception:
        return False


def start_tunnel():
    # Kill any dangling localtunnel node instances
    subprocess.run("taskkill /F /IM node.exe /T", shell=True, capture_output=True)
    time.sleep(1)
    cmd = f"cmd.exe /c npx -y localtunnel --port {PORT} --subdomain {SUBDOMAIN}"
    return subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main():
    print(f"Starting Sepehryar AI Tunnel Supervisor for https://{SUBDOMAIN}.loca.lt...")
    proc = None
    while True:
        try:
            # Only manage tunnel if local server is actually alive
            if is_local_healthy():
                if not is_tunnel_healthy():
                    print("[Supervisor] Tunnel unhealthy or disconnected. Restarting...")
                    proc = start_tunnel()
                    time.sleep(10)
                else:
                    time.sleep(15)
            else:
                time.sleep(5)
        except Exception as e:
            time.sleep(10)


if __name__ == "__main__":
    main()
