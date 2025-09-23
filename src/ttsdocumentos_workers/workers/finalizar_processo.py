from aio_pika.abc import AbstractIncomingMessage
from ttsdocumentos_core.domiain.workers.finalize_text_dto import FinalizeTextDTO
from ttsdocumentos_core.log.log_maneger import LogLevels, LoggerManager, LoggerNames
from ttsdocumentos_core.rabbitmq.rabbitmq import RabbitMQConnection

logger = LoggerManager(nome=LoggerNames.WORKER, level=LogLevels.DEBUG)

async def processar_finalizar_processo(message: AbstractIncomingMessage):
    payload = FinalizeTextDTO.from_json(message.body.decode())
    logger.info(f"Finalizando processo do documento ID: {payload.path_audio}")

async def processar_finalizar_processo_wrapper(message: AbstractIncomingMessage, connection: RabbitMQConnection):
    await processar_finalizar_processo(message)