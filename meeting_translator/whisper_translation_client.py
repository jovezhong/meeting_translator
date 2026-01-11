"""
Whisper ASR + Separate Translation Client

This client uses a two-stage approach for better accuracy:
1. OpenAI Whisper API for Speech-to-Text (ASR)
2. Separate LLM API for Text Translation

This approach provides better accuracy than end-to-end realtime API
because:
- Whisper processes longer audio segments with full context
- Translation model receives complete sentences to translate
- No hallucination from empty/partial audio buffers

Architecture:
    Audio Stream → Buffer → Whisper ASR → English Text → GPT Translation → Chinese Text
                           (offline)                      (streaming)
"""

import os
import time
import base64
import asyncio
import json
import threading
import queue
from typing import Dict, Optional, Callable
from datetime import datetime

import numpy as np
try:
    import pyaudiowpatch as pyaudio
except ImportError:
    import pyaudio

# Import base class
from translation_client_base import BaseTranslationClient, TranslationProvider
from output_manager import Out

# OpenAI client for Whisper and GPT APIs
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    # Warning will be shown when client is instantiated, not at import time


class WhisperTranslationClient(BaseTranslationClient):
    """
    Two-stage translation client using Whisper ASR + GPT Translation

    Stage 1: Whisper API (speech-to-text)
        - Accumulates audio for ~5-10 seconds
        - Sends to Whisper API for transcription
        - Returns English text

    Stage 2: GPT API (text translation)
        - Takes English text from Whisper
        - Translates to target language (Chinese)
        - Can use streaming for faster response

    Configuration (via .env):
        - OPENAI_API_KEY: API key for both Whisper and GPT
        - WHISPER_MODEL: whisper-1 (default)
        - TRANSLATION_MODEL: gpt-4o-mini or gpt-4o (default: gpt-4o-mini)
        - WHISPER_BUFFER_SECONDS: Audio buffer duration
    """

    provider = TranslationProvider.WHISPER

    # Whisper API expects 16kHz audio
    AUDIO_RATE = 16000

    def __init__(
        self,
        api_key: str,
        source_language: str = "en",
        target_language: str = "zh",
        whisper_model: str = "whisper-1",
        translation_model: str = "gpt-4o-mini",
        buffer_seconds: float = 8.0,
        audio_enabled: bool = False,  # Text-only output for this client
        **kwargs
    ):
        """
        Initialize Whisper + Translation client

        Args:
            api_key: OpenAI API key
            source_language: Source language code (default: en)
            target_language: Target language code (default: zh)
            whisper_model: Whisper model to use (default: whisper-1)
            translation_model: GPT model for translation (default: gpt-4o-mini)
            buffer_seconds: Seconds of audio to buffer before ASR
            audio_enabled: Whether to output audio (not supported yet)
        """
        super().__init__(
            api_key=api_key,
            source_language=source_language,
            target_language=target_language,
            audio_enabled=False,  # Force text-only for now
            **kwargs
        )

        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI package required. Install with: pip install openai")

        self.whisper_model = whisper_model
        self.translation_model = translation_model
        self.buffer_seconds = buffer_seconds

        # Initialize OpenAI client
        self.client = OpenAI(api_key=api_key)

        # Audio buffer for Whisper
        self.audio_buffer = bytearray()
        self.buffer_lock = threading.Lock()
        self._buffer_start_time = None

        # Processing state
        self.is_connected = False
        self.is_processing = False
        self._process_thread = None
        self._stop_event = threading.Event()

        # Callbacks
        self._on_transcription = None  # Called with English ASR result
        self._on_translation = None    # Called with Chinese translation

        # Context tracking for better translation continuity
        self._previous_transcription = ""  # Previous English text for context
        self._previous_translation = ""    # Previous translated text

        # Language names for prompts
        self.lang_names = {
            "en": "English",
            "zh": "Chinese",
            "ja": "Japanese",
            "ko": "Korean",
            "fr": "French",
            "de": "German",
            "es": "Spanish"
        }

        Out.status(f"WhisperTranslationClient initialized")
        Out.status(f"  ASR: {whisper_model}, Translation: {translation_model}")
        Out.status(f"  Buffer: {buffer_seconds}s, {source_language} → {target_language}")

    @property
    def input_rate(self) -> int:
        return self.AUDIO_RATE

    @property
    def output_rate(self) -> int:
        # Not used for text-only output
        return self.AUDIO_RATE

    async def configure_session(self):
        """Configure session - no-op for Whisper client"""
        pass  # No session configuration needed

    @classmethod
    def get_supported_voices(cls) -> dict:
        """Return supported voices - not applicable for text-only client"""
        return {}  # No TTS voices for this client

    @staticmethod
    def check_dependencies() -> tuple:
        """
        检查 Whisper 依赖是否已安装

        Returns:
            (is_available, error_message)
            - is_available: True 如果所有依赖都满足
            - error_message: 依赖缺失时的错误消息
        """
        if not OPENAI_AVAILABLE:
            return False, "Whisper 客户端需要 OpenAI 依赖包。请运行: pip install openai"

        return True, ""

    async def connect(self):
        """Start the processing pipeline"""
        self.is_connected = True
        self._stop_event.clear()

        # Start background processing thread
        self._process_thread = threading.Thread(
            target=self._processing_loop,
            daemon=True
        )
        self._process_thread.start()

        Out.status("Whisper translation client started")

    async def close(self):
        """Stop the processing pipeline"""
        self.is_connected = False
        self._stop_event.set()

        if self._process_thread and self._process_thread.is_alive():
            self._process_thread.join(timeout=2.0)

        Out.status("Whisper translation client stopped")

    async def send_audio_chunk(self, audio_data: bytes):
        """
        Receive audio data and buffer it for Whisper

        Args:
            audio_data: PCM16 audio bytes at 16kHz
        """
        if not self.is_connected:
            return

        with self.buffer_lock:
            if self._buffer_start_time is None:
                self._buffer_start_time = time.time()

            self.audio_buffer.extend(audio_data)

    def _processing_loop(self):
        """Background thread that processes buffered audio"""
        while not self._stop_event.is_set():
            try:
                # Check if we have enough audio
                buffer_duration = self._get_buffer_duration()

                # Process if buffer reached target duration AND minimum duration (1s)
                # This prevents processing silence or very short audio artifacts
                if buffer_duration >= self.buffer_seconds and buffer_duration > 1.0:
                    self._process_buffer()

                # Small sleep to prevent busy loop
                time.sleep(0.1)

            except Exception as e:
                Out.error(f"Processing error: {e}")
                import traceback
                traceback.print_exc()

    def _get_buffer_duration(self) -> float:
        """Get current buffer duration in seconds"""
        with self.buffer_lock:
            # PCM16 = 2 bytes per sample
            samples = len(self.audio_buffer) // 2
            return samples / self.AUDIO_RATE

    def _process_buffer(self):
        """Process the buffered audio through Whisper and translation"""
        # Get and clear buffer
        with self.buffer_lock:
            if len(self.audio_buffer) == 0:
                return

            audio_data = bytes(self.audio_buffer)
            self.audio_buffer.clear()
            self._buffer_start_time = None

        self.is_processing = True

        try:
            # Stage 1: Whisper ASR
            english_text = self._transcribe_audio(audio_data)

            if english_text and english_text.strip():
                # Filter out very short transcriptions (likely artifacts or filler words)
                word_count = len(english_text.strip().split())
                if word_count < 3:
                    Out.debug(f"Skipping short phrase ({word_count} words): {english_text}")
                    return

                Out.status(f"[ASR] {english_text}")
                # 将英文识别结果也作为源文本输出到字幕（增量展示体验）
                self.output_subtitle(
                    target_text=english_text,
                    source_text="",
                    is_final=False,
                    extra_metadata={"provider": "whisper", "mode": "S2T"}
                )

                # Notify transcription callback
                if self._on_transcription:
                    self._on_transcription(english_text)

                # Stage 2: Translate to target language (with previous context)
                chinese_text = self._translate_text(english_text, self._previous_transcription)

                if chinese_text and chinese_text.strip():
                    Out.status(f"[翻译] {chinese_text}")

                    # 输出最终字幕，带上源文本，供字幕窗口和控制台使用
                    self.output_subtitle(
                        target_text=chinese_text,
                        source_text=english_text,
                        is_final=True,
                        extra_metadata={"provider": "whisper", "mode": "S2T"}
                    )

                    # Notify translation callback
                    if self._on_translation:
                        self._on_translation(english_text, chinese_text)

                    # Update context for next translation
                    self._previous_transcription = english_text
                    self._previous_translation = chinese_text

        except Exception as e:
            Out.error(f"Processing failed: {e}")
            import traceback
            traceback.print_exc()

        finally:
            self.is_processing = False

    def _transcribe_audio(self, audio_data: bytes) -> str:
        """
        Transcribe audio using Whisper API

        Args:
            audio_data: PCM16 audio bytes

        Returns:
            Transcribed text in source language
        """
        try:
            # Convert PCM16 to WAV format for Whisper API
            import io
            import wave

            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(self.AUDIO_RATE)
                wav_file.writeframes(audio_data)

            wav_buffer.seek(0)
            wav_buffer.name = "audio.wav"  # Whisper API needs a filename

            # Call Whisper API
            response = self.client.audio.transcriptions.create(
                model=self.whisper_model,
                file=wav_buffer,
                language=self.source_language,  # Hint for better accuracy
                response_format="text"
            )

            return response.strip() if response else ""

        except Exception as e:
            Out.error(f"Whisper transcription failed: {e}")
            return ""

    def _translate_text(self, text: str, previous_context: str = "") -> str:
        """
        Translate text using GPT API

        Args:
            text: Source language text
            previous_context: Previous transcription for context continuity

        Returns:
            Translated text in target language
        """
        try:
            source_lang = self.lang_names.get(self.source_language, self.source_language)
            target_lang = self.lang_names.get(self.target_language, self.target_language)

            # Build context-aware system prompt
            system_content = f"""You are a professional translator. Translate the following {source_lang} text to {target_lang}.

Rules:
- Output ONLY the translation, nothing else
- Preserve technical terms and proper nouns
- Maintain natural, fluent {target_lang}
- Do not add explanations or notes"""

            # Add previous context if available
            if previous_context:
                system_content += f"""

Previous context for continuity:
"{previous_context}"

Use this context to improve translation accuracy and handle sentence fragments."""

            response = self.client.chat.completions.create(
                model=self.translation_model,
                messages=[
                    {
                        "role": "system",
                        "content": system_content
                    },
                    {
                        "role": "user",
                        "content": text
                    }
                ],
                temperature=0.3,
                max_tokens=1000
            )

            return response.choices[0].message.content.strip() if response.choices[0].message.content else ""

        except Exception as e:
            Out.error(f"Translation failed: {e}")
            return ""

    async def handle_server_messages(self, on_text_received: Optional[Callable] = None):
        """
        Handle translation results

        This method is called by the translation service to receive results.
        For Whisper client, we use callbacks instead of WebSocket messages.
        """
        # Set up callbacks to forward to on_text_received
        def on_transcription(english_text: str):
            if on_text_received:
                on_text_received(f"[源] {english_text}")

        def on_translation(english_text: str, chinese_text: str):
            if on_text_received:
                on_text_received(f"[译] {chinese_text}")

        self._on_transcription = on_transcription
        self._on_translation = on_translation

        # Keep running while connected
        while self.is_connected:
            await asyncio.sleep(0.1)

    def force_process(self):
        """Force processing of current buffer (useful for end of speech)"""
        if self._get_buffer_duration() > 0.5:  # At least 0.5 seconds
            self._process_buffer()


# Factory function for easy instantiation
def create_whisper_client(
    api_key: Optional[str] = None,
    source_language: str = "en",
    target_language: str = "zh",
    **kwargs
) -> WhisperTranslationClient:
    """
    Create a WhisperTranslationClient with default settings

    Args:
        api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
        source_language: Source language code
        target_language: Target language code
        **kwargs: Additional arguments passed to constructor

    Returns:
        Configured WhisperTranslationClient instance
    """
    if api_key is None:
        api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ValueError("OPENAI_API_KEY not provided and not found in environment")

    # Build kwargs for WhisperTranslationClient
    client_kwargs = {
        "api_key": api_key,
        "source_language": source_language,
        "target_language": target_language,
        "whisper_model": os.getenv("WHISPER_MODEL", "whisper-1"),
        "translation_model": os.getenv("TRANSLATION_MODEL", "gpt-4o-mini"),
        **kwargs
    }

    # Only pass buffer_seconds if explicitly set in env, otherwise use constructor default
    buffer_env = os.getenv("WHISPER_BUFFER_SECONDS")
    if buffer_env is not None:
        client_kwargs["buffer_seconds"] = float(buffer_env)

    return WhisperTranslationClient(**client_kwargs)
