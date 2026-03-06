"""
╔══════════════════════════════════════════════════════════════╗
║   PHISHGUARD AI v3.0 — Unified Backend                      ║
║   8 Security Modules + Sentinel Live Tracker                ║
║   Powered by Google Gemini API + OpenStreetMap              ║
╚══════════════════════════════════════════════════════════════╝
"""

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os, json, re, threading, hashlib
from datetime import datetime
import google.generativeai as genai

app = Flask(__name__)
CORS(app)

# ── Config ────────────────────────────────────────────────────
GEMINI_API_KEY  = os.environ.get("GEMINI_API_KEY", "")
TRACKER_TOKEN   = "phishguard_sentinel_2024"
DATA_FILE       = "sentinel_data.json"

# ── Tracker store ─────────────────────────────────────────────
device_store = {}
store_lock   = threading.Lock()

def load_data():
    global device_store
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE) as f:
                device_store = json.load(f)
            print(f"  Loaded {len(device_store)} tracked device(s).")
        except Exception:
            device_store = {}

def save_data():
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(device_store, f)
    except Exception as e:
        print(f"  Save warning: {e}")

# ── Gemini helpers ────────────────────────────────────────────
def get_model():
    if not GEMINI_API_KEY:
        return None
    genai.configure(api_key=GEMINI_API_KEY)
    return genai.GenerativeModel("gemini-2.5-flash")

def gemini(prompt, image_data=None):
    model = get_model()
    if not model:
        return json.dumps({"error": "GEMINI_API_KEY not configured. Click ⚙ Settings to add your key."})
    try:
        if image_data:
            import PIL.Image, io
            img = PIL.Image.open(io.BytesIO(image_data))
            return model.generate_content([prompt, img]).text
        return model.generate_content(prompt).text
    except Exception as e:
        return json.dumps({"error": str(e)})

def parse_json(raw):
    raw = raw.strip()
    raw = re.sub(r"```(?:json)?", "", raw).strip("`").strip()
    try:
        return json.loads(raw)
    except Exception:
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            try: return json.loads(m.group())
            except: pass
    return {"raw_response": raw, "error": "Could not parse response"}

import urllib.parse

# ══════════════════════════════════════════════════════════════
#  MODULE 1 — PHISHING URL
# ══════════════════════════════════════════════════════════════
@app.route("/api/phishing/check", methods=["POST"])
def phishing_check():
    url = request.json.get("url", "").strip()
    if not url: return jsonify({"error": "No URL provided"}), 400

    suspicious_kw  = ["login","verify","secure","account","update","bank","paypal","amazon","netflix","wallet","reward","prize","lucky","free","kyc","aadhaar","pan","upi","sbi","hdfc","icici","irctc"]
    bad_tlds       = [".tk",".ml",".ga",".cf",".gq",".xyz",".top",".click",".cam",".surf"]
    parsed = urllib.parse.urlparse(url if "://" in url else "http://"+url)
    domain = parsed.netloc.lower()
    flags  = []
    for kw in suspicious_kw:
        if kw in domain: flags.append(f"Keyword '{kw}' in domain")
    for tld in bad_tlds:
        if domain.endswith(tld): flags.append(f"High-risk TLD: {tld}")
    if re.search(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", domain): flags.append("IP address as domain")
    if domain.count(".") > 4: flags.append("Excessive subdomains")
    if len(domain) > 50: flags.append("Unusually long domain")

    prompt = f"""You are a cybersecurity expert for Indian internet users. Analyze this URL: {url}
Heuristic flags already found: {flags}
Respond ONLY with valid JSON:
{{"verdict":"SAFE"|"SUSPICIOUS"|"PHISHING","confidence":0-100,"risk_level":"LOW"|"MEDIUM"|"HIGH"|"CRITICAL","indicators":[],"explanation":"2-3 sentences","recommendation":"action to take"}}"""

    result = parse_json(gemini(prompt))
    result["url"] = url
    result["heuristic_flags"] = flags
    result["timestamp"] = datetime.now().isoformat()
    return jsonify(result)

# ══════════════════════════════════════════════════════════════
#  MODULE 2 — DEEPFAKE
# ══════════════════════════════════════════════════════════════
@app.route("/api/deepfake/analyze", methods=["POST"])
def deepfake_analyze():
    if "image" not in request.files: return jsonify({"error": "No image uploaded"}), 400
    file  = request.files["image"]
    data  = file.read()
    prompt = """You are an AI forensics expert. Analyze this image for deepfake indicators:
facial boundary artifacts, lighting inconsistencies, skin texture anomalies, eye irregularities,
hair/ear boundary blurring, background inconsistencies, compression artifacts.
Respond ONLY with valid JSON:
{"verdict":"AUTHENTIC"|"LIKELY_FAKE"|"DEEPFAKE_DETECTED","confidence":0-100,"risk_level":"LOW"|"MEDIUM"|"HIGH"|"CRITICAL","artifacts_found":[],"explanation":"detailed findings","recommendation":"action"}"""
    result = parse_json(gemini(prompt, image_data=data))
    result["timestamp"] = datetime.now().isoformat()
    return jsonify(result)

# ══════════════════════════════════════════════════════════════
#  MODULE 3 — UPI FRAUD
# ══════════════════════════════════════════════════════════════
@app.route("/api/upi/analyze", methods=["POST"])
def upi_analyze():
    d = request.json
    prompt = f"""You are a financial fraud expert for India. Analyze this UPI payment:
UPI ID: {d.get('upi_id','')}   Message: {d.get('message','')}   Amount: ₹{d.get('amount','')}
Check for: KYC scams, fake government portals, wrong-transfer tricks, UPI impersonation, lottery fraud.
Respond ONLY with valid JSON:
{{"verdict":"LEGITIMATE"|"SUSPICIOUS"|"FRAUD","confidence":0-100,"risk_level":"LOW"|"MEDIUM"|"HIGH"|"CRITICAL","fraud_type":null,"red_flags":[],"explanation":"clear explanation","recommendation":"action"}}"""
    result = parse_json(gemini(prompt))
    result["timestamp"] = datetime.now().isoformat()
    return jsonify(result)

# ══════════════════════════════════════════════════════════════
#  MODULE 4 — DIGITAL ARREST
# ══════════════════════════════════════════════════════════════
@app.route("/api/digital-arrest/analyze", methods=["POST"])
def digital_arrest():
    d = request.json
    prompt = f"""You are a cybercrime expert specializing in India's Digital Arrest scams.
Caller claims: {d.get('caller_info','')}   Script: {d.get('message','')}
Check for: CBI/ED/NCB/TRAI impersonation, illegal parcel claims, video call detention, money to 'safe account'.
Respond ONLY with valid JSON:
{{"verdict":"LEGITIMATE"|"SUSPICIOUS"|"DIGITAL_ARREST_SCAM","confidence":0-100,"risk_level":"LOW"|"MEDIUM"|"HIGH"|"CRITICAL","scam_tactics":[],"impersonated_agency":"agency or null","explanation":"clear explanation","immediate_action":"what to do NOW","report_to":"where to report"}}"""
    result = parse_json(gemini(prompt))
    result["timestamp"] = datetime.now().isoformat()
    return jsonify(result)

# ══════════════════════════════════════════════════════════════
#  MODULE 5 — FAKE JOB
# ══════════════════════════════════════════════════════════════
@app.route("/api/job/analyze", methods=["POST"])
def job_analyze():
    d = request.json
    prompt = f"""You are an employment fraud expert for India's job market.
Company: {d.get('company','')}   Contact: {d.get('contact','')}   Offer: {d.get('job_text','')}
Check for: WFH scams, advance fee fraud, fake multinationals, WhatsApp recruitment, unrealistic pay.
Respond ONLY with valid JSON:
{{"verdict":"LEGITIMATE"|"SUSPICIOUS"|"FAKE_JOB_SCAM","confidence":0-100,"risk_level":"LOW"|"MEDIUM"|"HIGH"|"CRITICAL","scam_type":"type or null","red_flags":[],"explanation":"clear explanation","recommendation":"action","verify_steps":[]}}"""
    result = parse_json(gemini(prompt))
    result["timestamp"] = datetime.now().isoformat()
    return jsonify(result)

# ══════════════════════════════════════════════════════════════
#  MODULE 6 — MISINFORMATION
# ══════════════════════════════════════════════════════════════
@app.route("/api/misinfo/analyze", methods=["POST"])
def misinfo_analyze():
    d = request.json
    prompt = f"""You are a fact-checker for Indian social media and WhatsApp forwards.
Content: {d.get('content','')}   Source: {d.get('source','WhatsApp')}
Check for: fake government schemes, health misinformation, communal content, morphed media, fake celebrity quotes.
Respond ONLY with valid JSON:
{{"verdict":"LIKELY_TRUE"|"UNVERIFIED"|"MISLEADING"|"FAKE","confidence":0-100,"category":"health|political|financial|religious|general","manipulation_tactics":[],"fact_check_summary":"truth vs false","explanation":"analysis","recommendation":"what to do","verify_sources":[]}}"""
    result = parse_json(gemini(prompt))
    result["timestamp"] = datetime.now().isoformat()
    return jsonify(result)

# ══════════════════════════════════════════════════════════════
#  MODULE 7 — SOS SAFETY
# ══════════════════════════════════════════════════════════════
@app.route("/api/sos/analyze", methods=["POST"])
def sos_analyze():
    d = request.json
    prompt = f"""You are a women's safety advisor for India.
Situation: {d.get('situation','')}   Location: {d.get('location','')}
Provide emergency guidance covering: immediate safety steps, digital safety, Indian laws (IPC 354, IT Act), emergency contacts.
Respond ONLY with valid JSON:
{{"threat_level":"LOW"|"MEDIUM"|"HIGH"|"CRITICAL","immediate_steps":[],"emergency_numbers":[{{"name":"","number":"","description":""}}],"legal_options":[],"digital_safety_steps":[],"support_organizations":[{{"name":"","contact":"","service":""}}],"evidence_to_preserve":[],"explanation":"empathetic assessment"}}"""
    result = parse_json(gemini(prompt))
    result["timestamp"] = datetime.now().isoformat()
    return jsonify(result)

# ══════════════════════════════════════════════════════════════
#  MODULE 8 — IMEI REGISTER
# ══════════════════════════════════════════════════════════════
@app.route("/api/imei/register", methods=["POST"])
def imei_register():
    d     = request.json
    imei  = d.get("imei","").strip()
    if not re.match(r"^\d{15}$", imei):
        return jsonify({"error": "Invalid IMEI — must be exactly 15 digits"}), 400

    def luhn(s):
        digits = [int(x) for x in s]
        for i in range(len(digits)-2, -1, -2):
            digits[i] *= 2
            if digits[i] > 9: digits[i] -= 9
        return sum(digits) % 10 == 0

    return jsonify({
        "imei": imei, "device_name": d.get("device_name","My Device"),
        "owner_name": d.get("owner_name",""), "valid": luhn(imei),
        "registered": True, "registration_time": datetime.now().isoformat(),
        "status": "ACTIVE",
        "message": "Device registered. Use CEIR portal (ceir.gov.in) or dial 14422 if stolen.",
        "report_theft_steps": [
            "File FIR at nearest police station with IMEI",
            "Report on CEIR portal: ceir.gov.in or call 14422",
            "Block SIM with your carrier",
            "File complaint at cybercrime.gov.in",
            "Use Sanchar Saathi app by DoT"
        ]
    })

@app.route("/api/imei/check-stolen", methods=["POST"])
def imei_check_stolen():
    imei = request.json.get("imei","").strip()
    prompt = f"""Device IMEI: {imei}. Provide India-specific guidance for checking if this device is stolen and filing FIR.
Respond ONLY with valid JSON:
{{"imei":"{imei}","check_portals":[{{"name":"","url":"","description":""}}],"legal_steps":[],"auto_fir_process":"explanation","recovery_chances":"LOW|MEDIUM|HIGH","recommendation":"actions"}}"""
    result = parse_json(gemini(prompt))
    result["timestamp"] = datetime.now().isoformat()
    return jsonify(result)

# ══════════════════════════════════════════════════════════════
#  SENTINEL TRACKER ENDPOINTS
# ══════════════════════════════════════════════════════════════
@app.route("/api/tracker/ping", methods=["POST"])
def tracker_ping():
    token = request.headers.get("X-Device-Token") or request.json.get("token","")
    if token != TRACKER_TOKEN:
        return jsonify({"error": "Unauthorized"}), 401
    d    = request.json
    imei = d.get("imei","unknown")
    loc  = d.get("location",{})
    if not loc or "lat" not in loc:
        return jsonify({"error": "No location"}), 400

    ping = {
        "seq":        d.get("seq",0),
        "timestamp":  d.get("timestamp", datetime.utcnow().isoformat()+"Z"),
        "local_time": d.get("local_time",""),
        "lat":        loc["lat"], "lon": loc["lon"],
        "accuracy":   loc.get("accuracy",0),
        "altitude":   loc.get("altitude",0),
        "speed":      loc.get("speed",0),
        "bearing":    loc.get("bearing",0),
        "method":     loc.get("method","unknown"),
        "city":       loc.get("city",""), "state": loc.get("state",""),
        "country":    loc.get("country",""), "isp": loc.get("isp",""),
        "battery":    d.get("battery",{}),
        "network":    d.get("network",{}),
        "received_at":datetime.utcnow().isoformat()+"Z"
    }

    with store_lock:
        if imei not in device_store:
            device_store[imei] = {
                "info": {
                    "imei": imei,
                    "device_id":   d.get("device_id",""),
                    "device_name": d.get("device_name","Unknown Device"),
                    "first_seen":  datetime.utcnow().isoformat()+"Z",
                    "status":      "active"
                }, "pings": []
            }
        device_store[imei]["info"]["last_seen"]    = datetime.utcnow().isoformat()+"Z"
        device_store[imei]["info"]["device_name"]  = d.get("device_name","Unknown")
        device_store[imei]["pings"].append(ping)
        if len(device_store[imei]["pings"]) > 500:
            device_store[imei]["pings"] = device_store[imei]["pings"][-500:]
        save_data()

    print(f"[{datetime.now().strftime('%H:%M:%S')}] 📍 {d.get('device_name','?')} | {ping['lat']:.5f},{ping['lon']:.5f} | {ping['method']}")
    return jsonify({"status":"ok","seq":ping["seq"]})

@app.route("/api/tracker/devices")
def tracker_devices():
    with store_lock:
        result = []
        for imei, dev in device_store.items():
            info = dict(dev["info"])
            if dev["pings"]:
                last = dev["pings"][-1]
                info["last_lat"]     = last["lat"]
                info["last_lon"]     = last["lon"]
                info["last_method"]  = last["method"]
                info["last_battery"] = last.get("battery",{}).get("percentage",-1)
                info["last_city"]    = last.get("city","")
                info["total_pings"]  = len(dev["pings"])
                try:
                    from datetime import timezone
                    lt  = datetime.fromisoformat(last["received_at"].replace("Z",""))
                    age = (datetime.utcnow()-lt).total_seconds()
                    info["online"]         = age < 30
                    info["last_ping_age"]  = int(age)
                except Exception:
                    info["online"]         = False
                    info["last_ping_age"]  = 9999
            result.append(info)
    return jsonify(result)

@app.route("/api/tracker/device/<imei>/pings")
def tracker_pings(imei):
    limit = int(request.args.get("limit",200))
    with store_lock:
        if imei not in device_store: return jsonify([])
        return jsonify(device_store[imei]["pings"][-limit:])

@app.route("/api/tracker/device/<imei>/mark-stolen", methods=["POST"])
def mark_stolen(imei):
    with store_lock:
        if imei in device_store:
            device_store[imei]["info"]["status"]    = "stolen"
            device_store[imei]["info"]["stolen_at"] = datetime.utcnow().isoformat()+"Z"
            save_data()
    return jsonify({"status":"ok","imei":imei,"marked":"stolen"})

@app.route("/api/tracker/device/<imei>/clear", methods=["DELETE"])
def clear_device(imei):
    with store_lock:
        if imei in device_store:
            del device_store[imei]
            save_data()
    return jsonify({"status":"ok"})

@app.route("/api/tracker/stats")
def tracker_stats():
    with store_lock:
        total = sum(len(d["pings"]) for d in device_store.values())
        online = 0
        for dev in device_store.values():
            if dev["pings"]:
                try:
                    lt  = datetime.fromisoformat(dev["pings"][-1]["received_at"].replace("Z",""))
                    if (datetime.utcnow()-lt).total_seconds() < 30: online += 1
                except: pass
        return jsonify({"total_devices":len(device_store),"online_devices":online,"total_pings":total,"server_time":datetime.utcnow().isoformat()+"Z"})

# ── System ────────────────────────────────────────────────────
@app.route("/api/health")
def health():
    return jsonify({"status":"online","api_key_configured":bool(GEMINI_API_KEY),"version":"3.0.0","timestamp":datetime.now().isoformat()})

@app.route("/api/config", methods=["POST"])
def set_config():
    global GEMINI_API_KEY
    key = request.json.get("api_key","").strip()
    if key:
        GEMINI_API_KEY = key
        genai.configure(api_key=GEMINI_API_KEY)
        return jsonify({"success":True})
    return jsonify({"error":"No key provided"}), 400

@app.route("/")
def index():
    return render_template("index.html")

# ── Run ───────────────────────────────────────────────────────
if __name__ == "__main__":
    load_data()
    print("="*60)
    print("  PHISHGUARD AI v3.0 — Unified Platform")
    print("  Visit: http://localhost:5000")
    print("="*60)
    if not GEMINI_API_KEY:
        print("  ⚠  GEMINI_API_KEY not set. Configure in the app.")
    app.run(debug=True, host="0.0.0.0", port=5000)
