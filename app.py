import os
import requests
import subprocess
import tempfile
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({"status": "VOXIFYR AI Backend Active & Fully Operational"})

@app.route('/api/tts', methods=['POST'])
def generate_tts():
    try:
        data = request.json or {}
        text = data.get('text', '')
        voice_id = data.get('voice_id', '21m00Tcm4TlvDq8ikWAM')

        if not text:
            return jsonify({'error': 'No text provided'}), 400

        if not ELEVENLABS_API_KEY:
            return jsonify({'error': 'ELEVENLABS_API_KEY not configured on Render'}), 500

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": ELEVENLABS_API_KEY
        }
        payload = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }

        response = requests.post(url, json=payload, headers=headers)
        if response.status_code != 200:
            return jsonify({'error': f'ElevenLabs API error: {response.text}'}), response.status_code

        return response.content, 200, {'Content-Type': 'audio/mpeg'}

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Endpoint for Merging Audio + Video into Final MP4
@app.route('/api/merge-video', methods=['POST'])
def merge_video():
    try:
        if 'video' not in request.files or 'audio' not in request.files:
            return jsonify({'error': 'Both video and audio files are required'}), 400

        video_file = request.files['video']
        audio_file = request.files['audio']

        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_video, \
             tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_audio, \
             tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as output_video:

            video_file.save(temp_video.name)
            audio_file.save(temp_audio.name)

            # FFmpeg Command to combine video with new audio
            cmd = [
                'ffmpeg', '-y',
                '-i', temp_video.name,
                '-i', temp_audio.name,
                '-c:v', 'copy',
                '-c:a', 'aac',
                '-map', '0:v:0',
                '-map', '1:a:0',
                '-shortest',
                output_video.name
            ]

            subprocess.run(cmd, check=True)
            return send_file(output_video.name, mimetype='video/mp4', as_attachment=True, download_name='voxifyr_localized_video.mp4')

    except Exception as e:
        return jsonify({'error': f"Video merging failed: {str(e)}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
