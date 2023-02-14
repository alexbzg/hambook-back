from typing import Optional, Dict
from pydantic import BaseModel
from datetime import datetime, date
from enum import StrEnum
import json, logging, traceback

from app.models.core import DateTimeModelMixin, IDModelMixin, CoreModel, FullCallsign, CallsignSearch

class Band(StrEnum):
    _160M = '160M'
    _80M = '80M'
    _40M = '40M'
    _30M = '30M'
    _20M = '20M'
    _17M = '17M'
    _15M = '15M'
    _12M = '12M'
    _10M = '10M'    

class QsoMode(StrEnum):
    CW = 'CW'
    SSB = 'SSB'
    FT4 = 'FT4'
    FT8 = 'FT8'
    RTTY = 'RTTY'
    PSK = 'PSK'
    PSK31 = 'PSK31'
    PSK63 = 'PSK63'
    PSK125 = 'PSK125'
    JT9 = 'JT9'
    JT65 = 'JT65'
    FM = 'FM'
    DIGI = 'DIGI'
    T10 = 'T10'

DEF_FREQS = {
    Band._160M: {
        QsoMode.FT8: 1840, 
        QsoMode.FT4: 1800, 
        QsoMode.JT65: 1838, 
        None: 1800
        },
    Band._80M: {
        QsoMode.FT8: 3573, 
        QsoMode.FT4: 3575, 
        QsoMode.JT65: 3570, 
        QsoMode.CW: 3500,
        QsoMode.SSB: 3750,
        None: 3500
        },
    Band._40M: {
        QsoMode.FT8: 7074, 
        QsoMode.FT4: 7974.5, 
        QsoMode.JT65: 7076, 
        QsoMode.CW: 7000,
        QsoMode.SSB: 7150,
        None: 7000
        },
    Band._30M: {
        QsoMode.FT8: 10136, 
        QsoMode.FT4: 10140, 
        QsoMode.JT65: 10138, 
        None: 10100
        },
    Band._20M: {
        QsoMode.FT8: 14074, 
        QsoMode.FT4: 14080, 
        QsoMode.JT65: 14076, 
        QsoMode.CW: 14000,
        QsoMode.SSB: 14150,
        None: 14000
        },
    Band._17M: {
        QsoMode.FT8: 18100, 
        QsoMode.FT4: 18104, 
        QsoMode.JT65: 18102, 
        QsoMode.CW: 18068,
        QsoMode.SSB: 18110,
        None: 18068
        },
    Band._15M: {
        QsoMode.FT8: 21074, 
        QsoMode.FT4: 21140, 
        QsoMode.JT65: 21076, 
        QsoMode.CW: 21000,
        QsoMode.SSB: 21200,
        None: 21000
        },
    Band._12M: {
        QsoMode.FT8: 24915, 
        QsoMode.FT4: 24919, 
        QsoMode.JT65: 24917, 
        QsoMode.CW: 24890,
        QsoMode.SSB: 24930,
        None: 24890
        },
    Band._10M: {
        QsoMode.FT8: 28074, 
        QsoMode.FT4: 28180, 
        QsoMode.JT65: 28076, 
        QsoMode.CW: 28000,
        QsoMode.SSB: 28300,
        None: 28000
        }
    }

def def_freq(band: Band, mode: QsoMode) -> float:
    return DEF_FREQS[band][mode if mode in DEF_FREQS[band] else None]

def freq_to_band(freq: float) -> Band:
    if freq <= 2000:
        return Band._160M
    if freq <= 4000:
        return Band._80M
    if freq <= 7300:
        return Band._40M
    if freq <= 10150:
        return Band._30M
    if freq <= 14350:
        return Band._20M
    if freq <= 18168:
        return Band._17M
    if freq <= 21450:
        return Band._15M
    if freq <= 24990:
        return Band._12M
    if freq <= 29700:
        return Band._10M
    return Band._10M

class QsoExtraField(StrEnum):
    CNTY = "CNTY"
    COMMENT = "COMMENT"
    CONTEST_ID = "CONTEST_ID"
    COUNTRY = "COUNTRY"
    CQZ = "CQZ"
    DARC_DOK = "DARC_DOK"
    DISTANCE = "DISTANCE"
    DXCC = "DXCC"
    GRIDSQUARE = "GRIDSQUARE"
    IOTA = "IOTA"
    ITUZ = "ITUZ"
    MY_CITY = "MY_CITY"
    MY_CNTY = "MY_CNTY"
    MY_COUNTRY = "MY_COUNTRY"
    MY_CQ_ZONE = "MY_CQ_ZONE"
    MY_DXCC = "MY_DXCC"
    MY_GRIDSQUARE = "MY_GRIDSQUARE"
    MY_NAME = "MY_NAME"
    MY_POTA_REF = "MY_POTA_REF"
    MY_SOTA_REF = "MY_SOTA_REF"
    MY_STATE = "MY_STATE"
    MY_WWFF_REF = "MY_WWFF_REF"
    NAME = "NAME"
    NOTES = "NOTES"
    OPERATOR = "OPERATOR"
    POTA_REF = "POTA_REF"
    QTH = "QTH"
    SOTA_REF = "SOTA_REF"
    STATE = "STATE"
    PFX = "PFX"
    SRX = "SRX"
    STX = "STX"
    WWFF_REF = "WWFF_REF"

class QsoBase(CoreModel):
    """
    Required fields for valid qso
    also used for qso creation, user_id and log_id is in headers/path
    """
    callsign: FullCallsign
    station_callsign: FullCallsign
    qso_datetime: datetime
    band: Band
    freq: float
    qso_mode: QsoMode
    rst_s: int
    rst_r: int
    extra: Optional[Dict[str, str]]

class QsoUpdate(QsoBase):
    callsign: Optional[FullCallsign]
    station_callsign: Optional[FullCallsign]
    qso_datetime: Optional[datetime]
    band: Optional[Band]
    freq: Optional[float]
    qso_mode: Optional[QsoMode]
    rst_s: Optional[int]
    rst_r: Optional[int]

class QsoInDB(IDModelMixin, DateTimeModelMixin, QsoBase):
    log_id: int

    def __init__(self, **kwargs):

        if isinstance(kwargs.get('extra'), str):
            kwargs['extra'] = json.loads(kwargs['extra'])

        super().__init__(**kwargs)

class QsoPublic(QsoInDB):
    id: str
    log_id: str

class QsoFilter(BaseModel):
    callsign_search: Optional[CallsignSearch]
    band: Optional[Band]
    qso_mode: Optional[QsoMode]
    date_begin: Optional[date]
    date_end: Optional[date]

