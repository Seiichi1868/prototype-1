from flask import Flask, render_template, request
import speech_recognition as sr
from gtts import gTTS
import os

app = Flask(__name__)

def format_text_for_speech(text):
    # 文末を検出してポーズを追加する
    text = text.replace(". ", ".... ")  # 文末に長めのポーズを挿入
    text = text.replace(", ", ",,,, ")  # カンマにも短いポーズを挿入
    return text

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    version_choice = request.form['version_choice']
    recognizer = sr.Recognizer()

    # 音声ファイルを受け取る部分を追加するなど、録音部分の代替方法を検討してください。

    # 録音したファイルを音声認識にかける（Herokuでは事前に録音した音声ファイルを使う想定）
    WAVE_OUTPUT_FILENAME = os.path.join("static", "recorded_audio.wav")
    with sr.AudioFile(WAVE_OUTPUT_FILENAME) as source:
        audio = recognizer.record(source)  # 音声ファイル全体を処理

    try:
        text = recognizer.recognize_google(audio, language="en-US")
        if not text:
            return render_template('index.html', error="Sorry, the recording was too short. Please try again.")

        # 句読点に基づいてポーズを追加
        formatted_text = format_text_for_speech(text)
        word_count = len(formatted_text.split())

        # TTSの処理（速度を調整）
        if version_choice == "1":
            tts = gTTS(text=formatted_text, lang='en', slow=True)
            tts.save(os.path.join("static", "output.mp3"))
            return render_template('index.html', text=formatted_text, word_count=word_count, original_audio_path=WAVE_OUTPUT_FILENAME, audio_path=os.path.join("static", "output.mp3"))
        elif version_choice == "2":
            return render_template('index.html', text=formatted_text, word_count=word_count, original_audio_path=WAVE_OUTPUT_FILENAME, audio_path=WAVE_OUTPUT_FILENAME)

    except sr.UnknownValueError:
        return render_template('index.html', error="Sorry, I could not understand the audio.")
    except sr.RequestError as e:
        return render_template('index.html', error=f"Could not request results; {e}")
    except Exception as e:
        return render_template('index.html', error=f"An error occurred: {e}")

if __name__ == "__main__":
    if not os.path.exists('static'):
        os.makedirs('static')
    port = int(os.environ.get("PORT", 5000))  # 環境変数からポート番号を取得
    app.run(host='0.0.0.0', port=port, debug=False)  # デバッグモードをオフ

