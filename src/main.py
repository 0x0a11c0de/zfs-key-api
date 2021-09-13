import os
import argparse
import secrets
import re
from typing import Optional

import uvicorn
from fastapi import FastAPI, Request, Header, HTTPException
from pydantic import BaseModel

from azure_client import AzureClient
from duo_auth import DuoAuth

app = FastAPI()
_client = AzureClient()
_auth = DuoAuth()
_token = os.getenv('ZFS_KEY_API_TOKEN')
_token_re = re.compile('^[Bb]earer\s+(.*)')

class Dataset(BaseModel):
    dataset: str
    key: str


def _authenticate(authorization):
    if authorization is None:
        raise HTTPException(status_code=401, detail='Authorization header is missing')
    match = _token_re.match(authorization)
    if not match:
        raise HTTPException(status_code=401, detail='Invalid token format')
    token = match.groups()[0]
    if token != _token:
        raise HTTPException(status_code=401, detail='Invalid token')


@app.get("/datasets/{dataset}")
def get_key(dataset: str, request: Request, authorization: str=Header(None), response_model=Dataset):
    _authenticate(authorization)
    _auth.authenticate(dataset, request.client.host)
    return Dataset(dataset=dataset, key=_client.get_secret(dataset))


@app.get("/datasets")
def get_key(request: Request, authorization: str=Header(None), response_model=Dataset):
    _authenticate(authorization)
    _auth.authenticate(request.client.host, 'all')
    return [Dataset(dataset=dataset, key=key) for dataset, key in _client.get_secrets()]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='ZFS Key API')
    parser.add_argument('-t', '--token', action='store_true',
                        help='Generate a cryptographically secure random token and exit')
    parser.add_argument('-r', '--root-path', default=os.environ.get('ZFS_KEY_API_ROOT_PATH', ''),
                        help='Set the root path when behind a reverse proxy')
    args = parser.parse_args()
    if args.token:
        print(secrets.token_urlsafe(64))
        raise SystemExit(0)

    if args.root_path:
        print(f'Root path: {args.root_path}')
    uvicorn.run('main:app', host='0.0.0.0', port=5000, log_level='info', root_path=args.root_path)
