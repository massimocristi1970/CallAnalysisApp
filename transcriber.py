import whisper
import streamlit as st
import os
from pydub import AudioSegment
import tempfile

@st.cache_resource
def load_whisper_model(size):
    return whisper.load_model(size)

model = None  # Cached model will be stored here

def set_model_size(size):
    global model
    model = load_whisper_model(size)
def transcribe_audio(file_path):
    try:
        if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
            return "[ERROR] File is missing or empty."

        is_temp = False  # Track if we're converting MP3 to WAV

        # ✅ Convert MP3 to temp WAV
        if file_path.lower().endswith(".mp3"):
            audio = AudioSegment.from_mp3(file_path)
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_wav:
                audio.export(tmp_wav.name, format="wav")
                tmp_wav.flush()
                file_path = tmp_wav.name
                is_temp = True

        # ✅ DEBUG: Check actual file being transcribed
        print(f"Transcribing: {file_path}")

        result = model.transcribe(file_path, fp16=False)
        transcript = result["text"]

        # ✅ Clean up temp WAV
        if is_temp and os.path.exists(file_path):
            os.remove(file_path)

        return transcript

    except Exception as e:
        return f"[ERROR] Transcription failed: {str(e)}"
