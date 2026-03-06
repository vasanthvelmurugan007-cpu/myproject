"""
SENTINEL AGENT — PhishGuard AI v3
Runs on your phone (via Termux on Android) and sends GPS to PhishGuard server.

SETUP:
1. Install Termux from F-Droid
2. Install Termux:API app from F-Droid (for real GPS)
3. Inside Termux: pkg install python termux-api
4. pip install requests
5. Edit C2_SERVER and DEVICE_IMEI below
6. python sentinel_agent.py
"""

import time, json, os, sys, hashlib, socket, platform
from datetime import datetime

try:
    import requests
except ImportError:
    os.system(f"{sys.executable} -m pip install requests")
    import requests

# ── EDIT THESE ────────────────────────────────────────────────
C2_SERVER    = "http://YOUR_PC_IP:5000"      # PhishGuard server IP
DEVICE_IMEI  = "YOUR_15_DIGIT_IMEI"          # Dial *#06# to find
DEVICE_NAME  = "My Phone"
SECRET_TOKEN = "phishguard_sentinel_2024"    # Must match server
PING_INTERVAL = 5                            # seconds
# ──────────────────────────────────────────────────────────────

def get_location():
    # Method 1: Real Android GPS via Termux API (best)
    try:
        import subprocess
        r = subprocess.run(['termux-location','-p','gps','-r','once'],
            capture_output=True,text=True,timeout=12)
        if r.returncode == 0:
            d = json.loads(r.stdout)
            return {"lat":d["latitude"],"lon":d["longitude"],
                    "accuracy":d.get("accuracy",5),"altitude":d.get("altitude",0),
                    "speed":d.get("speed",0),"bearing":d.get("bearing",0),
                    "method":"GPS_TERMUX","provider":"android_gps"}
    except Exception: pass

    # Method 2: IP geolocation fallback
    try:
        r = requests.get("http://ip-api.com/json/",timeout=5)
        d = r.json()
        if d.get("status")=="success":
            return {"lat":d["lat"],"lon":d["lon"],"accuracy":2000,
                    "altitude":0,"speed":0,"bearing":0,
                    "method":"IP_GEOLOCATION","city":d.get("city",""),
                    "state":d.get("regionName",""),"country":d.get("country",""),
                    "isp":d.get("isp","")}
    except Exception: pass
    return None

def get_battery():
    try:
        import subprocess
        r = subprocess.run(['termux-battery-status'],capture_output=True,text=True,timeout=5)
        if r.returncode==0:
            d=json.loads(r.stdout)
            return {"percentage":d.get("percentage",-1),"status":d.get("status","unknown"),"plugged":d.get("plugged","unknown")}
    except Exception: pass
    return {"percentage":-1,"status":"unknown"}

def send_ping(seq):
    loc = get_location()
    if not loc:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠ No location"); return False
    payload = {
        "token":SECRET_TOKEN,"imei":DEVICE_IMEI,
        "device_id":hashlib.md5(DEVICE_IMEI.encode()).hexdigest()[:16],
        "device_name":DEVICE_NAME,"seq":seq,
        "timestamp":datetime.utcnow().isoformat()+"Z",
        "local_time":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "location":loc,"battery":get_battery(),
        "network":{"hostname":socket.gethostname(),"platform":platform.system()}
    }
    try:
        r = requests.post(f"{C2_SERVER}/api/tracker/ping",json=payload,
            timeout=10,headers={"X-Device-Token":SECRET_TOKEN})
        if r.status_code==200:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✓ Ping #{seq} | {loc['lat']:.6f},{loc['lon']:.6f} | {loc['method']}")
            return True
    except requests.exceptions.ConnectionError:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ✗ Cannot reach {C2_SERVER}")
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ✗ {e}")
    return False

if __name__ == "__main__":
    print(f"  SENTINEL AGENT v3 — {DEVICE_NAME}")
    print(f"  Server: {C2_SERVER}")
    print(f"  IMEI:   {DEVICE_IMEI}")
    print(f"  Press Ctrl+C to stop\n")
    seq=0
    while True:
        try:
            send_ping(seq); seq+=1; time.sleep(PING_INTERVAL)
        except KeyboardInterrupt:
            print("\n  Agent stopped."); break
