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
RECORD_SECONDS = 30
WAVE_OUTPUT_FILENAME = "static/recorded_audio.wav"

def record_audio():
    audio = pyaudio.PyAudio()

    # 録音開始
    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True,
                        frames_per_buffer=CHUNK)

    print("Recording...")
    frames = []

    for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    version_choice = request.form['version_choice']
    recognizer = sr.Recognizer()

    # 30秒間録音を行う
    record_audio()

    # 録音したファイルを音声認識にかける
    with sr.AudioFile(WAVE_OUTPUT_FILENAME) as source:
        audio = recognizer.record(source, duration=30)  # 音声ファイル全体を処理

    try:
        text = recognizer.recognize_google(audio, language="en-US")
        if not text:
            return render_template('index.html', error="Sorry, the recording was too short. Please try again.")

        word_count = len(text.split())

        if version_choice == "1":
            tts = gTTS(text=text, lang='en')
            tts.save("static/output.mp3")
            return render_template('index.html', text=text, word_count=word_count, audio_path='static/output.mp3')
        elif version_choice == "2":
            return render_template('index.html', text=text, word_count=word_count, audio_path=WAVE_OUTPUT_FILENAME)

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