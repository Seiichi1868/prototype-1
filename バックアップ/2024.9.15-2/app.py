from flask import Flask, render_template, request
import speech_recognition as sr
from gtts import gTTS
import pyaudio
import wave
import os

app = Flask(__name__)

# 録音設定
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024
WAVE_OUTPUT_FILENAME = os.path.join("static", "recorded_audio.wav")

def record_audio(record_seconds):
    audio = pyaudio.PyAudio()

    # 録音開始
    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True,
                        frames_per_buffer=CHUNK)

    print("Recording...")
    frames = []

    for _ in range(0, int(RATE / CHUNK * record_seconds)):
        try:
            data = stream.read(CHUNK, exception_on_overflow=False)
            frames.append(data)
        except IOError as e:
            print(f"Error while recording: {e}")
            break

    print("Finished recording.")

    # ストリームを停止
    stream.stop_stream()
    stream.close()
    audio.terminate()

    # 録音データをファイルに保存
    with wave.open(WAVE_OUTPUT_FILENAME, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))

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
    record_seconds = int(request.form['recording_time'])  # フォームから選択された録音時間を取得
    recognizer = sr.Recognizer()

    # 選択された秒数で録音を行う
    record_audio(record_seconds)

    # 録音したファイルを音声認識にかける
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
    app.run(host='0.0.0.0', port=5000, debug=True)
