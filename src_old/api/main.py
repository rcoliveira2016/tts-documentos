import shutil
import tempfile
from typing import Annotated
import uuid
from core.config import settings
from core.log_maneger import LoggerManager, LoggerNames, LogLevels
from core.utils.azure_blob import AzureBlobUtils
from fastapi import FastAPI, Form, UploadFile, File,HTTPException
from pathlib import Path
from core.utils import rabbitmq

app = FastAPI()

azure_blob_utils = AzureBlobUtils()
log_app = LoggerManager(LoggerNames.APP, level=LogLevels.DEBUG)

@app.get("/")
def read_root():
    return {"Hello": f"World {settings.environment}"}

@app.post("/send-document")
def send_document(
    document_id: Annotated[str, Form()],
    file: Annotated[UploadFile, File()]
):    
    try:
        document_id_guid = uuid.UUID(document_id)
    except ValueError:
        log_app.error(f"Invalid document ID: {document_id}")
        raise HTTPException(status_code=400, detail="Document ID must be a valid GUID")
    
    if not file:
        log_app.error("File is required")
        return HTTPException(status_code=400, detail="File is required")
    
    path_file = Path(file.filename)
    extensao = path_file.suffix

    if extensao not in settings.allowed_extensions:
        log_app.error(f"Invalid file extension: {extensao}")
        raise HTTPException(status_code=400, detail=f"Invalid file extension. Allowed extensions: {settings.allowed_extensions}")

    with tempfile.NamedTemporaryFile(delete=False,) as temp_file:
        shutil.copyfileobj(file.file, temp_file)

    name_file = f'{document_id_guid}{extensao}'
    azure_blob_utils.upload_file(temp_file.name, name_file)
    log_app.info(f"File {file.filename} uploaded successfully to document {name_file}")
    rabbitmq.publish(
        exchange= "documents",
        routing_key= "extract_text_queue",
        body={
            "document_id": str(document_id_guid),
            "request_id": str(uuid.uuid4()),
        }
    )
    temp_file.close()
    file.file.close()        
    return {"Status": f"Enviado com sucesso o arquivo {file.filename} para o documento {name_file}"}