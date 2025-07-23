
from src.utils.speech_recognizer import SpeechRecognitionAgent
from src.utils.wake_word_listener import WakeWordListener
from src.utils.langgraph_router import route_to_langgraph
from dotenv import load_dotenv
import os
import sys # Import the sys module

def run_sentinel_agent():
    load_dotenv()
    access_key = os.getenv("PORCUPINE_KEY")
    keyword_path = "src/wakeword/Sentinel_en_windows_v3_0_0.ppn"

    wake_listener = WakeWordListener(keyword_path=keyword_path, access_key=access_key)
    recognizer = SpeechRecognitionAgent()

    wake_listener.start()
    print("🟢 Waiting for wake word... (Press Ctrl+C to exit)")

    try:
        while True:
            wake_listener.wait_for_wake_word()
            print("🎙️ Listening for command...")
            command = recognizer.listen_command(timeout=5, phrase_time_limit=10)

            if command:
                print(f"🧠 Recognized: {command}")
                response = route_to_langgraph(command)
                print(f"🤖 LangGraph response: {response}")
            else:
                print("⚠️ No command detected.")
    except KeyboardInterrupt:
        print("\n🛑 Shutting down Sentinel agent.")
        # Add any cleanup code here if needed, e.g., wake_listener.stop()
        wake_listener.stop()
        sys.exit(0) # Exit the program cleanly