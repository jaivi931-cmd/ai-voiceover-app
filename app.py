import os
from flask import Flask, request, jsonify, render_template_string, send_file
from flask_cors import CORS
import requests
from moviepy import VideoFileClip, AudioFileClip
import tempfile

app = Flask(__name__)
CORS(app)

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>VOXIFYR - AI Localizer</title>
    <style>
        body { font-family: sans-serif; background: #0f172a; color: #fff; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .card { background: #1e293b; padding: 2rem; border-radius: 12px; width: 400px; text-align: center; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }
        h1 { color: #38bdf8; margin-bottom: 1rem; }
        input, button { width: 100%; margin-top: 10px; padding: 10px; border-radius: 6px; border: none; box-sizing: border-box; }
        button { background: #0284c7; color: white; font-weight: bold; cursor: pointer; }
        button:hover { background: #0369a1; }
    </style>
</head>
<body>
    <div class="card">
        <h1>VOXIFYR AI</h1>
        <p>Ultra-Fast AI Video Voiceover & Localization</p>
        <p style="color: #4ade80;">System Status: ONLINE 🚀</p>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
