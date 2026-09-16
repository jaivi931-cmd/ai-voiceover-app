import os
import requests
from flask import Flask, jsonify, render_template_string, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Direct fallback key to prevent Render Environment variable read failures
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "sk_ff3a3ef8bea876ca71344946e33dc9d7ee5e23df62408928")

HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VOXIFYR - AI Video Studio</title>
</head>
<body>
    <h1>VOXIFYR AI Backend Live</h1>
</body>
</html>
"""

@app.route('/')
def home():
    try:
        with open('index.html', 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
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

    api_key = ELEVENLABS_API_KEY
    if not api_key:
        return jsonify({"error": "API Key missing"}), 500

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": api_key.strip()
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
