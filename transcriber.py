import whisper
import os
from pydub import AudioSegment
import tempfile

model = None  # will be loaded based on selection in app

def set_model_size(size):
    global model
    model = whisper.load_model(size)

def transcribe_audio(file_path):
    try:
        if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
            return "[ERROR] File is missing or empty."

        # Convert MP3 to WAV if needed
        if file_path.lower().endswith(".mp3"):
            audio = AudioSegment.from_mp3(file_path)
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_wav:
                audio.export(tmp_wav.name, format="wav")
                file_path = tmp_wav.name

        result = model.transcribe(file_path, fp16=False)
        return result["text"]

    except Exception as e:
        return f"[ERROR] Transcription failed: {str(e)}"


