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
    JT9 = 'JT9'
    JT65 = 'JT65'

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

