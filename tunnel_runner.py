import sys
import subprocess
import time
import urllib.request
import os
import socket

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PORT = 8080

def get_lan_ip():
    try:
        import psutil
        for iface, addrs in psutil.net_if_addrs().items():
            if any(k in iface.lower() for k in ["wi-fi", "wireless", "ethernet", "lan"]) and "tun" not in iface.lower():
                for addr in addrs:
                    if addr.family == socket.AF_INET and not addr.address.startswith("169.254.") and not addr.address.startswith("127."):
                        return addr.address
    except Exception:
        pass
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "192.168.10.190"

def get_public_ip():
    for url in ["https://api.ipify.org", "https://icanhazip.com", "https://ifconfig.me/ip"]:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "curl/7.68.0"})
            with urllib.request.urlopen(req, timeout=4) as response:
                ip = response.read().decode("utf-8").strip()
                if ip:
                    return ip
        except Exception:
            continue
    return "109.125.160.251"

def ensure_server_running():
    try:
        req = urllib.request.Request(f"http://127.0.0.1:{PORT}/health")
        with urllib.request.urlopen(req, timeout=2) as resp:
            if resp.status == 200:
                return None
    except Exception:
        pass
    
    print("[SERVER] در حال راه‌اندازی سرور هوش مصنوعی سپهریار در پس‌زمینه...")
    server_cmd = ["py", "run.py", "--server", "--port", str(PORT)]
    proc = subprocess.Popen(
        server_cmd,
        cwd=os.path.dirname(os.path.abspath(__file__)),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    time.sleep(3)
    return proc

lan_ip = get_lan_ip()
current_ip = get_public_ip()
target_subdomain = "sepehryar-ai"
server_proc = ensure_server_running()

print("==========================================================")
print("  سامانه دسترسی به نسخه تحت وب سپهریار (کامپیوتر و موبایل)")
print("==========================================================")
print(f"  ۱. آدرس ورود در همین سیستم:")
print(f"     >>> http://127.0.0.1:{PORT} <<<")
print()
print(f"  ۲. آدرس ورود مستقیم در گوشی (اگر به یک وای‌فای متصل هستید):")
print(f"     >>> http://{lan_ip}:{PORT} <<<")
print()
print(f"  ۳. رمز ورود Endpoint IP (در صورت درخواست تایید هویت تونل):")
print(f"     >>> {current_ip} <<<")
print("==========================================================")
print("در حال برقراری تونل امن اینترنتی برای اتصال از راه دور...")
print()
sys.stdout.flush()

cmd = [
    "cmd.exe", "/c",
    f"npx.cmd -y localtunnel --port {PORT} --subdomain {target_subdomain} --local-host 127.0.0.1 --print-requests"
]

while True:
    proc = None
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            encoding="utf-8",
            errors="replace"
        )
        for line in proc.stdout:
            sys.stdout.write(line)
            sys.stdout.flush()
            if "your url is:" in line:
                url_obtained = line.split("your url is:")[-1].strip()
                print("\n" + "="*58)
                print(f"  [موفقیت] تونل اینترنتی فعال شد!")
                print(f"  لینک اختصاصی برای ورود در گوشی از طریق اینترنت همراه:")
                print(f"  >>> {url_obtained} <<<")
                print(f"  (در صورت مشاهده فرم تایید، IP زیر را وارد کنید: {current_ip})")
                print("="*58 + "\n")
                sys.stdout.flush()
        proc.wait()
    except Exception as e:
        print(f"[TUNNEL] خطا: {e}")
        sys.stdout.flush()
    if proc:
        try:
            subprocess.run(f"taskkill /F /T /PID {proc.pid}", shell=True, capture_output=True)
        except Exception:
            pass
    print("[TUNNEL] تلاش مجدد اتصال پس از ۵ ثانیه...")
    sys.stdout.flush()
    time.sleep(5)
