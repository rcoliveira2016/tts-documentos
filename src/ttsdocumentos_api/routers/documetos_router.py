import asyncio
from pathlib import Path
import shutil
import tempfile
from typing import Annotated
import uuid
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from ttsdocumentos_core.azure_blob import AzureBlobUtils
from ttsdocumentos_core.domiain.workers.extract_text_dto import ExtractTextDTO
from ttsdocumentos_core.log.log_maneger import LogLevels, LoggerManager, LoggerNames
from ttsdocumentos_core.config import settings
from ttsdocumentos_core.rabbitmq.rabbitmq import RabbitMQConnection, RabbitMQProducer

logger = LoggerManager(nome=LoggerNames.API, level=LogLevels.DEBUG)
azure_blob_utils = AzureBlobUtils()

routerDocumentos = APIRouter(
    prefix="/documentos",
    tags=["documentos"],
    responses={404: {"description": "Not found"}},
)

# Objetos globais
rabbit_connection: RabbitMQConnection | None = None
producer: RabbitMQProducer | None = None

async def iniciar_fila(body: dict):
    global producer

    await conectar_rabbitmq()

    if not producer:
        raise HTTPException(status_code=500, detail="RabbitMQ producer is not initialized")
    
    await producer.setup_exchange()
    await producer.bind_queue(ExtractTextDTO.QUEUE_NAME, f"{ExtractTextDTO.QUEUE_NAME}_routing_key")
    await producer.publishJson(body, routing_key=f"{ExtractTextDTO.QUEUE_NAME}_routing_key")


async def conectar_rabbitmq():
    """Tenta conectar ao RabbitMQ em background com retry exponencial"""
    global rabbit_connection, producer
    logger.info("Attempting to connect to RabbitMQ(temiout)...")
    rabbit_connection = await RabbitMQConnection(settings).connect()
    producer = RabbitMQProducer(rabbit_connection)
    logger.info("Connected to RabbitMQ")

@routerDocumentos.on_event("shutdown")
async def shutdown_event():
    if rabbit_connection:
        await rabbit_connection.close()

@routerDocumentos.post("/importar")
async def importar_documentos(
    document_id: Annotated[str, Form()],
    file: Annotated[UploadFile, File()]
):
    try:
        document_id_guid = uuid.UUID(document_id)
    except ValueError:
        logger.error(f"Invalid document ID: {document_id}")
        raise HTTPException(status_code=400, detail="Document ID must be a valid GUID")
    
    if not file:
        logger.error("File is required")
        return HTTPException(status_code=400, detail="File is required")
    
    path_file = Path(file.filename)
    extensao = path_file.suffix

    if extensao not in settings.allowed_extensions:
        logger.error(f"Invalid file extension: {extensao}")
        raise HTTPException(status_code=400, detail=f"Invalid file extension. Allowed extensions: {settings.allowed_extensions}")

    with tempfile.NamedTemporaryFile(delete=False,) as temp_file:
        shutil.copyfileobj(file.file, temp_file)

    name_file = f'{document_id_guid}{extensao}'
    azure_blob_utils.upload_file(temp_file.name, name_file)
    logger.info(f"File {file.filename} uploaded successfully to document {name_file}")        
    temp_file.close()
    file.file.close()

    await iniciar_fila(ExtractTextDTO(
        document_id=document_id,
        name_file=name_file,
        language="pt"
    ).to_dict())

    return {"Mensagem": "Processando importação de documentos"}