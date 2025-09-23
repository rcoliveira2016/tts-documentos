from dataclasses import asdict, dataclass
from typing import ClassVar
from ttsdocumentos_core.domiain.workers.queue_dto_base import QueueDtoBase


@dataclass
class FinalizeTextDTO(QueueDtoBase):
    QUEUE_NAME: ClassVar[str] = "finalize_text"
    name_file: str
    path_audio: str