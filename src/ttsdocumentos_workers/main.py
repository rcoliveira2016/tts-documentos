import asyncio
import signal
from functools import partial
from ttsdocumentos_core.config import settings
from ttsdocumentos_core.domiain.workers.extract_text_dto import ExtractTextDTO
from ttsdocumentos_core.domiain.workers.finalize_text_dto import FinalizeTextDTO
from ttsdocumentos_core.domiain.workers.transcribe_text_dto import TranscribeTextDTO
from ttsdocumentos_core.domiain.workers.treat_text_dto import TreatTextDTO
from ttsdocumentos_core.log.log_maneger import LogLevels, LoggerManager, LoggerNames
from ttsdocumentos_core.rabbitmq.rabbitmq import RabbitMQConnection, RabbitMQConsumer
from workers.finalizar_processo import processar_finalizar_processo_wrapper
from workers.transcrever_texto import processar_transcrever_texto_wrapper
from workers.tratar_texto import processar_tratar_texto_wrapper
from workers.extract_text import processar_estrair_texto_wrapper

logger = LoggerManager(nome=LoggerNames.WORKER, level=LogLevels.DEBUG)

async def main():

    stop_event = asyncio.Event()
    # Captura SIGINT (Ctrl+C) e SIGTERM
    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGINT, stop_event.set)
    loop.add_signal_handler(signal.SIGTERM, stop_event.set)

    rabbit_connection = await RabbitMQConnection(settings).connect()

    tasks = [
        asyncio.create_task(processar_fila(rabbit_connection, ExtractTextDTO.QUEUE_NAME, processar_estrair_texto_wrapper)),
        asyncio.create_task(processar_fila(rabbit_connection, TreatTextDTO.QUEUE_NAME, processar_tratar_texto_wrapper)),
        asyncio.create_task(processar_fila(rabbit_connection, TranscribeTextDTO.QUEUE_NAME, processar_transcrever_texto_wrapper)),
        asyncio.create_task(processar_fila(rabbit_connection, FinalizeTextDTO.QUEUE_NAME, processar_finalizar_processo_wrapper)),
    ]

    logger.info("WORKERS rodando. Pressione Ctrl+C para parar.")

    await stop_event.wait()

    logger.info("Parando aplicação...")

    for task in tasks:
        task.cancel()
    await rabbit_connection.close()


async def processar_fila(connection: RabbitMQConnection, queue_name: str, callback):
    consumer = RabbitMQConsumer(connection=connection, queue_name=queue_name)
    logger.info(f"Iniciando consumo da fila '{queue_name}'...")
    
    # Passando o connection para o callback
    await consumer.start_consuming(callback=partial(callback, connection=connection))

if __name__ == "__main__":
    asyncio.run(main())
