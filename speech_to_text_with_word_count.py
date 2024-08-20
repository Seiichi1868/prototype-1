import speech_recognition as sr
from gtts import gTTS
import playsound

# マイクのインデックスを指定
recognizer = sr.Recognizer()

with sr.Microphone(device_index=0) as source:
    recognizer.adjust_for_ambient_noise(source, duration=1)
    print("Please speak...")
    audio = recognizer.listen(source)

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