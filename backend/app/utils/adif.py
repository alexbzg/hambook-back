from typing import AsyncIterator, Any, Iterator, List, Dict
from decimal import Decimal
import time
import logging
import re
from datetime import datetime

import chardet

from app.models.qso import QsoBase, QsoMode, Band, def_freq, freq_to_band
from app.models.core import FullCallsign

def adif_field(name: str, data: Any) -> str:
    dataStr = str(data) if data else ''
    return f"<{name.upper()}:{len(dataStr)}>{dataStr} "


async def create_adif(qsos: AsyncIterator[QsoBase]) -> AsyncIterator[str]:
    yield f"""ADIF Export from HAMBOOK.net
Logs generated @ {time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())}
<EOH>"""

    async for qso in qsos:
        yield ' '.join((
            adif_field("CALL", qso.callsign),
            adif_field("QSO_DATE", qso.qso_datetime.strftime("%Y%m%d")),
            adif_field("TIME_ON", qso.qso_datetime.strftime("%H%M%S")),
            adif_field("TIME_OFF", qso.qso_datetime.strftime("%H%M%S")),
            adif_field("BAND", qso.band),
            adif_field("STATION_CALLSIGN", qso.station_callsign),
            adif_field("FREQ", Decimal(qso.freq)/1000),
            adif_field("MODE", qso.qso_mode),
            adif_field("RST_RCVD", qso.rst_r),
            adif_field("RST_SENT", qso.rst_s)))
        if qso.extra:
            yield ' '.join([adif_field(field, value) for field, value in qso.extra.items()])
        yield " <EOR>\n"

def parse_adif(file_path: str, log_settings: dict, qso_errors: Dict) -> Iterator[QsoBase]:
    re_field = re.compile(r"<(\w+):(\d+):?\w*>")
    re_digits = re.compile(r"\D.*")

    def get_rst(rst_str):
        sign = 1
        if rst_str.startswith('-'):
            sign = -1
            rst_str = rst_str[1:]
        return int(re_digits.sub('', rst_str.lstrip('0+')) or '0') * sign

    with open(file_path, 'rb') as file:
        rawdata = file.read(1024)
        encoding = chardet.detect(rawdata)['encoding']
        if (not encoding) or encoding == 'ascii':
            encoding = 'utf-8'


    with open(file_path, 'r', encoding=encoding) as file:
        eoh = False
        buf = ''

        for line in file:
            line = line.upper()
            if not eoh and '<EOH>' in line:
                eoh = True
                buf = line.split('<EOH>')[1]
            else:
                buf += line

            if '<EOR>' in buf:
                if buf.strip().endswith('<EOR>'):
                    qso_lines, buf = buf, ''
                else:
                    qso_lines, buf = buf.rsplit('<EOR>', 1)
                qso_lines = qso_lines.split('<EOR>')
                for qso_line in qso_lines:
                    if '<' in qso_line:
                        qso_fields = {}
                        for match in re_field.finditer(qso_line):
                            name, length = match.groups()
                            if length != '0':
                                field_start = match.end()
                                qso_fields[name] = qso_line[field_start : field_start + int(length)]
                        try:
                            qso_data = {}
                            try:
                                qso_data['callsign'] = FullCallsign(qso_fields.get("CALL"))
                            except Exception:
                                qso_errors['Missing or invalif field (CALL)'] += 1
                                continue
                            qso_time = qso_fields.get("TIME_ON") or qso_fields.get("TIME_OFF")
                            if not qso_time:
                                qso_errors['Missing or invalif field (TIME_ON, TIME_OFF)'] += 1
                                continue
                            datetime_format = '%Y%m%d %H%M%S' if len(qso_time) == 6 else '%Y%m%d %H%M'
                            try:
                                qso_data['qso_datetime'] = datetime.strptime(
                                        f'{qso_fields.get("QSO_DATE")} {qso_time}',
                                        datetime_format)
                            except Exception:
                                qso_errors['Missing or invalid field (QSO_DATE)'] += 1
                                continue
                            qso_data['station_callsign'] = (qso_fields.get("STATION_CALLSIGN") or 
                                    log_settings.get('callsign'))

                            try:
                                qso_data['qso_mode'] = QsoMode(qso_fields.get("MODE"))
                            except Exception:
                                qso_errors['Missing or invalid field (MODE)'] += 1
                                continue

                            try:
                                qso_data['band'] = Band(qso_fields.get("BAND"))
                            except Exception:
                                qso_data['band'] = None

                            try:
                                qso_data['freq'] = Decimal(qso_fields.get("FREQ"))*1000
                            except Exception:
                                qso_data['freq'] = None

                            if not qso_data['freq']:
                                if qso_data['band']:
                                    qso_data['freq'] = def_freq(qso_data['band'], qso_data['qso_mode'])
                                else:
                                    qso_errors['Missing or invalid field (BAND, FREQ)'] += 1
                                    continue
                            if not qso_data['band']:
                                qso_data['band'] = freq_to_band(qso_data['freq'])
 
                            qso_data['rst_r'] = get_rst(qso_fields.get("RST_RCVD"))
                            qso_data['rst_s'] = get_rst(qso_fields.get("RST_SENT"))
                            qso_data['extra'] = {field: value for field, value in qso_fields.items() 
                                    if field not in ("CALL", "QSO_DATE", "TIME_ON", "TIME_OFF", "BAND",
                                            "FREQ", "MODE", "STATION_CALLSIGN", "RST_RCVD", "RST_SENT") 
                                        and value}
                            yield QsoBase(**qso_data)
                        except Exception as exc:
                            logging.exception(exc)
                            logging.error(qso_line)

