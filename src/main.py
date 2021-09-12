import uvicorn
from fastapi import FastAPI, Request
from pydantic import BaseModel

from azure_client import AzureClient
from duo_auth import DuoAuth

app = FastAPI()
_client = AzureClient()
_auth = DuoAuth()


class Secret(BaseModel):
    name: str
    value: str


@app.get("/secrets/{dataset}")
def get_key(dataset: str, request: Request, response_model=Secret):
    _auth.authenticate(dataset, request.client.host)
    return Secret(name=dataset, value=_client.get_secret(dataset))


@app.get("/secrets")
def get_key(request: Request, response_model=Secret):
    _auth.authenticate(request.client.host, 'all')
    return [Secret(name=dataset, value=key) for dataset, key in _client.get_secrets()]


if __name__ == '__main__':
    uvicorn.run('main:app', host='0.0.0.0', port=5000, log_level='info')
