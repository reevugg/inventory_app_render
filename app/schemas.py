from pydantic import BaseModel, Field
from typing import Optional, List, Dict

# ----- Settings -----
class SettingsOut(BaseModel):
    exchange_rate_yen_to_bdt: float
    shipping_cost_per_kg_bdt: float
    part_types: List[str]
    part_subtypes: Dict[str, List[str]]
    car_makes: List[str]
    manufacturers: List[str]
    last_recalc: Optional[str] = None

    class Config:
        from_attributes = True

class SettingsUpdate(BaseModel):
    exchange_rate_yen_to_bdt: Optional[float] = None
    shipping_cost_per_kg_bdt: Optional[float] = None
    part_types: Optional[List[str]] = None
    part_subtypes: Optional[Dict[str, List[str]]] = None
    car_makes: Optional[List[str]] = None
    manufacturers: Optional[List[str]] = None

# ----- Suppliers -----
class SupplierCreate(BaseModel):
    supplier_id: str = Field(..., pattern=r"^SUP-[A-Za-z0-9]{8}$")
    name: str
    contact: Optional[str] = None
    notes: Optional[str] = None
    active: bool = True

class SupplierOut(SupplierCreate):
    id: int
    class Config:
        from_attributes = True

# ----- Inventory -----
class InventoryBase(BaseModel):
    part_number: str
    photo_path: Optional[str] = None
    quality: Optional[str] = None
    part_type: Optional[str] = None
    part_subtype: Optional[str] = None
    car_make: Optional[str] = None
    manufacturer: Optional[str] = None
    applicable_models: Optional[str] = None
    purchase_cost_yen: float = 0.0
    weight_kg: float = 0.0
    wholesale_actual_bdt: Optional[float] = None
    retail_actual_bdt: Optional[float] = None
    available_qty: int = 0
    status: str = "In stock"

class InventoryCreate(InventoryBase):
    pass

class InventoryUpdate(BaseModel):
    photo_path: Optional[str] = None
    quality: Optional[str] = None
    part_type: Optional[str] = None
    part_subtype: Optional[str] = None
    car_make: Optional[str] = None
    manufacturer: Optional[str] = None
    applicable_models: Optional[str] = None
    purchase_cost_yen: Optional[float] = None
    weight_kg: Optional[float] = None
    wholesale_actual_bdt: Optional[float] = None
    retail_actual_bdt: Optional[float] = None
    available_qty: Optional[int] = None
    status: Optional[str] = None

class InventoryOut(InventoryBase):
    id: int
    exchange_rate_used: float | None = None
    shipping_per_kg_used: float | None = None
    purchase_cost_bdt: float | None = None
    shipping_cost_bdt: float | None = None
    landed_cost_bdt: float | None = None
    suggested_wholesale_bdt: float | None = None
    suggested_retail_bdt: float | None = None

    class Config:
        from_attributes = True

# ----- Sales -----
class SalesItemIn(BaseModel):
    part_number: str
    channel: str  # Wholesale / Retail
    quantity: int
    price_each_bdt: float

class SalesCartIn(BaseModel):
    items: List[SalesItemIn]
    note: Optional[str] = None

class SalesLogOut(BaseModel):
    id: int
    date: str
    part_number: str
    channel: str
    qty: int
    price_each_bdt: float
    subtotal_bdt: float
    notes: Optional[str]

    class Config:
        from_attributes = True

# ----- Purchases / InTransit -----
class POLineIn(BaseModel):
    part_number: str
    quality: Optional[str] = None
    part_type: Optional[str] = None
    part_subtype: Optional[str] = None
    car_make: Optional[str] = None
    manufacturer: Optional[str] = None
    qty_ordered: int
    purchase_cost_yen: float
    weight_kg: float
    notes: Optional[str] = None
    photo_path: Optional[str] = None

class POIn(BaseModel):
    supplier_id: str
    supplier_name: str
    lines: List[POLineIn]

class POCreated(BaseModel):
    po_id: str
    lines: int

class InTransitOut(BaseModel):
    id: int
    po_id: str
    status: str
    qty_ordered: int
    qty_received: int
    part_number: str

    class Config:
        from_attributes = True
