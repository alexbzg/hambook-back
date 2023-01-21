from typing import AsyncIterator, Any
import time

from app.models.qso import QsoBase

def adif_field(name: str, data: Any) -> str:
    dataStr = str(data) if data else ''
    return f"<{name.upper()}:{len(dataStr)}>{dataStr} "


async def create_adif(qsos: AsyncIterator[QsoBase]) -> AsyncIterator[str]:
    yield f"""ADIF Export from TNXLOG
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
            adif_field("FREQ", qso.freq),
            adif_field("MODE", qso.qso_mode),
            adif_field("RST_R", qso.rst_r),
            adif_field("RST_S", qso.rst_s),
            adif_field("GRIDSQUARE", qso.gridsquare),
            "<EOR>\n"))
           

           






