import logging
import io
import numpy as np
from typing import Optional
from faster_whisper import WhisperModel

logger = logging.getLogger(__name__)

class ASRService:
    """
    Automatic Speech Recognition (ASR) service using Faster-Whisper.
    
    This service provides fast, local transcription of audio using the Whisper model.
    Optimized for cost control by running locally instead of using expensive API services.
    """
    
    def __init__(self, model_size: str = "tiny.en", device: str = "cpu"):
        """
        Initialize the ASR service with a Whisper model.
        
        Args:
            model_size: Whisper model size ("tiny.en", "base.en", "small.en", "medium.en", "large")
            device: Device to run on ("cpu", "cuda", "auto")
        """
        self.model_size = model_size
        self.device = device
        self.model = None
        self._initialize_model()
        
    def _initialize_model(self):
        """Initialize the Whisper model lazily."""
        # Don't initialize the model during __init__ to avoid blocking startup
        # The model will be loaded on first use
        self.model = None
        logger.info(f"ASR service ready, model will be loaded on first use: {self.model_size}")
    
    def transcribe_utterance(self, audio_bytes: bytes) -> Optional[str]:
        """
        Transcribe raw audio bytes to text.
        
        Args:
            audio_bytes: Raw audio bytes (16kHz, 16-bit, mono PCM)
            
        Returns:
            Transcribed text string, or None if transcription fails
        """
        try:
            # Load model on first use if not already loaded
            if not self.model:
                logger.info(f"Loading Whisper model: {self.model_size} on {self.device}")
                try:
                    self.model = WhisperModel(
                        self.model_size, 
                        device=self.device,
                        compute_type="int8"  # Use int8 for faster inference on CPU
                    )
                    logger.info("Whisper model loaded successfully")
                except Exception as e:
                    logger.error(f"Failed to load Whisper model: {e}")
                    return None
            
            if not audio_bytes:
                logger.warning("Empty audio data provided")
                return None
            
            logger.info(f"Transcribing audio: {len(audio_bytes)} bytes")
            
            # Convert bytes to numpy array for Whisper
            audio_array = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
            
            # Transcribe using Whisper
            segments, info = self.model.transcribe(
                audio_array,
                beam_size=1,  # Faster inference
                language="en",  # English only for .en models
                task="transcribe",
                vad_filter=True,  # Use VAD filtering for better results
                vad_parameters=dict(min_silence_duration_ms=500)
            )
            
            # Extract text from segments
            transcript_parts = []
            for segment in segments:
                transcript_parts.append(segment.text.strip())
            
            # Combine all segments into final transcript
            final_transcript = " ".join(transcript_parts).strip()
            
            if final_transcript:
                logger.info(f"Transcription successful: '{final_transcript}'")
                return final_transcript
            else:
                logger.warning("No speech detected in audio")
                return None
                
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return None
    
    def is_ready(self) -> bool:
        """Check if the ASR service is ready to process audio."""
        # Service is always ready, model will be loaded on first use
        return True

# Global ASR service instance
_asr_service = None

def get_asr_service() -> ASRService:
    """Get the global ASR service instance."""
    global _asr_service
    if _asr_service is None:
        _asr_service = ASRService()
    return _asr_service

def transcribe_utterance(audio_bytes: bytes) -> Optional[str]:
    """
    Convenience function to transcribe audio bytes using the global ASR service.
    
    Args:
        audio_bytes: Raw audio bytes (16kHz, 16-bit, mono PCM)
        
    Returns:
        Transcribed text string, or None if transcription fails
    """
    asr_service = get_asr_service()
    return asr_service.transcribe_utterance(audio_bytes)