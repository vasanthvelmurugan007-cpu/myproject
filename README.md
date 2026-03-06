# PhishGuard AI v3.0 — Unified Cyber Defense Platform

## What's Included

### 9 Modules in One App
| Module | Description |
|--------|-------------|
| 🎣 Phishing URL | Fake banking/UPI/Aadhaar portals |
| 🖼 Deepfake Detector | AI-generated images, morphed faces |
| 💳 UPI Fraud | Fake payments, KYC scams |
| 🚔 Digital Arrest | Fake CBI/ED/NCB calls |
| 💼 Fake Job | WFH scams, advance fee fraud |
| 📱 Misinformation | WhatsApp forwards, fake news |
| 🆘 SOS Safety | Women's emergency guidance |
| 📲 IMEI Tracker | Device registration, FIR guidance |
| 🗺 Live GPS Tracker | Real-time map (OpenStreetMap, zero API cost) |

## Quick Start

### 1. Install
```bash
pip install flask flask-cors google-generativeai Pillow requests
```

### 2. Run
```bash
# With API key
export GEMINI_API_KEY="AIzaSy_your_key_here"
python app.py

# Without API key (configure inside app)
python app.py
```

### 3. Open
```
http://localhost:5000
```

### 4. Set API Key (if not set above)
Click **⚙ Settings** in the top right → paste your Gemini key → Save

Get a free key at: **aistudio.google.com**

---

## Live GPS Tracker Setup

### Install agent on your phone (Android — Termux)
```bash
# Install Termux from F-Droid + Termux:API app
pkg install python termux-api
pip install requests

# Edit sentinel_agent.py:
C2_SERVER   = "http://YOUR_PC_IP:5000"  # find with: ipconfig / ifconfig
DEVICE_IMEI = "your_15_digit_imei"     # dial *#06#

python sentinel_agent.py
```

### Test without a phone
Open the app → click **🗺 Track** → click **▶ DEMO — Auto Simulate**

---

## Files
```
phishguard_v3/
├── app.py              ← Flask backend (all APIs + tracker)
├── sentinel_agent.py   ← GPS agent (runs on phone)
├── requirements.txt
├── start.sh
├── README.md
├── sentinel_data.json  ← Created automatically (GPS history)
└── templates/
    └── index.html      ← Complete frontend (single file)
```

## API Endpoints
| Endpoint | Method | Module |
|----------|--------|--------|
| `/api/phishing/check` | POST | Phishing |
| `/api/deepfake/analyze` | POST | Deepfake |
| `/api/upi/analyze` | POST | UPI Fraud |
| `/api/digital-arrest/analyze` | POST | Digital Arrest |
| `/api/job/analyze` | POST | Fake Job |
| `/api/misinfo/analyze` | POST | Misinformation |
| `/api/sos/analyze` | POST | SOS |
| `/api/imei/register` | POST | IMEI |
| `/api/imei/check-stolen` | POST | IMEI |
| `/api/tracker/ping` | POST | GPS Agent |
| `/api/tracker/devices` | GET | Tracker |
| `/api/tracker/device/<imei>/pings` | GET | Tracker |
| `/api/tracker/device/<imei>/mark-stolen` | POST | Tracker |
| `/api/health` | GET | System |
| `/api/config` | POST | System |
