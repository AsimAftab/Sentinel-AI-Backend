# src/utils/wake_word_listener.py

import pvporcupine
import pyaudio
import struct
import threading

class WakeWordListener:
    def __init__(self, keyword_path, access_key, sensitivities=0.7):
        self.porcupine = pvporcupine.create(
            access_key=access_key,
            keyword_paths=[keyword_path],
            sensitivities=[sensitivities]
        )
        self.pa = pyaudio.PyAudio()
        self.stream = self.pa.open(
            rate=self.porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=self.porcupine.frame_length
        )
        self._wake_event = threading.Event()
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._listen)

    def start(self):
        self._wake_event.clear()
        self._stop_event.clear()
        self._thread.start()

    def _listen(self):
        while not self._stop_event.is_set():
            pcm = self.stream.read(self.porcupine.frame_length, exception_on_overflow=False)
            pcm = struct.unpack_from("h" * self.porcupine.frame_length, pcm)
            result = self.porcupine.process(pcm)
            if result >= 0:
                print("🗣️ Wake word detected!")
                self._wake_event.set()

    def wait_for_wake_word(self):
        self._wake_event.wait()
        self._wake_event.clear()

    def stop(self):
        self._stop_event.set()
        self._thread.join()
        self.stream.stop_stream()
        self.stream.close()
        self.pa.terminate()
        self.porcupine.delete()
