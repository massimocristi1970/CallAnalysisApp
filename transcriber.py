# transcriber.py
import whisper

model = whisper.load_model("base")  # Options: "tiny", "base", "small", "medium", "large"

def transcribe_audio(file_path):
    result = model.transcribe(file_path)
    return result['text']
