import logging

logger = logging.getLogger("WhisperService")

class WhisperService:
    def __init__(self):
        self._model = None
        self._initialized = False

    def initialize(self):
        try:
            import whisper
            self._model = whisper.load_model("base")
            self._initialized = True
            logger.info("✅ Whisper local model loaded successfully.")
        except Exception as e:
            logger.warning(f"⚠️ Whisper local not available ({e}). Running in fallback mode.")
            self._initialized = False

    def transcribe(self, audio_path: str) -> str:
        if not self._initialized:
            self.initialize()
        if self._model:
            try:
                res = self._model.transcribe(audio_path)
                return res.get("text", "")
            except Exception as e:
                logger.error(f"Error transcribing audio with Whisper: {e}")
                return ""
        return ""

whisper_service = WhisperService()
