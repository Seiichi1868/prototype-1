from flask import Flask, render_template, request
import speech_recognition as sr
from gtts import gTTS
import wave
import os
import time  # 追加してユニークなファイル名を生成

app = Flask(__name__)

# 録音設定
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024

# ファイル名をユニークにするためにタイムスタンプを追加
def generate_unique_filename():
    return os.path.join("static", f"recorded_audio_{int(time.time())}.wav")

def record_audio(record_seconds):
    WAVE_OUTPUT_FILENAME = generate_unique_filename()  # ここでファイル名を生成
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

    return WAVE_OUTPUT_FILENAME  # 録音されたファイル名を返す

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    version_choice = request.form['version_choice']
    record_seconds = int(request.form['recording_time'])  # フォームから選択された録音時間を取得
    recognizer = sr.Recognizer()

    # 選択された秒数で録音を行う
    WAVE_OUTPUT_FILENAME = record_audio(record_seconds)

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
            output_mp3 = os.path.join("static", f"output_{int(time.time())}.mp3")  # ユニークなファイル名
            tts.save(output_mp3)
            return render_template('index.html', text=formatted_text, word_count=word_count, original_audio_path=WAVE_OUTPUT_FILENAME, audio_path=output_mp3)
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
