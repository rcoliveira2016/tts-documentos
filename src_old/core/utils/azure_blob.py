import os
from azure.storage.blob import BlobServiceClient
from ..config import settings


class AzureBlobUtils:
    def __init__(self):
        connection_string = settings.azure_storage_connection_string
        self.container_name = settings.azure_container_name

        if not connection_string or not self.container_name:
            raise ValueError("⚠️ Variáveis de ambiente não configuradas corretamente.")

        self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        self.container_client = self.blob_service_client.get_container_client(self.container_name)

    def upload_file(self, file_path: str, blob_name: str = None) -> str:
        """Faz upload de um arquivo para o Azure Blob Storage."""
        if not blob_name:
            blob_name = os.path.basename(file_path)

        blob_client = self.container_client.get_blob_client(blob_name)

        with open(file_path, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)

        return f"Arquivo {blob_name} enviado com sucesso para {self.container_name}."

    def download_file(self, blob_name: str, download_path: str) -> str:
        """Baixa um arquivo do Azure Blob Storage."""
        blob_client = self.container_client.get_blob_client(blob_name)

        with open(download_path, "wb") as file:
            file.write(blob_client.download_blob().readall())

        return f"Arquivo {blob_name} baixado com sucesso para {download_path}."

    def delete_file(self, blob_name: str) -> str:
        """Deleta um arquivo do Azure Blob Storage."""
        blob_client = self.container_client.get_blob_client(blob_name)
        blob_client.delete_blob()
        return f"Arquivo {blob_name} removido do container {self.container_name}."
