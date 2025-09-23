from dataclasses import asdict
import json


class QueueDtoBase:
    """
    Base class para DTOs de fila. Fornece to_dict, to_json e métodos para transformar JSON em DTO.
    """
    QUEUE_NAME: str = ""

    def to_dict(self) -> dict:
        # assume que a instância é um dataclass (como os DTOs que herdam desta classe)
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @staticmethod
    def json_to_dict(payload):
        """Converte string JSON ou dict em dict."""
        if isinstance(payload, dict):
            return payload
        return json.loads(payload)

    @classmethod
    def from_json(cls, payload):
        """
        Constrói a instância do DTO a partir de uma string JSON ou dict.
        Uso: ExtractTextDTO.from_json(json_str) -> ExtractTextDTO(...)
        """
        data = cls.json_to_dict(payload)
        return cls(**data)