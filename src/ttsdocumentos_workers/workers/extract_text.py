from aio_pika.abc import AbstractIncomingMessage
from ttsdocumentos_core.rabbitmq.rabbitmq import RabbitMQConnection

async def processar_estrair_texto(message: AbstractIncomingMessage):
    print("Processando mensagem:", message.body.decode())
    import json
    data = json.loads(message.body.decode())
    document_id = data.get("document_id")
    print(f"Extraindo texto do documento ID: {document_id}")
    extracted_text = "Texto extraído do documento"
    print(f"Texto extraído: {extracted_text}")

async def processar_estrair_texto_wrapper(msg, connection: RabbitMQConnection):
    # Aqui você processa a mensagem
    await processar_estrair_texto(msg)
    
    # Exemplo: publicar mensagem em outra fila
    await connection.channel.default_exchange.publish(
        msg, routing_key="other_queue"
    )