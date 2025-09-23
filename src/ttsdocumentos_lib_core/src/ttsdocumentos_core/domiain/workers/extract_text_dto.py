from dataclasses import asdict, dataclass
from typing import ClassVar
from ttsdocumentos_core.domiain.workers.queue_dto_base import QueueDtoBase


@dataclass
class ExtractTextDTO(QueueDtoBase):
    QUEUE_NAME: ClassVar[str] = "extract_text"
    document_id: str
    name_file: str
    language: str = "pt"