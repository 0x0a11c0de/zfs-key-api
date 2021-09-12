import os
from azure.core.exceptions import ResourceNotFoundError
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from fastapi import HTTPException


# The Azure client uses the following environment variables:
#   AZURE_CLIENT_ID
#   AZURE_CLIENT_SECRET
#   AZURE_TENANT_ID
#   AZURE_VAULT_URL
class AzureClient:
    def __init__(self):
        self._vault_url = os.getenv('AZURE_VAULT_URL')

    def _client(self, client_class):
        try:
            credential = DefaultAzureCredential()
            return client_class(self._vault_url, credential)
        except Exception as exc:
            raise HTTPException(status_code=401, detail=str(exc))

    def get_secret(self, dataset):
        client = self._client(SecretClient)
        try:
            return client.get_secret(dataset).value
        except ResourceNotFoundError:
            raise HTTPException(status_code=404, detail="dataset not found")
        except Exception as exc:
            raise HTTPException(status_code=404, detail=str(exc))

    def get_secrets(self):
        client = self._client(SecretClient)
        try:
            secret_props = client.list_properties_of_secrets()
            return [(sp.name, client.get_secret(sp.name).value) for sp in secret_props]
        except Exception as exc:
            raise HTTPException(status_code=404, detail=str(exc))
