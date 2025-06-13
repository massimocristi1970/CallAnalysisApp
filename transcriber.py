import os
import streamlit as st
from pydub import AudioSegment
from pydub.effects import normalize, compress_dynamic_range
import tempfile
import asyncio
import concurrent.futures
from typing import List, Dict, Any, Optional
import hashlib
import yaml
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

model = None  # Will hold the Whisper model after it's set

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

def preprocess_audio(audio: AudioSegment, config: Dict[str, Any]) -> AudioSegment:
    """Preprocess audio for better transcription quality"""
    audio_config = config.get('audio', {})
    
    try:
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
    
    # If already in target format, check if preprocessing is needed
    if file_extension == target_format and not any([
        config.get('audio', {}).get('normalize_audio', True),
        config.get('audio', {}).get('noise_reduction', True)
    ]):
        return file_path
    
    try:
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
    """Transcribe a single audio chunk"""
    try:
        result = model_instance.transcribe(chunk_path, fp16=False)
        return {
            'success': True,
            'text': result.get('text', ''),
            'language': result.get('language', 'unknown'),
            'segments': result.get('segments', [])
        }
    except Exception as e:
        logger.error(f"Chunk transcription failed: {e}")
        return {
            'success': False,
            'text': f'[ERROR] Chunk transcription failed: {str(e)}',
            'language': 'unknown',
            'segments': []
        }

def transcribe_audio_parallel(file_path: str, max_workers: int = 2) -> Dict[str, Any]:
    """Transcribe audio using parallel processing for large files"""
    config = load_config()
    chunk_duration = config.get('audio', {}).get('chunk_duration_minutes', 10)
    
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
        # Convert audio to optimal format (includes automatic upsampling)
        processed_file = convert_audio_format(file_path, 'wav')
        is_temp_file = processed_file != file_path
        
        if needs_chunking:
            # Split into chunks
            chunks = chunk_audio(processed_file, chunk_duration)
            
            # Transcribe chunks in parallel
            transcripts = []
            all_segments = []
            
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
    """Main transcription function with enhanced error handling and security"""
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
        
        # Add warnings if any (but not sample rate warnings)
        warnings = result.get('warnings', [])
        if warnings:
            transcript += f"\n\n[Warnings: {'; '.join(warnings)}]"
        
        return transcript
        
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        return f"[ERROR] Transcription failed: {str(e)}"

# Async version for future use
async def transcribe_audio_async(file_path: str) -> str:
    """Async version of transcribe_audio for better performance"""
    loop = asyncio.get_event_loop()
    
    # Run transcription in thread pool to avoid blocking
    with concurrent.futures.ThreadPoolExecutor() as executor:
        result = await loop.run_in_executor(executor, transcribe_audio, file_path)
    
    return result
