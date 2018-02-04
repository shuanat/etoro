from typing import List
import pandas as pd
from dataclasses import dataclass


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