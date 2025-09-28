import asyncio
import logging
from typing import Optional, Tuple
import webrtcvad
import numpy as np

logger = logging.getLogger(__name__)

class RealTimeVADStreamer:
    """
    Real-time Voice Activity Detection (VAD) streamer for detecting End-of-Turn (EoT).
    
    This class processes incoming audio chunks, detects speech activity, and determines
    when a user has finished speaking (End-of-Turn) based on silence detection.
    """
    
    def __init__(self, aggressiveness: int = 3, sample_rate: int = 16000, frame_duration: int = 30):
        """
        Initialize the VAD streamer.
        
        Args:
            aggressiveness: VAD aggressiveness level (0-3, 3 is most aggressive)
            sample_rate: Audio sample rate in Hz (16000 recommended)
            frame_duration: Frame duration in milliseconds (30ms recommended)
        """
        self.sample_rate = sample_rate
        self.frame_duration = frame_duration
        self.frame_size = int(sample_rate * frame_duration / 1000)  # samples per frame
        
        # Initialize VAD
        self.vad = webrtcvad.Vad(aggressiveness)
        
        # Audio buffer for accumulating speech
        self.audio_buffer = bytearray()
        
        # VAD state tracking
        self.silence_frames = 0
        self.speech_frames = 0
        self.in_speech = False
        self.eot_silence_threshold = 1.5  # seconds of silence for EoT
        self.eot_frames_threshold = int(self.eot_silence_threshold * 1000 / frame_duration)
        
        logger.info(f"VAD Streamer initialized: {sample_rate}Hz, {frame_duration}ms frames, "
                   f"EoT threshold: {self.eot_silence_threshold}s ({self.eot_frames_threshold} frames)")
    
    def process_chunk(self, chunk_data: bytes) -> Optional[bytes]:
        """
        Process an incoming audio chunk and detect End-of-Turn.
        
        Args:
            chunk_data: Raw audio bytes (16kHz, 16-bit, mono PCM)
            
        Returns:
            Complete audio buffer when EoT is detected, None otherwise
        """
        try:
            # Add chunk to buffer
            self.audio_buffer.extend(chunk_data)
            
            # Process complete frames
            complete_frames = len(self.audio_buffer) // (self.frame_size * 2)  # 2 bytes per sample (16-bit)
            
            for i in range(complete_frames):
                # Extract frame
                start_idx = i * self.frame_size * 2
                end_idx = start_idx + self.frame_size * 2
                frame_bytes = bytes(self.audio_buffer[start_idx:end_idx])
                
                # Check if frame is valid for VAD (must be exactly the right size)
                if len(frame_bytes) != self.frame_size * 2:
                    continue
                
                # Classify frame as speech or silence
                is_speech = self.vad.is_speech(frame_bytes, self.sample_rate)
                
                if is_speech:
                    self.speech_frames += 1
                    self.silence_frames = 0
                    self.in_speech = True
                    logger.debug(f"Speech detected (frame {self.speech_frames})")
                else:
                    self.silence_frames += 1
                    logger.debug(f"Silence detected (frame {self.silence_frames})")
                
                # Check for End-of-Turn
                if self.in_speech and self.silence_frames >= self.eot_frames_threshold:
                    logger.info(f"EoT detected: {self.silence_frames} silence frames after {self.speech_frames} speech frames")
                    
                    # Return complete audio buffer and reset
                    complete_audio = bytes(self.audio_buffer)
                    self._reset_state()
                    return complete_audio
            
            # Remove processed frames from buffer
            processed_bytes = complete_frames * self.frame_size * 2
            self.audio_buffer = self.audio_buffer[processed_bytes:]
            
            return None
            
        except Exception as e:
            logger.error(f"Error processing audio chunk: {e}")
            return None
    
    def _reset_state(self):
        """Reset the VAD state for the next utterance."""
        self.audio_buffer = bytearray()
        self.silence_frames = 0
        self.speech_frames = 0
        self.in_speech = False
        logger.debug("VAD state reset for next utterance")
    
    def get_state(self) -> dict:
        """Get current VAD state for monitoring."""
        return {
            "buffer_size": len(self.audio_buffer),
            "silence_frames": self.silence_frames,
            "speech_frames": self.speech_frames,
            "in_speech": self.in_speech,
            "eot_threshold": self.eot_frames_threshold
        }
    
    def force_eot(self) -> Optional[bytes]:
        """
        Force End-of-Turn detection, returning current buffer if speech was detected.
        
        Returns:
            Complete audio buffer if speech was detected, None otherwise
        """
        if self.in_speech and len(self.audio_buffer) > 0:
            logger.info("Forcing EoT detection")
            complete_audio = bytes(self.audio_buffer)
            self._reset_state()
            return complete_audio
        else:
            logger.debug("No speech detected, nothing to return")
            self._reset_state()
            return None