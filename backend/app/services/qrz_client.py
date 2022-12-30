import logging
import asyncio

import httpx
import xmltodict
from xml.parsers.expat import ExpatError

from app.core.config import QRZ_USER, QRZ_PASSWORD

client = httpx.AsyncClient()

class QrzError(Exception):
    pass

class QrzClient:

    def __init__(self):
        self._session_id = None



    async def get_session_id(self):
        try:
            response = await client.get(f'https://xmldata.qrz.com/xml/current/?username={QRZ_USER};password={QRZ_PASSWORD}')
            response.raise_for_status()
            session_data = xmltodict.parse(response.text)
            self._session_id = session_data['QRZDatabase']['Session']['Key']
        except (httpx.HTTPError, ExpatError, KeyError) as exc:
            logging.exception('QrzClient: error while getting qrz.com session id')
            #retry 5 minutes later
            await asyncio.sleep(300)
            await self.get_session_id()

    async def lookup(self, callsign):
        if self._session_id:
            try:
                response = await client.get(f'https://xmldata.qrz.com/xml/current/?s={self._session_id};callsign={callsign}')
                response.raise_for_status()
                data = xmltodict.parse(response.text)
                if 'Callsign' in data['QRZDatabase']:
                    return data['QRZDatabase']['Callsign']
                elif ('Session' in data['QRZDatabase'] and 'Error' in data['QRZDatabase']['Session'] and 
                    (data['QRZDatabase']['Session']['Error'] == 'Session Timeout' or 
                    data['QRZDatabase']['Session']['Error'] == 'Invalid session key')):
                    await self.get_session_id()
                    if self._session_id:
                        return await self.lookup(callsign)
                elif 'Session' in data['QRZDatabase'] and 'Error' in data['QRZDatabase']['Session']:
                    if 'Not found' in data['QRZDatabase']['Session']['Error']:
                        return None
                    else:
                        raise QrzError(data['QRZDatabase']['Session']['Error'])
                else:
                    raise QrzError('Unexpected qrz.com response: \n' + response.text)
            except (httpx.HTTPError, ExpatError, KeyError) as exc:
                logging.exception('QrzClient: error while querying qrz.com')
                return None
        else:
            await self.get_session_id()
            if self._session_id:
                return await self.lookup(callsign)


