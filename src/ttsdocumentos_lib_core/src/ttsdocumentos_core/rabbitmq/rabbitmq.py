import json
import aio_pika
from aio_pika.abc import AbstractIncomingMessage
from ttsdocumentos_core.config import Settings
from ttsdocumentos_core.log.log_maneger import LogLevels, LoggerManager, LoggerNames  # importa sua classe de config

logger = LoggerManager(nome=LoggerNames.WORKER, level=LogLevels.DEBUG)


class RabbitMQConnection:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.connection: aio_pika.RobustConnection | None = None
        self.channel: aio_pika.RobustChannel | None = None

    async def connect(self):
        self.connection = await aio_pika.connect_robust(
            host=self.settings.rabbitmq_host,
            port=self.settings.rabbitmq_port,
            login=self.settings.rabbitmq_user,
            password=self.settings.rabbitmq_pass,
        )
        self.channel = await self.connection.channel()
        await self.channel.set_qos(prefetch_count=10)
        return self

    async def close(self):
        if self.connection:
            await self.connection.close()


class RabbitMQProducer:
    def __init__(self, connection: RabbitMQConnection, exchange_name: str = "tts_exchange", exchange_type: str = "direct"):
        self.connection = connection
        self.exchange_name = exchange_name
        self.exchange_type = exchange_type
        self.exchange: aio_pika.Exchange | None = None

    async def setup_exchange(self):
        """Declara a exchange no RabbitMQ."""
        if not self.connection.channel:
            raise RuntimeError("❌ Canal RabbitMQ não está conectado.")
        self.exchange = await self.connection.channel.declare_exchange(
            self.exchange_name, 
            aio_pika.ExchangeType(self.exchange_type), 
            durable=True
        )

    async def bind_queue(self, queue_name: str, routing_key: str):
        """Faz o bind de uma fila à exchange com uma routing key."""
        if not self.connection.channel or not self.exchange:
            raise RuntimeError("❌ Canal RabbitMQ ou exchange não está configurado.")
        queue = await self.connection.channel.declare_queue(queue_name, durable=True)
        await queue.bind(self.exchange, routing_key)

    async def publishJson(self, payload: dict, routing_key: str):
        """Publica um objeto Python (dict) serializado como JSON."""
        if not self.connection.channel or not self.exchange:
            raise RuntimeError("❌ Canal RabbitMQ ou exchange não está configurado.")
        body = json.dumps(payload).encode("utf-8")
        await self.exchange.publish(
            aio_pika.Message(body=body, content_type="application/json"),
            routing_key=routing_key,            
        )
    async def publish(self, payload: str, routing_key: str):
        """Publica um objeto Python (dict) serializado."""
        if not self.connection.channel or not self.exchange:
            raise RuntimeError("❌ Canal RabbitMQ ou exchange não está configurado.")
        body = payload
        await self.exchange.publish(
            aio_pika.Message(body=body, content_type="application/json"),
            routing_key=routing_key,            
        )


class RabbitMQConsumer:
    def __init__(self, connection: RabbitMQConnection, queue_name: str):
        self.connection = connection
        self.queue_name = queue_name

    async def start_consuming(self, callback):
        if not self.connection.channel:
            raise RuntimeError("❌ Canal RabbitMQ não está conectado.")
        queue = await self.connection.channel.declare_queue(self.queue_name, durable=True)
        await queue.consume(lambda msg: self._on_message(msg, callback))

    async def _on_message(self, message: AbstractIncomingMessage, callback):
        async with message.process():
            try:
                logger.info(f"✅ Mensagem recebida na fila '{self.queue_name}'")
                await callback(message)
            except Exception as e:
                logger.error(f"❌ Erro ao processar mensagem: {e}")