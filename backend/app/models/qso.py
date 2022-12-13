from typing import Optional, Dict
from datetime import datetime
from enum import StrEnum
import json, logging, traceback

from app.models.core import DateTimeModelMixin, IDModelMixin, CoreModel, FullCallsign

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

class QsoBase(CoreModel):
    """
    Requested fields for valid qso
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
    name: Optional[str]
    qth: Optional[str]
    gridsquare: Optional[str]
    extra: Optional[dict]
    comment: Optional[str]

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
