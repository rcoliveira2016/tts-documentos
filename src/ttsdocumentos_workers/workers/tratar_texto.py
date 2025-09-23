from aio_pika.abc import AbstractIncomingMessage
from ttsdocumentos_core.domiain.workers.transcribe_text_dto import TranscribeTextDTO
from ttsdocumentos_core.domiain.workers.treat_text_dto import TreatTextDTO
from ttsdocumentos_core.log.log_maneger import LogLevels, LoggerManager, LoggerNames
from ttsdocumentos_core.rabbitmq.rabbitmq import RabbitMQConnection, RabbitMQProducer

logger = LoggerManager(nome=LoggerNames.WORKER, level=LogLevels.DEBUG)

async def processar_tratar_texto(message: AbstractIncomingMessage):
    payload = TreatTextDTO.from_json(message.body.decode())
    logger.info(f"Tratando texto do documento")
    return TranscribeTextDTO(
        conteudo=payload.conteudo,
        name_file=payload.name_file,
        language=payload.language
    )

async def processar_tratar_texto_wrapper(msg, connection: RabbitMQConnection):
    # Aqui você processa a mensagem
    result = await processar_tratar_texto(msg)

    producer = RabbitMQProducer(connection)
    await producer.setup_exchange()
    await producer.bind_queue(TranscribeTextDTO.QUEUE_NAME, "transcribe_text_routing_key")
    await producer.publishJson(result.to_dict(), routing_key="transcribe_text_routing_key")