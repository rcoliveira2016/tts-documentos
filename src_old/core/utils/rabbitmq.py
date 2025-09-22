import pika
import json
from core.config import settings

def connect():
    credentials = pika.PlainCredentials(settings.rabbitmq_user, settings.rabbitmq_pass)
    parameters = pika.ConnectionParameters(
        host=settings.rabbitmq_host,
        port=settings.rabbitmq_port,
        credentials=credentials,
        heartbeat=600,
        blocked_connection_timeout=300,
    )
    return pika.BlockingConnection(parameters)

def publish(exchange: str, routing_key: str, message: dict):
    connection = connect()
    channel = connection.channel()
    channel.exchange_declare(exchange=exchange, exchange_type="direct", durable=True)
    channel.basic_publish(
        exchange=exchange,
        routing_key=routing_key,
        body=json.dumps(message),
        properties=pika.BasicProperties(
            delivery_mode=2  # mensagem persistente
        )
    )
    connection.close()
