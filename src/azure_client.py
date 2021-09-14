import os
from typing import Dict
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

    def get_secrets(self) -> Dict[str, str]:
        client = self._client(SecretClient)
        try:
            secret_props = client.list_properties_of_secrets()
            datasets = {}
            for sp in secret_props:
                dataset, secret = client.get_secret(sp.name).value.split(':')
                datasets[dataset.strip()] = secret.strip()
            return datasets
        except ValueError:
            raise HTTPException(status_code=404, detail='Invalid secret format, should be <dataset>:<hex key>')
        except Exception as exc:
            raise HTTPException(status_code=404, detail=str(exc))
