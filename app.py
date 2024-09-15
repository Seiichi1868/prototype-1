from flask import Flask, render_template, request
import speech_recognition as sr
import os

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    if 'audio-file' not in request.files:
        return render_template('index.html', error="No audio file uploaded.")

    # アップロードされた音声ファイルを保存
    audio_file = request.files['audio-file']
    audio_path = os.path.join("static", "uploaded_audio.wav")
    audio_file.save(audio_path)

    # 音声ファイルを音声認識にかける
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_path) as source:
        audio = recognizer.record(source)

    try:
        text = recognizer.recognize_google(audio, language="en-US")
        return render_template('index.html', text=text)
    except sr.UnknownValueError:
        return render_template('index.html', error="Could not understand the audio.")
    except sr.RequestError as e:
        return render_template('index.html', error=f"Request error: {e}")
    except Exception as e:
        return render_template('index.html', error=f"An error occurred: {e}")

if __name__ == "__main__":
    if not os.path.exists('static'):
        os.makedirs('static')
    app.run(host='0.0.0.0', port=5000, debug=True)
