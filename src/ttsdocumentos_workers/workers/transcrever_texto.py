from pathlib import Path
import wave
from aio_pika.abc import AbstractIncomingMessage
from ttsdocumentos_core.domiain.workers.finalize_text_dto import FinalizeTextDTO
from ttsdocumentos_core.domiain.workers.transcribe_text_dto import TranscribeTextDTO
from ttsdocumentos_core.log.log_maneger import LogLevels, LoggerManager, LoggerNames
from ttsdocumentos_core.rabbitmq.rabbitmq import RabbitMQConnection, RabbitMQProducer
from ttsdocumentos_core.services.tts_service import tts_service
from ttsdocumentos_core.config import settings

logger = LoggerManager(nome=LoggerNames.WORKER, level=LogLevels.DEBUG)

async def processar_transcrever_texto(message: AbstractIncomingMessage):
    payload = TranscribeTextDTO.from_json(message.body.decode())
    logger.info(f"Transcrevendo texto do documento: {payload.name_file}")

    arquivo = Path(f"{settings.file_temp_audio}/{payload.name_file}.wav")
    arquivo.parent.mkdir(parents=True, exist_ok=True)
    arquivo.exists() and arquivo.unlink()

    logger.info(f"Tamanho do conteúdo: {len(payload.conteudo)}")

    with wave.open(str(arquivo), "wb") as wf:
        wf.setnchannels(1)         # mono
        wf.setsampwidth(2)         # int16 = 2 bytes
        wf.setframerate(24000)     # taxa do TTS

        # Converte float32 para int16 e escreve cada chunk
        async for chunk in tts_service.audio_generator(payload.conteudo, voice="pm_santa", chunk_size=2048):
            wf.writeframes(chunk)

    return FinalizeTextDTO(
        path_audio=str(arquivo),
        name_file=payload.name_file,
    )


async def processar_transcrever_texto_wrapper(msg, connection: RabbitMQConnection):
    result = await processar_transcrever_texto(msg)

    producer = RabbitMQProducer(connection)
    await producer.setup_exchange()
    await producer.bind_queue(FinalizeTextDTO.QUEUE_NAME, f"{FinalizeTextDTO.QUEUE_NAME}_routing_key")
    await producer.publishJson(result.to_dict(), routing_key=f"{FinalizeTextDTO.QUEUE_NAME}_routing_key")
