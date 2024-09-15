from flask import Flask, render_template, request
import speech_recognition as sr
from gtts import gTTS
import os

app = Flask(__name__)

WAVE_OUTPUT_FILENAME = os.path.join("static", "recorded_audio.wav")

def format_text_for_speech(text):
    # 文末を検出してポーズを追加する
    text = text.replace(". ", ".... ")  # 文末に長めのポーズを挿入
    text = text.replace(", ", ",,,, ")  # カンマにも短いポーズを挿入
    return text

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_audio():
    if 'audio_data' not in request.files:
        return render_template('index.html', error="No audio file uploaded.")

    # アップロードされた音声ファイルを保存
    audio_file = request.files['audio_data']
    audio_file.save(WAVE_OUTPUT_FILENAME)

    recognizer = sr.Recognizer()

    # 音声ファイルを音声認識にかける
    try:
        with sr.AudioFile(WAVE_OUTPUT_FILENAME) as source:
            audio = recognizer.record(source)  # 音声ファイル全体を処理

        text = recognizer.recognize_google(audio, language="en-US")
        if not text:
            return render_template('index.html', error="Sorry, the recording was too short. Please try again.")

        # 句読点に基づいてポーズを追加
        formatted_text = format_text_for_speech(text)
        word_count = len(formatted_text.split())

        # TTSの処理
        tts = gTTS(text=formatted_text, lang='en', slow=False)
        tts_output_path = os.path.join("static", "output.mp3")
        tts.save(tts_output_path)

        return render_template('index.html', text=formatted_text, word_count=word_count, original_audio_path=WAVE_OUTPUT_FILENAME, audio_path=tts_output_path)

    except sr.UnknownValueError:
        return render_template('index.html', error="Sorry, I could not understand the audio.")
    except sr.RequestError as e:
        return render_template('index.html', error=f"Could not request results; {e}")
    except Exception as e:
        return render_template('index.html', error=f"An error occurred: {e}")

if __name__ == "__main__":
    if not os.path.exists('static'):
        os.makedirs('static')
    app.run(host='0.0.0.0', port=5000, debug=True)
