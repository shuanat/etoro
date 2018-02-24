from typing import List
from dataclasses import dataclass
from datetime import datetime
import pandas as pd


@dataclass
class Instrument:
    id: int
    name: str
    series: pd.Series


@dataclass
class InstrumentHistory:
    id: List[int]
    name: List[str]
    series: List[pd.Series]


@dataclass
class SpreadInstrument:
    spread: int
    name: List[str]
    id: List[int]


@dataclass
class Tick:
    time: datetime
    price: float
    instrument_name: str
    instrument_id: str
    lot_size: int
