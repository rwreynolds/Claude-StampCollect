# enhanced_stamp.py
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional, List

@dataclass
class Stamp:
    scott_number: str
    description: str
    country: Optional[str] = None
    year: Optional[int] = None
    denomination: Optional[str] = None
    color: Optional[str] = None
    condition_grade: str = 'Unknown'
    gum_condition: str = 'Unknown'
    perforation: Optional[str] = None
    used: bool = False
    plate_block: bool = False
    first_day_cover: bool = False
    location: Optional[str] = None
    notes: Optional[str] = None
    qty_mint: Optional[int] = 0
    qty_used: Optional[int] = 0
    catalog_value_mint: Decimal = Decimal('0.00')
    catalog_value_used: Decimal = Decimal('0.00')
    purchase_price: Decimal = Decimal('0.00')
    current_market_value: Decimal = Decimal('0.00')
    want_list: bool = False
    for_sale: bool = False
    date_acquired: Optional[str] = None
    source: Optional[str] = None
    image_path: Optional[str] = None

    def calculate_total_value(self) -> Decimal:
        """Calculate total value based on condition"""
        if self.used:
            qty = self.qty_used if self.qty_used is not None else 0
            return self.catalog_value_used * qty
        qty = self.qty_mint if self.qty_mint is not None else 0
        return self.catalog_value_mint * qty

class StampCollection:
    def __init__(self):
        self.stamps: List[Stamp] = []

    def add_stamp(self, stamp: Stamp):
        """Add a stamp to the collection"""
        self.stamps.append(stamp)

    def list_stamps(self) -> List[Stamp]:
        """Return list of all stamps"""
        return self.stamps