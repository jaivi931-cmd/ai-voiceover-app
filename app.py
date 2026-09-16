import os
import subprocess
import requests
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import whisper

app = Flask(__name__)
CORS(app)

# Load Whisper model for auto speech extraction
print("Loading Whisper model...")
model = whisper.load_model("tiny")
print("Whisper model loaded!")

ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY", "sk_ff3a3ef8bea876ca71344946e33dc9d7ee5e23df62408928")

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "VOXIFYR AI Backend Active & Secure"}), 200

@app.route("/extract-audio", methods=["POST"])
def extract_audio():
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "No video file provided"}), 400
    
    file = request.files['file']
    input_path = "temp_input_video.mp4"
    audio_path = "temp_extracted_audio.wav"
    
    file.save(input_path)
    
    # Extract audio using ffmpeg
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", input_path, "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", audio_path],
            check=True
        )
        # Transcribe audio using Whisper
        result = model.transcribe(audio_path)
        extracted_text = result.get("text", "").strip()
        
        return jsonify({"success": True, "text": extracted_text})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        if os.path.exists(input_path): os.remove(input_path)
        if os.path.exists(audio_path): os.remove(audio_path)

@app.route("/generate-voice", methods=["POST"])
def generate_voice():
    data = request.json or {}
    text = data.get("text", "")
    voice_id = data.get("voice_id", "nPczCjzI2devNBz1zQrb")
    
    if not text:
        return jsonify({"error": "No text provided"}), 400

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
            output_audio = "generated_voice.mp3"
            with open(output_audio, "wb") as f:
                f.write(response.content)
            return send_file(output_audio, mimetype="audio/mpeg")
        else:
            return jsonify({"error": f"ElevenLabs Error: {response.text}"}), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
