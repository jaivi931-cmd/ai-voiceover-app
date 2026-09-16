import os
import requests
import subprocess
import tempfile
from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
from deep_translator import GoogleTranslator

app = Flask(__name__, template_folder='templates')
CORS(app)

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

LANG_CODES = {
    'English': 'en',
    'Hindi': 'hi',
    'Spanish': 'es',
    'French': 'fr',
    'German': 'de'
}

@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "VOXIFYR AI Backend Active & Fully Operational"})

@app.route('/api/tts', methods=['POST'])
def generate_tts():
    try:
        data = request.json or {}
        text = data.get('text', '')
        voice_id = data.get('voice_id', 'pNInz6obpgDQGcFmaJgB')
        target_lang = data.get('language', 'English')

        if not text:
            return jsonify({'error': 'No text provided'}), 400

        if not ELEVENLABS_API_KEY:
            return jsonify({'error': 'ELEVENLABS_API_KEY not configured on Render'}), 500

        translated_text = text
        if target_lang in LANG_CODES and target_lang != 'English':
            try:
                lang_code = LANG_CODES[target_lang]
                translated_text = GoogleTranslator(source='auto', target=lang_code).translate(text)
            except Exception as trans_err:
                print(f"Translation error: {trans_err}")

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": ELEVENLABS_API_KEY
        }
        payload = {
            "text": translated_text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }

        response = requests.post(url, json=payload, headers=headers)
        if response.status_code != 200:
            return jsonify({'error': f'ElevenLabs API error: {response.text}'}), response.status_code

        temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        temp_audio.write(response.content)
        temp_audio.close()

        res = send_file(temp_audio.name, mimetype='audio/mpeg')
        res.headers['X-Translated-Text'] = requests.utils.quote(translated_text)
        return res

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/merge-video', methods=['POST'])
def merge_video():
    try:
        if 'video' not in request.files or 'audio' not in request.files:
            return jsonify({'error': 'Both video and audio files are required'}), 400

        video_file = request.files['video']
        audio_file = request.files['audio']

        temp_v = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
        temp_a = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        output_v = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')

        video_file.save(temp_v.name)
        audio_file.save(temp_a.name)

        temp_v.close()
        temp_a.close()
        output_v.close()

        cmd = [
            'ffmpeg', '-y',
            '-i', temp_v.name,
            '-i', temp_a.name,
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-map', '0:v:0',
            '-map', '1:a:0',
            '-shortest',
            output_v.name
        ]

        subprocess.run(cmd, check=True)
        return send_file(output_v.name, mimetype='video/mp4', as_attachment=True, download_name='voxifyr_localized_video.mp4')

    except Exception as e:
        return jsonify({'error': f"Video merging failed: {str(e)}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
