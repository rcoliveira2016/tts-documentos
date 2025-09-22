import asyncio
import signal
from functools import partial
from ttsdocumentos_core.config import settings
from ttsdocumentos_core.log.log_maneger import LogLevels, LoggerManager, LoggerNames
from ttsdocumentos_core.rabbitmq.rabbitmq import RabbitMQConnection, RabbitMQConsumer
from workers.extract_text import processar_estrair_texto_wrapper

logger = LoggerManager(nome=LoggerNames.API, level=LogLevels.DEBUG)

async def main():
    stop_event = asyncio.Event()

    loop = asyncio.get_running_loop()
    for s in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(s, stop_event.set)

    rabbit_connection = await RabbitMQConnection(settings).connect()

    tasks = [
        asyncio.create_task(processar_fila(rabbit_connection, "extract_text", processar_estrair_texto_wrapper)),
    ]

    logger.info("API rodando. Pressione Ctrl+C para parar.")

    await stop_event.wait()

    logger.info("Parando aplicação...")

    for task in tasks:
        task.cancel()

    for task in tasks:
        try:
            await task
        except asyncio.CancelledError:
            pass


async def processar_fila(connection: RabbitMQConnection, queue_name: str, callback):
    consumer = RabbitMQConsumer(connection=connection, queue_name=queue_name)
    logger.info(f"Iniciando consumo da fila '{queue_name}'...")
    
    # Passando o connection para o callback
    await consumer.start_consuming(callback=partial(callback, connection=connection))

if __name__ == "__main__":
    asyncio.run(main())
