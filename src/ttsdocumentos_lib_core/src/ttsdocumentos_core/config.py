from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    """Configurações globais do projeto (carregadas do .env)."""

    # 🛠️ Outros configs (ex.: Debug, ambiente)
    environment: str = Field(default="dev", env="APP_ENV")
    debug: bool = Field(default=True, env="DEBUG")
    azure_storage_connection_string: str = Field(
        default="", env="AZURE_STORAGE_CONNECTION_STRING"
    )
    azure_container_name: str = Field(
        default="", env="AZURE_CONTAINER_NAME"
    )
    allowed_extensions: list[str] = Field(
        default=[".docx"], env="ALLOWED_EXTENSIONS"
    )

    # KOKORO
    kokoro_url_onnx: str = Field(default="", env="KOKORO_URL_ONNX")
    kokoro_url_bin: str = Field(default="", env="KOKORO_URL_BIN")
    kokoro_path_relative: str = Field(default="", env="KOKORO_PATH_RELATIVE")

    # 🐰 RabbitMQ
    rabbitmq_user: str = Field(default="guest", env="RABBITMQ_USER")
    rabbitmq_pass: str = Field(default="guest", env="RABBITMQ_PASS")
    rabbitmq_host: str = Field(default="localhost", env="RABBITMQ_HOST")
    rabbitmq_port: int = Field(default=5672, env="RABBITMQ_PORT")

    #WORKERS
    file_temp_audio: str = Field(default="./TEMP_FILES", env="FILE_TEMP_AUDIO")
    
    class Config:
        env_file = ".env"  # permite carregar automaticamente de um arquivo .env
        env_file_encoding = "utf-8"
        extra = "allow"

# ✅ Instância global de config
settings = Settings()