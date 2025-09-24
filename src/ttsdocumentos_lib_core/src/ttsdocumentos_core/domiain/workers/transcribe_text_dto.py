from dataclasses import asdict, dataclass
from typing import ClassVar
from ttsdocumentos_core.domiain.workers.queue_dto_base import QueueDtoBase


@dataclass
class TranscribeTextDTO(QueueDtoBase):
    QUEUE_NAME: ClassVar[str] = "transcribe_text"
    conteudo: str
    name_file: str
    document_id: str
    language: str = "pt"