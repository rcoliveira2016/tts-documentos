from pathlib import Path
import tempfile
from aio_pika.abc import AbstractIncomingMessage
import pypandoc
from ttsdocumentos_core.config import settings
from ttsdocumentos_core.azure_blob import AzureBlobUtils
from ttsdocumentos_core.domiain.workers.extract_text_dto import ExtractTextDTO
from ttsdocumentos_core.domiain.workers.treat_text_dto import TreatTextDTO
from ttsdocumentos_core.log.log_maneger import LogLevels, LoggerManager, LoggerNames
from ttsdocumentos_core.rabbitmq.rabbitmq import RabbitMQConnection, RabbitMQProducer
logger = LoggerManager(nome=LoggerNames.WORKER, level=LogLevels.DEBUG)
azure_blob_utils = AzureBlobUtils()

async def processar_estrair_texto(message: AbstractIncomingMessage):
    payload = ExtractTextDTO.from_json(message.body.decode())
    logger.info(f"Extraindo texto do documento ID: {payload.document_id}")
    logger.info(f"nome: {payload.name_file}")
    retorno: TreatTextDTO | None = None
    with tempfile.NamedTemporaryFile(suffix=Path(payload.name_file).suffix, delete=True) as download_file:
        name_file = download_file.name    
        pathFile = azure_blob_utils.download_file(payload.name_file, name_file)
        logger.info(f"Arquivo baixado em: {pathFile}")
        with tempfile.NamedTemporaryFile(delete=True) as convert_file:
            pypandoc.convert_file(
                source_file=pathFile,
                to="markdown",
                outputfile=convert_file.name,
                extra_args=[
                    "--standalone",
                ]
            )
            retorno = TreatTextDTO(
                name_file=payload.name_file,
                conteudo=convert_file.read().decode('utf-8'),  
                document_id= payload.document_id,              
                language=payload.language
            )

    azure_blob_utils.delete_file(payload.name_file)
    return retorno

async def processar_estrair_texto_wrapper(msg, connection: RabbitMQConnection):
    # Aqui você processa a mensagem
    result = await processar_estrair_texto(msg)
    
    producer = RabbitMQProducer(connection)
    await producer.setup_exchange()
    await producer.bind_queue(TreatTextDTO.QUEUE_NAME, f"{TreatTextDTO.QUEUE_NAME}_routing_key")
    await producer.publishJson(result.to_dict(), routing_key=f"{TreatTextDTO.QUEUE_NAME}_routing_key")