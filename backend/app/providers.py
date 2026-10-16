import io
import wave
from typing import Protocol


class SpeechRecognizer(Protocol):
    def transcribe(self, wav_path: str) -> list[dict]: ...


class Translator(Protocol):
    def translate(self, text: str, context: str) -> str: ...


class SpeechSynthesizer(Protocol):
    def synthesize(self, text: str, voice: str) -> bytes: ...


class MockRecognizer:
    def transcribe(self, wav_path: str) -> list[dict]:
        return [{"start_ms": 0, "end_ms": 1000, "speaker": "speaker_1", "text": "你好"}]


class MockTranslator:
    def translate(self, text: str, context: str) -> str:
        return "Xin chào"


class MockSynthesizer:
    def synthesize(self, text: str, voice: str) -> bytes:
        output = io.BytesIO()
        with wave.open(output, "wb") as audio:
            audio.setnchannels(1)
            audio.setsampwidth(2)
            audio.setframerate(16000)
            audio.writeframes(bytes(32000))
        return output.getvalue()
