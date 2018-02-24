from dataclasses import dataclass


@dataclass
class InstrumentList:
    instrument_id: str
    instrument_display_name: str
    stock_industry_id: int
    symbol_full: str
    lot_size: int
