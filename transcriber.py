import whisper
import os

def transcribe_audio(file_path, model_size="small"):
    try:
        # Load model dynamically based on sidebar selection
        model = whisper.load_model(model_size)

        # Check file existence and non-zero size
        if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
            return "[ERROR] File is missing or empty."

        # Optional: validate WAV format
        import wave
        try:
            with wave.open(file_path, 'rb') as wf:
                if wf.getnframes() == 0:
                    return "[ERROR] Audio contains no frames."
        except wave.Error:
            pass  # Might not be WAV, which is fine for Whisper.

        result = model.transcribe(file_path, fp16=False)
        return result["text"]

    except Exception as e:
        return f"[ERROR] Transcription failed: {str(e)}"


