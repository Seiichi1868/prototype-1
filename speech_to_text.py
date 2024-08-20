import speech_recognition as sr

# マイクから音声を取得
recognizer = sr.Recognizer()

with sr.Microphone() as source:
    print("話してください...")
    audio = recognizer.listen(source)

# 音声をテキストに変換
try:
    text = recognizer.recognize_google(audio, language="ja-JP")
    print("あなたが言った内容: " + text)
except sr.UnknownValueError:
    print("音声が理解できませんでした")
except sr.RequestError as e:
    print(f"サービスにアクセスできませんでした; {e}")