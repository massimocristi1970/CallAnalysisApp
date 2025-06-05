import whisper
import os
from pydub import AudioSegment
import tempfile

model = None  # Model will be loaded based on selection in app

def set_model_size(size):
    global model
    model = whisper.load_model(size)

def transcribe_audio(file_path):
    try:
        if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
            return "[ERROR] File is missing or empty."

        is_temp = False  # Flag to track if we created a temp file

        # Convert MP3 to temporary WAV file
        if file_path.lower().endswith(".mp3"):
            audio = AudioSegment.from_mp3(file_path)
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_wav:
                audio.export(tmp_wav.name, format="wav")
                file_path = tmp_wav.name
                is_temp = True


        result = model.transcribe(file_path, fp16=False)
        transcript = result["text"]

        # Clean up temporary file
        if is_temp and os.path.exists(file_path):
            os.remove(file_path)

        return transcript

    except Exception as e:
        return f"[ERROR] Transcription failed: {str(e)}"

