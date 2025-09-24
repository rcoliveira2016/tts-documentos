import os
from pathlib import Path
import tempfile
import wave
from aio_pika.abc import AbstractIncomingMessage
from ttsdocumentos_core.azure_blob import AzureBlobUtils
from ttsdocumentos_core.domiain.workers.finalize_text_dto import FinalizeTextDTO
from ttsdocumentos_core.domiain.workers.transcribe_text_dto import TranscribeTextDTO
from ttsdocumentos_core.log.log_maneger import LogLevels, LoggerManager, LoggerNames
from ttsdocumentos_core.rabbitmq.rabbitmq import RabbitMQConnection, RabbitMQProducer
from ttsdocumentos_core.services.tts_service import tts_service
from ttsdocumentos_core.config import settings

azure_blob_utils = AzureBlobUtils()
logger = LoggerManager(nome=LoggerNames.WORKER, level=LogLevels.DEBUG)

async def processar_transcrever_texto(message: AbstractIncomingMessage):
    payload = TranscribeTextDTO.from_json(message.body.decode())
    logger.info(f"Transcrevendo texto do documento: {payload.name_file}")

    logger.info(f"Tamanho do conteúdo: {len(payload.conteudo)}")

    with tempfile.NamedTemporaryFile(suffix=Path(payload.name_file).suffix, delete=False) as temp_file:
        temp_path = temp_file.name 

    try:
        # Abre com wave para escrita
        with wave.open(temp_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(24000)

            async for chunk in tts_service.audio_generator(payload.conteudo, voice="pm_santa", chunk_size=2048):
                wf.writeframes(chunk)

        # Faz upload
        nome_arquivo_blob = f"{payload.document_id}.wav"
        azure_blob_utils.upload_file(temp_path, nome_arquivo_blob)
        logger.info(f"upload concluido {nome_arquivo_blob}")

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    return FinalizeTextDTO(
        path_audio=str(nome_arquivo_blob),
        name_file=payload.name_file,
    )


async def processar_transcrever_texto_wrapper(msg, connection: RabbitMQConnection):
    result = await processar_transcrever_texto(msg)

    producer = RabbitMQProducer(connection)
    await producer.setup_exchange()
    await producer.bind_queue(FinalizeTextDTO.QUEUE_NAME, f"{FinalizeTextDTO.QUEUE_NAME}_routing_key")
    await producer.publishJson(result.to_dict(), routing_key=f"{FinalizeTextDTO.QUEUE_NAME}_routing_key")
