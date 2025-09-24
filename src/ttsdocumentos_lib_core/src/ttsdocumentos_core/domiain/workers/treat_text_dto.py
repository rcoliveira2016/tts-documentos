from dataclasses import asdict, dataclass
from typing import ClassVar
from ttsdocumentos_core.domiain.workers.queue_dto_base import QueueDtoBase


@dataclass
class TreatTextDTO(QueueDtoBase):
    QUEUE_NAME: ClassVar[str] = "treat_text"
    document_id: str
    name_file: str
    conteudo: str
    language: str = "pt"