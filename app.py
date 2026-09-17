import os
import requests
import subprocess
import tempfile
from flask import Flask, request, jsonify, send_file, render_template, session
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from deep_translator import GoogleTranslator

app = Flask(__name__, template_folder='templates')
app.secret_key = os.environ.get("SECRET_KEY", "voxifyr_super_secret_key_999")
CORS(app)

# 1. Security & Rate Limiting (Protects server and API key from bot attacks)
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"]
)

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

LANG_CODES = {
    'English': 'en',
    'Hindi': 'hi',
    'Spanish': 'es',
    'French': 'fr',
    'German': 'de'
}

# 2. Free Database / Session-based Credits (Zero cost, gives 3 free video renders per user)
USER_CREDITS = {}

@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "VOXIFYR AI Backend Active & Fully Operational with Security"})

# 3. Free User Authentication & Session Login
@app.route('/api/auth/login', methods=['POST'])
@limiter.limit("10 per minute")
def api_login():
    data = request.json or {}
    email = data.get('email', '').strip().lower()
    if not email:
        return jsonify({'error': 'Email is required'}), 400
    
    session['user'] = email
    if email not in USER_CREDITS:
        USER_CREDITS[email] = 3  # 3 Free credits per user
        
    return jsonify({'success': True, 'email': email, 'credits': USER_CREDITS[email]})

@app.route('/api/auth/status', methods=['GET'])
def auth_status():
    user = session.get('user')
    if not user:
        return jsonify({'logged_in': False})
    return jsonify({'logged_in': True, 'email': user, 'credits': USER_CREDITS.get(user, 3)})

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    session.pop('user', None)
    return jsonify({'success': True})

@app.route('/api/tts', methods=['POST'])
@limiter.limit("5 per minute") # Strict security on expensive AI text-to-speech calls
def generate_tts():
    try:
        user = session.get('user')
        if not user:
            user = "guest@voxifyr.ai"
            if user not in USER_CREDITS:
                USER_CREDITS[user] = 3

        if USER_CREDITS.get(user, 0) <= 0:
            return jsonify({'error': 'Free credit limit reached! You have used all your free AI video renders.'}), 403

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

        # Deduct 1 credit on successful generation
        USER_CREDITS[user] -= 1

        temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        temp_audio.write(response.content)
        temp_audio.close()

        res = send_file(temp_audio.name, mimetype='audio/mpeg')
        res.headers['X-Translated-Text'] = requests.utils.quote(translated_text)
        res.headers['X-Remaining-Credits'] = str(USER_CREDITS[user])
        return res

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/merge-video', methods=['POST'])
@limiter.limit("5 per minute")
def merge_video():
    try:
        if 'video' not in request.files or 'audio' not in request.files:
            return jsonify({'error': 'Both video and audio files are required'}), 400

        video_file = request.files['video']
        audio_file = request.files['audio']
        is_vertical = request.form.get('vertical', 'false') == 'true'
        add_subtitles = request.form.get('subtitles', 'false') == 'true'
        script_text = request.form.get('script_text', '')

        temp_v = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
        temp_a = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        output_v = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')

        video_file.save(temp_v.name)
        audio_file.save(temp_a.name)

        temp_v.close()
        temp_a.close()
        output_v.close()

        filters = []
        if is_vertical:
            filters.append('crop=ih*9/16:ih')

        if add_subtitles and script_text:
            clean_text = script_text.replace("'", "").replace('"', "").replace(":", "-")
            if len(clean_text) > 80:
                clean_text = clean_text[:77] + "..."
            
            sub_filter = f"drawtext=text='{clean_text}':fontcolor=white:fontsize=24:box=1:boxcolor=black@0.6:boxborderw=5:x=(w-text_w)/2:y=h-50"
            filters.append(sub_filter)

        if filters:
            vf_arg = ','.join(filters)
            cmd = [
                'ffmpeg', '-y',
                '-i', temp_v.name,
                '-i', temp_a.name,
                '-vf', vf_arg,
                '-c:v', 'libx264',
                '-preset', 'fast',
                '-c:a', 'aac',
                '-map', '0:v:0',
                '-map', '1:a:0',
                '-shortest',
                output_v.name
            ]
        else:
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
        return jsonify({'error': f"Video merging failed: {str(e)} "}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
