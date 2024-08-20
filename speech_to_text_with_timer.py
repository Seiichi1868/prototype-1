import speech_recognition as sr
from gtts import gTTS
import playsound
import threading
import time

# カウントダウンを表示する関数
def countdown(time_limit):
    for i in range(time_limit, 0, -1):
        print(f"Time remaining: {i} seconds", end="\r")
        time.sleep(1)
    print("Time's up!                           ")

# マイクのインデックスを指定
recognizer = sr.Recognizer()

# 録音とカウントダウンを同時に開始
time_limit = 30  # 制限時間を秒で設定

with sr.Microphone(device_index=0) as source:
    recognizer.adjust_for_ambient_noise(source, duration=1)
    print("Please speak... (Recording will stop after 30 seconds)")

    # カウントダウンを別のスレッドで開始
    countdown_thread = threading.Thread(target=countdown, args=(time_limit,))
    countdown_thread.start()

    # 制限時間まで録音
    audio = recognizer.listen(source, timeout=time_limit, phrase_time_limit=time_limit)

# 音声をテキストに変換
try:
    text = recognizer.recognize_google(audio, language="en-US")
    print("You said: " + text)
    
    # 単語数をカウント
    word_count = len(text.split())
    print(f"Word count: {word_count}")
    
    # テキストを音声に変換
    tts = gTTS(text=text, lang='en')
    tts.save("output.mp3")

    # 音声を再生
    playsound.playsound("output.mp3")

except sr.UnknownValueError:
    print("Sorry, I could not understand the audio.")
except sr.RequestError as e:
    print(f"Could not request results; {e}")
except Exception as e:
    print(f"An error occurred: {e}")