# --- SHIM: ensure pyaudioop resolves to stdlib audioop (MUST be first) ---
import sys
try:
    import audioop as _audioop
    sys.modules.setdefault("pyaudioop", _audioop)
except Exception:
    pass

# transcriber.py
import os
import tempfile
import asyncio
import concurrent.futures
from typing import List, Dict, Any, Optional
import hashlib
import yaml
from pathlib import Path
import logging
import torch
import threading
import gc

# Lazy import pattern: import pydub inside functions to ensure shim runs first
def _get_audiosegment():
    """Lazy import AudioSegment to ensure shim runs before pydub imports"""
    try:
        from pydub import AudioSegment
        return AudioSegment
    except Exception as e:
        logging.exception("Failed to import pydub.AudioSegment: %s", e)
        raise RuntimeError("Audio processing requires pydub to be installed and available.\n"
                           "On Streamlit Cloud, ensure pydub is in requirements.txt and ffmpeg is available.")

def _get_pydub_effects():
    """Lazy import pydub.effects to ensure shim runs first"""
    try:
        from pydub.effects import normalize, compress_dynamic_range
        return normalize, compress_dynamic_range
    except Exception as e:
        logging.exception("Failed to import pydub.effects: %s", e)
        raise RuntimeError("Audio processing requires pydub to be installed and available.\n"
                           "On Streamlit Cloud, ensure pydub is in requirements.txt and ffmpeg is available.")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

model = None  # Will hold the Whisper model after it's set
model_lock = threading.Lock()  # Thread safety for model access

def reset_model():
    """Reset the Whisper model when it gets corrupted"""
    global model
    with model_lock:
        if model is not None:
            logger.info("Resetting corrupted Whisper model")
            del model
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            # Reload the model
            model = load_whisper_model("base")  # Force base model for stability
            logger.info("Model reset complete")

def load_config():
    """Load audio configuration"""
    config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
    try:
        with open(config_path, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    except (FileNotFoundError, yaml.YAMLError):
        return {}

@st.cache_resource
def load_whisper_model(size: str):
    """Load Whisper model with caching"""
    try:
        import whisper
        return whisper.load_model(size)
    except Exception as e:
        logger.error(f"Failed to load Whisper model: {e}")
        raise

def set_model_size(size: str):
    """Set the global Whisper model"""
    global model
    model = load_whisper_model(size)

def validate_audio_file(file_path: str) -> Dict[str, Any]:
    """Validate audio file and return metadata"""
    config = load_config()
    audio_config = config.get('audio', {})
    supported_formats = audio_config.get('supported_formats', ['mp3', 'wav'])
    max_size_mb = audio_config.get('max_file_size_mb', 100)
    
    validation_result = {
        'valid': True,
        'errors': [],
        'warnings': [],
        'metadata': {}
    }
    
    # Check if file exists
    if not os.path.exists(file_path):
        validation_result['valid'] = False
        validation_result['errors'].append("File does not exist")
        return validation_result
    
    # Check file size
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    if file_size_mb > max_size_mb:
        validation_result['valid'] = False
        validation_result['errors'].append(f"File size ({file_size_mb:.1f}MB) exceeds maximum ({max_size_mb}MB)")
    
    # Check file extension
    file_extension = Path(file_path).suffix.lower().lstrip('.')
    if file_extension not in supported_formats:
        validation_result['valid'] = False
        validation_result['errors'].append(f"Unsupported format: {file_extension}. Supported: {', '.join(supported_formats)}")
    
    # Try to load audio file to check if it's valid
    try:
        AudioSegment = _get_audiosegment()
        if file_extension == 'mp3':
            audio = AudioSegment.from_mp3(file_path)
        elif file_extension == 'wav':
            audio = AudioSegment.from_wav(file_path)
        elif file_extension == 'm4a':
            audio = AudioSegment.from_file(file_path, format='m4a')
        elif file_extension == 'flac':
            audio = AudioSegment.from_file(file_path, format='flac')
        elif file_extension == 'aac':
            audio = AudioSegment.from_file(file_path, format='aac')
        elif file_extension == 'ogg':
            audio = AudioSegment.from_ogg(file_path)
        else:
            audio = AudioSegment.from_file(file_path)
        
        # Extract metadata
        duration_seconds = len(audio) / 1000
        validation_result['metadata'] = {
            'duration_seconds': duration_seconds,
            'duration_minutes': duration_seconds / 60,
            'sample_rate': audio.frame_rate,
            'channels': audio.channels,
            'sample_width': audio.sample_width,
            'file_size_mb': file_size_mb,
            'format': file_extension
        }
        
        # Only warn about very long files (over 1 hour)
        if duration_seconds > 3600:  # 1 hour
            validation_result['warnings'].append("File is very long (>1 hour), consider chunking for better performance")
        
        # Removed the low sample rate warning since we automatically fix it
        # The app upsamples to 16kHz automatically, so no need to warn users
            
    except Exception as e:
        validation_result['valid'] = False
        validation_result['errors'].append(f"Cannot read audio file: {str(e)}")
    
    return validation_result

def preprocess_audio(audio, config: Dict[str, Any]):
    """Preprocess audio for better transcription quality"""
    audio_config = config.get('audio', {})
    
    try:
        normalize, compress_dynamic_range = _get_pydub_effects()
        
        # Normalize audio levels
        if audio_config.get('normalize_audio', True):
            audio = normalize(audio)
        
        # Apply dynamic range compression
        if audio_config.get('noise_reduction', True):
            audio = compress_dynamic_range(audio)
        
        # Convert to mono if stereo (reduces processing time)
        if audio.channels > 1:
            audio = audio.set_channels(1)
        
        # Ensure consistent sample rate (16kHz is optimal for Whisper)
        # This automatically fixes low sample rate issues without warning
        target_sample_rate = 16000
        if audio.frame_rate != target_sample_rate:
            audio = audio.set_frame_rate(target_sample_rate)
        
        return audio
        
    except Exception as e:
        logger.warning(f"Audio preprocessing failed, using original: {e}")
        return audio

def convert_audio_format(file_path: str, target_format: str = 'wav') -> str:
    """Convert audio file to target format with preprocessing"""
    config = load_config()
    file_extension = Path(file_path).suffix.lower().lstrip('.')
    
    # NEW: Skip conversion for MP3 files when targeting WAV
    if file_extension == 'mp3' and target_format == 'wav':
        logger.info("Skipping MP3 to WAV conversion - processing MP3 directly")
        return file_path
    
        
    try:
        AudioSegment = _get_audiosegment()
        
        # Load audio file
        if file_extension == 'mp3':
            audio = AudioSegment.from_mp3(file_path)
        elif file_extension == 'wav':
            audio = AudioSegment.from_wav(file_path)
        elif file_extension == 'm4a':
            audio = AudioSegment.from_file(file_path, format='m4a')
        elif file_extension == 'flac':
            audio = AudioSegment.from_file(file_path, format='flac')
        elif file_extension == 'aac':
            audio = AudioSegment.from_file(file_path, format='aac')
        elif file_extension == 'ogg':
            audio = AudioSegment.from_ogg(file_path)
        else:
            audio = AudioSegment.from_file(file_path)
        
        # Preprocess audio (includes automatic upsampling to 16kHz)
        audio = preprocess_audio(audio, config)
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix=f'.{target_format}', delete=False) as tmp_file:
            if target_format == 'wav':
                audio.export(tmp_file.name, format='wav')
            elif target_format == 'mp3':
                audio.export(tmp_file.name, format='mp3')
            else:
                audio.export(tmp_file.name, format=target_format)
            
            return tmp_file.name
            
    except Exception as e:
        logger.error(f"Audio conversion failed: {e}")
        raise Exception(f"Failed to convert audio file: {str(e)}")

def chunk_audio(file_path: str, chunk_duration_minutes: int = 10) -> List[str]:
    """Split audio file into smaller chunks for processing"""
    try:
        AudioSegment = _get_audiosegment()
        audio = AudioSegment.from_file(file_path)
        chunk_duration_ms = chunk_duration_minutes * 60 * 1000
        
        chunks = []
        for i in range(0, len(audio), chunk_duration_ms):
            chunk = audio[i:i + chunk_duration_ms]
            
            # Create temporary file for chunk
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                chunk.export(tmp_file.name, format='wav')
                chunks.append(tmp_file.name)
        
        return chunks
        
    except Exception as e:
        logger.error(f"Audio chunking failed: {e}")
        return [file_path]  # Return original file if chunking fails

def transcribe_chunk(chunk_path: str, model_instance) -> Dict[str, Any]:
    """Transcribe a single audio chunk with enhanced error handling and thread safety"""
    try:
        # Validate chunk file exists and isn't empty
        if not os.path.exists(chunk_path):
            return {
                'success': False,
                'text': f'[ERROR] Chunk file not found: {chunk_path}',
                'language': 'unknown',
                'segments': []
            }
        
        # Check file size (empty files cause tensor errors)
        file_size = os.path.getsize(chunk_path)
        if file_size == 0:
            return {
                'success': False,
                'text': f'[ERROR] Chunk file is empty: {chunk_path}',
                'language': 'unknown',
                'segments': []
            }
        
        # NEW: Check if file is too small (less than 100KB often causes issues)
        if file_size < 100000:  # 100KB threshold
            logger.warning(f"Very small chunk file: {chunk_path} ({file_size} bytes)")
        
        # NEW: Additional audio validation using pydub
        try:
            AudioSegment = _get_audiosegment()
            test_audio = AudioSegment.from_file(chunk_path)
            duration_ms = len(test_audio)
            
            # Skip chunks shorter than 0.5 seconds (often cause tensor issues)
            if duration_ms < 500:
                return {
                    'success': False,
                    'text': f'[ERROR] Chunk too short ({duration_ms}ms): {chunk_path}',
                    'language': 'unknown',
                    'segments': []
                }
                
        except Exception as audio_error:
            return {
                'success': False,
                'text': f'[ERROR] Invalid audio chunk: {str(audio_error)}',
                'language': 'unknown',
                'segments': []
            }
        
        # Clear memory before transcription
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        # Use thread lock to prevent concurrent model access
        with model_lock:
            # Check model is available
            if model_instance is None:
                return {
                    'success': False,
                    'text': '[ERROR] Model not loaded',
                    'language': 'unknown', 
                    'segments': []
                }
            
            # NEW: Try transcription with multiple fallback strategies
            transcription_attempts = [
                # Attempt 1: Standard parameters
                {'fp16': False, 'verbose': False, 'language': None, 'task': 'transcribe'},
                # Attempt 2: Force English (sometimes helps with tensor issues)
                {'fp16': False, 'verbose': False, 'language': 'en', 'task': 'transcribe'},
                # Attempt 3: Minimal parameters
                {'fp16': False, 'verbose': False}
            ]
            
            last_error = None
            for attempt_num, params in enumerate(transcription_attempts, 1):
                try:
                    logger.info(f"Transcription attempt {attempt_num} for {chunk_path}")
                    result = model_instance.transcribe(chunk_path, **params)
                    
                    # Validate result
                    if result and 'text' in result:
                        text = result.get('text', '').strip()
                        if text:  # Non-empty transcription
                            return {
                                'success': True,
                                'text': text,
                                'language': result.get('language', 'unknown'),
                                'segments': result.get('segments', []),
                                'attempt': attempt_num
                            }
                        else:
                            logger.warning(f"Empty transcription on attempt {attempt_num}")
                    
                except Exception as attempt_error:
                    last_error = attempt_error
                    logger.warning(f"Attempt {attempt_num} failed: {str(attempt_error)}")
                    
                    # Clear cache between attempts
                    gc.collect()
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                    
                    # Wait briefly between attempts
                    import time
                    time.sleep(0.1)
            
            # All attempts failed
            return {
                'success': False,
                'text': f'[ERROR] All transcription attempts failed. Last error: {str(last_error)}',
                'language': 'unknown',
                'segments': [],
                'error_type': type(last_error).__name__ if last_error else 'Unknown'
            }
        
    except torch.cuda.OutOfMemoryError as e:
        logger.error(f"CUDA OOM error: {e}")
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        return {
            'success': False,
            'text': f'[ERROR] GPU memory error. Try using CPU or smaller chunks.',
            'language': 'unknown',
            'segments': []
        }
        
    except Exception as e:
        # Enhanced error reporting
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Chunk transcription error: {e}")
        logger.error(f"Full traceback: {error_details}")
        
        # NEW: Check for specific known errors
        error_msg = str(e)
        if "reshape tensor" in error_msg:
            return {
                'success': False,
                'text': f'[ERROR] Model tensor error (try smaller chunks or different model): {error_msg}',
                'language': 'unknown',
                'segments': []
            }
        elif "Linear(in_features=" in error_msg:
            return {
                'success': False,  
                'text': f'[ERROR] Model architecture error (try restarting app): {error_msg}',
                'language': 'unknown',
                'segments': []
            }
        else:
            return {
                'success': False,
                'text': f'[ERROR] Transcription failed: {str(e)}',
                'language': 'unknown',
                'segments': [],
                'error_type': type(e).__name__
            }
    except Exception as e:
        logger.error(f"Chunk transcription failed: {e}")
        return {
            'success': False,
            'text': f'[ERROR] Chunk transcription failed: {str(e)}',
            'language': 'unknown',
            'segments': []
        }

def transcribe_audio_parallel(file_path: str, max_workers: int = 4) -> Dict[str, Any]:
    """Transcribe audio using parallel processing with enhanced error handling"""
    config = load_config()
    chunk_duration = config.get('audio', {}).get('chunk_duration_minutes', 5)  # Reduced default
    
    # NEW: Force sequential processing for stability
    max_workers = min(max_workers, 4)  # Allow up to 4 workers
    
    # NEW: Check model health before starting
    global model
    if model is None:
        logger.error("Model not loaded before transcription")
        return {
            'success': False,
            'text': '[ERROR] Whisper model not loaded',
            'metadata': {},
            'warnings': []
        }    
    
    
    # Validate audio file
    validation = validate_audio_file(file_path)
    if not validation['valid']:
        return {
            'success': False,
            'text': f"[ERROR] Invalid audio file: {'; '.join(validation['errors'])}",
            'metadata': validation['metadata'],
            'warnings': validation['warnings']
        }
    
    metadata = validation['metadata']
    warnings = validation['warnings']
    
    # Determine if chunking is needed
    duration_minutes = metadata.get('duration_minutes', 0)
    needs_chunking = duration_minutes > chunk_duration
    
    try:
        # NEW: Check if this is an MP3 file we can process directly
        file_extension = Path(file_path).suffix.lower().lstrip('.')
    
        if file_extension == 'mp3':
            # Process MP3 directly - no conversion!
            logger.info("Processing MP3 file directly (no conversion)")
            processed_file = file_path
            is_temp_file = False
        else:
            # Convert non-MP3 files as before
            processed_file = convert_audio_format(file_path, 'wav')
            is_temp_file = processed_file != file_path
        
        if needs_chunking:
            # Split into chunks
            chunks = chunk_audio(processed_file, chunk_duration)
            
            # Transcribe chunks sequentially for stability
            transcripts = []
            all_segments = []
            failed_chunks = []
            consecutive_failures = 0

            logger.info(f"Processing {len(chunks)} chunks sequentially")
            for i, chunk in enumerate(chunks):
                chunk_id = f"{i+1}/{len(chunks)}"
    
                # Reset model if too many consecutive failures
                if consecutive_failures >= 2:
                    logger.warning("Too many failures, resetting model")
                    try:
                        reset_model()
                        consecutive_failures = 0
                    except Exception as reset_error:
                        logger.error(f"Model reset failed: {reset_error}")
    
                result = transcribe_chunk(chunk, model)
    
                if result['success']:
                    transcripts.append(result['text'])
                    all_segments.extend(result.get('segments', []))
                    consecutive_failures = 0  # Reset failure counter
                else:
                    transcripts.append(result['text'])  # Error message
                    failed_chunks.append(chunk_id)
                    consecutive_failures += 1
                    logger.warning(f"Chunk {chunk_id} failed, consecutive failures: {consecutive_failures}")
    
                # Clean up chunk file immediately
                try:
                    os.remove(chunk)
                except:
                    pass
            
            max_workers = min(max_workers, 4)  # Cap at 4 workers for stability
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_chunk = {
                    executor.submit(transcribe_chunk, chunk, model): chunk 
                    for chunk in chunks
                }
                
                for future in concurrent.futures.as_completed(future_to_chunk):
                    chunk_path = future_to_chunk[future]
                    try:
                        result = future.result()
                        if result['success']:
                            transcripts.append(result['text'])
                            all_segments.extend(result['segments'])
                        else:
                            transcripts.append(result['text'])  # Error message
                    except Exception as e:
                        transcripts.append(f'[ERROR] Chunk processing failed: {str(e)}')
                    finally:
                        # Clean up chunk file
                        if os.path.exists(chunk_path):
                            os.remove(chunk_path)
            
            # Combine transcripts
            full_transcript = ' '.join(transcripts)
            
        else:
            # Single file transcription
            result = model.transcribe(processed_file, fp16=False)
            full_transcript = result.get('text', '')
            all_segments = result.get('segments', [])
        
        # Clean up temporary files
        if is_temp_file and os.path.exists(processed_file):
            os.remove(processed_file)
        
        return {
            'success': True,
            'text': full_transcript,
            'metadata': metadata,
            'warnings': warnings,
            'segments': all_segments,
            'chunked': needs_chunking
        }
        
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        return {
            'success': False,
            'text': f'[ERROR] Transcription failed: {str(e)}',
            'metadata': metadata,
            'warnings': warnings
        }

def secure_file_handling(file_path: str, operation: str = 'read') -> str:
    """Handle files securely with encryption if enabled"""
    config = load_config()
    security_config = config.get('security', {})
    
    if not security_config.get('secure_temp_files', False):
        return file_path
    
    try:
        from analyser import init_encryption
        cipher_suite = init_encryption()
        
        if operation == 'encrypt':
            # Encrypt file content
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            encrypted_data = cipher_suite.encrypt(file_data)
            
            # Save encrypted file
            encrypted_path = f"{file_path}.encrypted"
            with open(encrypted_path, 'wb') as f:
                f.write(encrypted_data)
            
            # Remove original if auto-cleanup is enabled
            if security_config.get('auto_cleanup', True):
                os.remove(file_path)
            
            return encrypted_path
            
        elif operation == 'decrypt':
            # Decrypt file content
            with open(file_path, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = cipher_suite.decrypt(encrypted_data)
            
            # Save decrypted file
            decrypted_path = file_path.replace('.encrypted', '')
            with open(decrypted_path, 'wb') as f:
                f.write(decrypted_data)
            
            return decrypted_path
            
    except Exception as e:
        logger.warning(f"Secure file handling failed: {e}")
        return file_path

def cleanup_temp_files(file_paths: List[str]):
    """Clean up temporary files securely"""
    config = load_config()
    if not config.get('security', {}).get('auto_cleanup', True):
        return
    
    for file_path in file_paths:
        try:
            if os.path.exists(file_path):
                # Secure deletion: overwrite with random data before deletion
                with open(file_path, 'r+b') as f:
                    length = f.seek(0, 2)  # Seek to end to get file size
                    f.seek(0)
                    f.write(os.urandom(length))
                    f.flush()
                    os.fsync(f.fileno())  # Force write to disk
                
                os.remove(file_path)
                logger.info(f"Securely deleted temporary file: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to securely delete {file_path}: {e}")

def transcribe_audio(file_path: str) -> str:
    """Main transcription function """
    try:
        # Check if file exists and is not empty
        if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
            return "[ERROR] File is missing or empty."
        
        # Use parallel processing for large files
        result = transcribe_audio_parallel(file_path)
        
        if not result['success']:
            return result['text']  # Return error message
        
        # Apply PII redaction if enabled
        transcript = result['text']
        config = load_config()
        if config.get('security', {}).get('redact_pii', False):
            from analyser import redact_pii
            transcript = redact_pii(transcript)
        
        # Add metadata as comments if available
        metadata = result.get('metadata', {})
        if metadata:
            duration = metadata.get('duration_minutes', 0)
            if duration > 0:
                transcript += f"\n\n[Metadata: Duration: {duration:.1f} minutes"
                if result.get('chunked', False):
                    transcript += ", Processed in chunks"
                transcript += "]"
        
        # Add warnings if any
        warnings = result.get('warnings', [])
        if warnings:
            transcript += f"\n\n[Warnings: {'; '.join(warnings)}]"
        
        return transcript
        
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        return f"[ERROR] Transcription failed: {str(e)}"

# Keep the async function
async def transcribe_audio_async(file_path: str) -> str:
    """Async version of transcribe_audio for better performance"""
    loop = asyncio.get_event_loop()
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        result = await loop.run_in_executor(executor, transcribe_audio, file_path)
    
    return result
def transcribe_large_file_safely(file_path: str) -> str:
    """Handle large files with extra safety measures"""
    try:
        # Convert to optimal format first
        processed_file = convert_audio_format(file_path, 'wav')
        
        # Create smaller chunks (2 minutes each)
        chunks = chunk_audio(processed_file, 2)  # 2-minute chunks
        
        if not chunks:
            return "[ERROR] Failed to create audio chunks"
        
        logger.info(f"Processing {len(chunks)} chunks with fresh models")
        transcripts = []
        
        # Process each chunk with fresh model
        for i, chunk_path in enumerate(chunks):
            chunk_id = f"{i+1}/{len(chunks)}"
            logger.info(f"Processing chunk {chunk_id}")
            
            try:
                # Use fresh model for each chunk
                chunk_text = transcribe_with_fresh_model(chunk_path, "base")
                
                if not chunk_text.startswith("[ERROR]"):
                    transcripts.append(chunk_text)
                else:
                    logger.warning(f"Chunk {chunk_id} failed: {chunk_text}")
                    transcripts.append(f"[Chunk {chunk_id} failed]")
                    
            except Exception as chunk_error:
                logger.error(f"Chunk {chunk_id} error: {chunk_error}")
                transcripts.append(f"[Chunk {chunk_id} error: {str(chunk_error)}]")
            
            finally:
                # Clean up chunk file
                try:
                    os.remove(chunk_path)
                except:
                    pass
        
        # Clean up processed file
        if processed_file != file_path:
            try:
                os.remove(processed_file)
            except:
                pass
        
        # Combine results
        full_transcript = ' '.join(filter(lambda x: not x.startswith('[ERROR]') and not x.startswith('[Chunk'), transcripts))
        
        if not full_transcript.strip():
            return "[ERROR] No successful transcriptions from any chunks"
        
        return full_transcript
        
    except Exception as e:
        logger.error(f"Large file transcription failed: {e}")
        return f"[ERROR] Large file processing failed: {str(e)}"
        
def transcribe_ultra_simple(file_path: str) -> str:
    """Ultra-simple transcription with no fancy features"""
    try:
        import whisper
        import os
        
        # Check file exists
        if not os.path.exists(file_path):
            return "[ERROR] File not found"
        
        # Load model fresh every time
        print(f"Loading small model for {file_path}")
        model = whisper.load_model("small", device="cpu")
        
        # Basic transcription - no parameters
        print(f"Starting transcription...")
        result = model.transcribe(file_path)
        
        # Get text
        text = result.get("text", "").strip()
        
        # Clean up
        del model
        
        if not text:
            return "[ERROR] No text transcribed"
        
        return text
        
    except Exception as e:
        return f"[ERROR] Ultra-simple transcription failed: {str(e)}"