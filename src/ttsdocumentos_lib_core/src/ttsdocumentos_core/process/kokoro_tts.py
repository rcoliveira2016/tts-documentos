import io
import os
import logging
import kokoro_onnx
import soundfile as sf
from pathlib import Path
import requests
from ttsdocumentos_core.config import settings
from ttsdocumentos_core.log.log_maneger import LoggerManager, LoggerNames

logger = LoggerManager(nome=LoggerNames.API, level=logging.DEBUG)

class KokoroTTSSimple:
    def __init__(self, models_dir="./models"):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(exist_ok=True)
        
        if logger:
            self.logger = logger
        else:
            self.logger = logging.getLogger(__name__)
            if not self.logger.handlers:
                handler = logging.StreamHandler()
                formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
                handler.setFormatter(formatter)
                self.logger.addHandler(handler)
                self.logger.setLevel(logging.INFO)
        
        self.model_path = self.models_dir / "kokoro-v1.0.onnx"
        self.voices_path = self.models_dir / "voices-v1.0.bin"
        
        self.tts = None
        
        self.info(f"KokoroTTS inicializado com diretório de modelos: {self.models_dir}")
    
    def debug(self, msg: str): 
        self.logger.debug(msg)
    
    def info(self, msg: str): 
        self.logger.info(msg)
    
    def warning(self, msg: str): 
        self.logger.warning(msg)
    
    def error(self, msg: str): 
        self.logger.error(msg)
    
    def critical(self, msg: str): 
        self.logger.critical(msg)
        
    def download_models(self):
        files_to_download = [
            (settings.kokoro_url_onnx, self.model_path),
            (settings.kokoro_url_bin, self.voices_path)
        ]
        
        for url, local_path in files_to_download:
            if not local_path.exists():
                self.info(f"Iniciando download de {local_path.name}...")

                try:
                    response = requests.get(url, stream=True)
                    response.raise_for_status()
                    
                    with open(local_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    self.info(f"Download concluído com sucesso: {local_path}")
                    
                except Exception as e:
                    self.error(f"Falha no download de {local_path}: {str(e)}")
                    return False
            else:
                self.debug(f"Arquivo já existe: {local_path}")
        
        return True
    
    def initialize(self):
        if not self.model_path.exists() or not self.voices_path.exists():
            self.info("Modelos não encontrados. Iniciando download...")
            if not self.download_models():
                self.error("Falha ao baixar os modelos necessários")
                return False
        
        if self.tts:
            return True

        try:
            self.tts = kokoro_onnx.Kokoro(
                str(self.model_path), 
                str(self.voices_path)
            )
            self.info("Kokoro TTS inicializado com sucesso")
            return True
            
        except Exception as e:
            self.error(f"Erro ao inicializar Kokoro TTS: {str(e)}")
            return False

    async def get_bytes(self, text, voice_id="pm_santa", speed=1.0):
        if not self.tts:
            self.error("TTS não inicializado. Execute initialize() primeiro")
            raise Exception("TTS não inicializado")

        try:
            samples_generator = self.tts.create_stream(text=text, voice=voice_id, speed=speed, lang="pt-br",)
            async for chunk, rate in samples_generator:
                yield chunk

        except Exception as e:
            self.error(f"Erro ao gerar bytes de áudio: {str(e)}")

ttsInstancia = KokoroTTSSimple()