import speech_recognition as sr

class SpeechRecognitionAgent:
    def __init__(self, energy_threshold=300, pause_threshold=0.8):
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = energy_threshold
        self.recognizer.pause_threshold = pause_threshold
        self.microphone = sr.Microphone()

    def adjust_for_ambient_noise(self, duration=1):
        try:
            with self.microphone as source:
                print("🔈 Calibrating microphone for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=duration)
                print(f"📏 Energy threshold set to: {self.recognizer.energy_threshold}")
                return True
        except Exception as e:
            print(f"❌ Failed to calibrate mic: {e}")
            return False

    def listen_command(self, timeout=5, phrase_time_limit=10):
        try:
            with self.microphone as source:
                print("🎙️ Listening for a command...")
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            command = self.recognizer.recognize_google(audio)
            return command
        except sr.WaitTimeoutError:
            print("⌛ Listening timed out.")
        except sr.UnknownValueError:
            print("🤷 Could not understand audio.")
        except sr.RequestError as e:
            print(f"⚠️ Could not request results from Google API: {e}")
        return None

    def listen_in_background(self, callback):
        print("🎧 Background listener started.")
        return self.recognizer.listen_in_background(self.microphone, callback)


def default_callback(recognizer, audio):
    try:
        command = recognizer.recognize_google(audio)
        print(f"🗣️ Heard (background): {command}")
        # 👇 Route to LangGraph agent here (will be defined in next step)
        # response = my_langgraph.invoke({"input": command})
        # print(f"🤖 LangGraph response: {response}")
    except sr.UnknownValueError:
        print("🤷 Background: Could not understand audio.")
    except sr.RequestError as e:
        print(f"⚠️ Background: API error: {e}")
