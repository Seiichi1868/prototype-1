import speech_recognition as sr

# マイクのインデックスを指定
recognizer = sr.Recognizer()

# ここでデバイスインデックスを指定
with sr.Microphone(device_index=0) as source:
    recognizer.adjust_for_ambient_noise(source, duration=1)
    print("Please speak...")
    audio = recognizer.listen(source)

# 音声をテキストに変換
try:
    text = recognizer.recognize_google(audio, language="en-US")
    print("You said: " + text)
except sr.UnknownValueError:
    print("Sorry, I could not understand the audio.")
except sr.RequestError as e:
    print(f"Could not request results; {e}")