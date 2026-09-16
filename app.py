import os
import requests
from flask import Flask, jsonify, render_template_string, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VOXIFYR - AI Video Localization</title>
    <style>
        body { background-color: #0b0f19; color: #ffffff; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .card { background: #161e2e; border: 1px solid #233044; padding: 2.5rem; border-radius: 16px; box-shadow: 0 20px 40px rgba(0,0,0,0.6); text-align: center; max-width: 450px; width: 90%; }
        h1 { color: #38bdf8; font-size: 2.2rem; margin-bottom: 0.5rem; letter-spacing: 1px; }
        p { color: #94a3b8; font-size: 1rem; margin-bottom: 1.5rem; }
        .badge { display: inline-block; background: rgba(56, 189, 248, 0.1); color: #38bdf8; padding: 6px 16px; border-radius: 20px; font-weight: 600; font-size: 0.85rem; border: 1px solid rgba(56, 189, 248, 0.3); }
    </style>
</head>
<body>
    <div class="card">
        <h1>VOXIFYR</h1>
        <p>Enterprise AI Video Voiceover & Localization Platform</p>
        <span class="badge">SYSTEM ONLINE & READY</span>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_LAYOUT)

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "service": "VOXIFYR AI Backend"}), 200

@app.route('/generate-voice', methods=['POST'])
def generate_voice():
    data = request.json or {}
    text = data.get('text')
    voice_id = data.get('voice_id', '21m00Tcm4TlvDq8ikWAM')

    if not text:
        return jsonify({"error": "Text is required"}), 400

    if not ELEVENLABS_API_KEY:
        return jsonify({"error": "API Key missing in environment"}), 500

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVENLABS_API_KEY
    }
    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            return response.content, 200, {'Content-Type': 'audio/mpeg'}
        return jsonify({"error": response.text}), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
