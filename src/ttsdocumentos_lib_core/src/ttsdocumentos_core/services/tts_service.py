import logging
import numpy as np
from ttsdocumentos_core.log.log_maneger import LoggerManager, LoggerNames
from ttsdocumentos_core.process.kokoro_tts import KokoroTTSSimple, ttsInstancia
from ttsdocumentos_core.process.text_process import split_text
from ttsdocumentos_core.common.audio_helper import stream_audio_chunks_to_wav

logger = LoggerManager(nome=LoggerNames.API, level=logging.DEBUG)

class TTSService:
    def __init__(self, tts_instance: KokoroTTSSimple):
        self.tts_process = tts_instance

    
    async def _build_stream(self, text: str, voice: str = "pf_dora"):
        tts = self.tts_process
        if not tts.initialize():
            logger.error("Falha na inicialização do TTS")
            raise Exception("Falha na inicialização do TTS")
        
        silence = np.zeros(int(0.4 * 24000), dtype=np.float32)  # 0.4s silêncio

        for text_chunk in split_text(text):
            logger.debug(f"Processando chunk: {text_chunk[:30]}... (len={len(text_chunk)})")
            if text_chunk.strip() == "":
                yield silence
            else:
                async for audio_chunk in tts.get_bytes(text_chunk, voice_id=voice):
                    yield audio_chunk

    async def audio_generator(self, text: str, voice: str):
        stream_tts = self._build_stream(text, voice)
        async for audio_chunk in stream_audio_chunks_to_wav(stream_tts):
            yield audio_chunk

tts_service = TTSService(ttsInstancia)