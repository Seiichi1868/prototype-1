from flask import Flask, render_template, request, redirect, url_for
import os
import time
import speech_recognition as sr
from pydub import AudioSegment

app = Flask(__name__)

WAVE_OUTPUT_FILENAME = "output.wav"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_audio():
    start_time = time.time()
    print("音声処理開始...")

    # アップロードされた音声ファイルを取得
    if 'file' not in request.files:
        return redirect(request.url)
    
    file = request.files['file']
    
    if file.filename == '':
        return redirect(request.url)
    
    if file:
        file_path = os.path.join(os.getcwd(), 'temp.wav')
        file.save(file_path)
        print(f"ファイル保存完了。経過時間: {time.time() - start_time} 秒")

        # 音声ファイルをWAV形式に変換
        start_conversion_time = time.time()
        sound = AudioSegment.from_file(file_path)
        sound.export(WAVE_OUTPUT_FILENAME, format="wav")
        print(f"WAV変換完了。経過時間: {time.time() - start_conversion_time} 秒")

        # 音声認識処理
        start_recognition_time = time.time()
        recognizer = sr.Recognizer()
        with sr.AudioFile(WAVE_OUTPUT_FILENAME) as source:
            audio = recognizer.record(source)
        
        try:
            text = recognizer.recognize_google(audio, language="en-US")
            print(f"音声認識完了。経過時間: {time.time() - start_recognition_time} 秒")
            return f"認識されたテキスト: {text}"
        except sr.UnknownValueError:
            return "Google Speech Recognitionは音声を認識できませんでした。"
        except sr.RequestError as e:
            return f"Google Speech Recognitionサービスにアクセスできませんでした; {e}"

    print(f"処理全体完了。経過時間: {time.time() - start_time} 秒")
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
