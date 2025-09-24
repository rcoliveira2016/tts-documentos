import logging

class LogLevels:
    """Constantes de níveis de log para uso padronizado."""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class LoggerNames:
    """Constantes para nomes de loggers (padroniza categorias de log)."""
    API = "API"
    Core = "Core"
    WORKER = "Worker"


class LoggerManager:
    _instances: dict[str, "LoggerManager"] = {}

    def __new__(cls, nome: str = LoggerNames.Core, level=LogLevels.INFO):
        """
        Singleton: garante que cada 'nome' terá apenas um logger.
        """
        if nome not in cls._instances:
            instance = super().__new__(cls)
            cls._instances[nome] = instance        
        return cls._instances[nome]

    def __init__(self, nome: str = LoggerNames.Core, level=LogLevels.INFO):
        # evita reconfiguração caso o logger já tenha sido criado
        if hasattr(self, "logger"):
            return

        self.logger = logging.getLogger(nome)
        self.logger.setLevel(level)

        # 🎯 Formato dos logs
        formatter = logging.Formatter(
            "%(asctime)s | %(name)s | %(levelname)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # 📌 Apenas console
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def _setLevel(self, level: int):
        """
        Define o nível de log do logger.
        """
        self.logger.setLevel(level)
        for handler in self.logger.handlers:
            handler.setLevel(level)

    # 🔹 Métodos de atalho
    def debug(self, msg: str): self.logger.debug(msg)
    def info(self, msg: str): self.logger.info(msg)
    def warning(self, msg: str): self.logger.warning(msg)
    def error(self, msg: str): self.logger.error(msg)
    def critical(self, msg: str): self.logger.critical(msg)
    def exception(self, msg, *args): self.logger.exception(msg, *args)

