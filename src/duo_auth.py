import os
import socket
from urllib.parse import urlencode
from fastapi import HTTPException
from duo_client.client import Client


class DuoAuth:
    def __init__(self):
        self._enabled = bool(int(os.environ.get('DUO_ENABLED', 1)))
        self._ikey = os.getenv('DUO_CLIENT_ID')
        self._skey = os.getenv('DUO_CLIENT_SECRET')
        self._host = os.getenv('DUO_API_HOSTNAME')
        self._username = os.getenv('DUO_USERNAME')

    def authenticate(self, client_host, dataset):
        if not self._enabled:
            return

        client = Client(ikey=self._ikey, skey=self._skey, host=self._host, timeout=75)
        try:
            resp = client.json_api_call(
                method='POST',
                path='/auth/v2/preauth',
                params={'username': self._username}
            )
            result = resp['result']
            if result == 'allow':
                return
            elif result != 'auth':
                raise HTTPException(status_code=401, detail=f"Duo: {resp['status_msg']}")

            devices = [device for device in resp['devices'] if 'push' in device['capabilities']]
            if not devices:
                raise HTTPException(status_code=401, detail='Duo: At least 1 device must support push')

            resp = client.json_api_call(
                method='POST',
                path='/auth/v2/auth',
                params={
                    'username': self._username,
                    'device': devices[0]['device'],
                    'factor': 'push',
                    'hostname': client_host,
                    'async': '1',
                    'type': 'Key Request',
                    'pushinfo': urlencode({'dataset': dataset}),
                }
            )
            txid = resp.get('txid')
            if not txid:
                raise HTTPException(status_code=401, detail='Duo: no txid')

            result = ''
            while result not in ('allow', 'deny'):
                resp = client.json_api_call(
                    method='GET',
                    path='/auth/v2/auth_status',
                    params={'txid': txid}
                )
                result = resp['result']
        except socket.timeout:
            raise HTTPException(status_code=401, detail='Duo: authentication timed out')
        except Exception as exc:
            raise HTTPException(status_code=401, detail=f'Duo: error: {str(exc)}')
        if result != 'allow':
            raise HTTPException(status_code=401, detail=f"Duo: {resp['status_msg']}")
