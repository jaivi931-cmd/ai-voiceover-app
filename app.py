import os
from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
from dotenv import load_dotenv
import whisper
import requests
from moviepy import VideoFileClip, AudioFileClip
import tempfile

load_dotenv()

app = Flask(__name__, template_folder='.')
CORS(app)

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

print("⚡ Loading Whisper AI Engine...")
model = whisper.load_model("base")
print("✅ Whisper AI Ready!")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/transcribe', methods=['POST'])
def transcribe():
    if 'video' not in request.files:
        return jsonify({"error": "No video file provided"}), 400
    
    file = request.files['video']
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_video:
        file.save(temp_video.name)
        temp_video_path = temp_video.name

    try:
        result = model.transcribe(temp_video_path)
        os.remove(temp_video_path)
        return jsonify({"script": result['text'].strip()})
    except Exception as e:
        if os.path.exists(temp_video_path):
            os.remove(temp_video_path)
        return jsonify({"error": str(e)}), 500

@app.route('/translate', methods=['POST'])
def translate():
    data = request.json
    text = data.get('text', '')
    target_lang = data.get('target_lang', 'English')

    if not text:
        return jsonify({"error": "No text provided"}), 400

    prompt = f"Translate the following video voiceover script accurately into {target_lang}:\n\n{text}"
    
    try:
        response = requests.post(
            "https://text.pollinations.ai/",
            json={"messages": [{"role": "user", "content": prompt}]},
            headers={"Content-Type": "application/json"}
        )
        return jsonify({"translated_text": response.text.strip()})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/localize-video', methods=['POST'])
def localize_video():
    if 'video' not in request.files or 'script' not in request.form:
        return jsonify({"error": "Missing video or script"}), 400

    video_file = request.files['video']
    script = request.form['script']
    voice_id = request.form.get('voice_id', 'JBFqnCBsd6RMkjVDRZzb')

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_vid:
        video_file.save(temp_vid.name)
        input_video_path = temp_vid.name

    # ElevenLabs AI Voiceover Synthesis
    tts_url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVENLABS_API_KEY
    }
    data = {
        "text": script,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.8}
    }

    response = requests.post(tts_url, json=data, headers=headers)
    if response.status_code != 200:
        return jsonify({"error": "Voice AI Error: " + response.text}), 500

    temp_audio_path = tempfile.mktemp(suffix=".mp3")
    with open(temp_audio_path, 'wb') as f:
        f.write(response.content)

    output_video_path = tempfile.mktemp(suffix=".mp4")
    try:
        video_clip = VideoFileClip(input_video_path)
        new_audio = AudioFileClip(temp_audio_path)
        
        # Audio & Video Syncing (MoviePy v2 compatibility)
        if hasattr(video_clip, 'with_audio'):
            final_clip = video_clip.with_audio(new_audio)
        else:
            final_clip = video_clip.set_audio(new_audio)
            
        final_clip.write_videofile(output_video_path, codec="libx264", audio_codec="aac")

        video_clip.close()
        new_audio.close()
        os.remove(input_video_path)
        os.remove(temp_audio_path)

        return send_file(output_video_path, mimetype="video/mp4", as_attachment=True, download_name="localized_pro_video.mp4")
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000, debug=True)