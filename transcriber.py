import whisper
import os

model = whisper.load_model("small")

def transcribe_audio(file_path):
    try:
        # Check file existence and non-zero size
        if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
            return "[ERROR] File is missing or empty."

        # Optional: check if file is a valid audio file (basic attempt)
        import wave
        try:
            with wave.open(file_path, 'rb') as wf:
                if wf.getnframes() == 0:
                    return "[ERROR] Audio contains no frames."
        except wave.Error:
            pass  # Might not be WAV; Whisper may still handle it.

        result = model.transcribe(file_path, fp16=False)
        return result["text"]
    except Exception as e:
        return f"[ERROR] Transcription failed: {str(e)}"


