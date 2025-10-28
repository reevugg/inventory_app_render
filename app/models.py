from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, JSON
from .db import Base

class Settings(Base):
    __tablename__ = "settings"
    id = Column(Integer, primary_key=True, index=True)
    exchange_rate_yen_to_bdt = Column(Float, default=0.0)
    shipping_cost_per_kg_bdt = Column(Float, default=0.0)
    part_types = Column(JSON, default=list)
    part_subtypes = Column(JSON, default=dict)  # {type: [subtypes]}
    car_makes = Column(JSON, default=list)
    manufacturers = Column(JSON, default=list)
    last_recalc = Column(DateTime, nullable=True)

class Supplier(Base):
    __tablename__ = "suppliers"
    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(String, unique=True, index=True)
    name = Column(String, nullable=False)
    contact = Column(String, nullable=True)
    notes = Column(String, nullable=True)
    active = Column(Boolean, default=True)

class Inventory(Base):
    __tablename__ = "inventory"
    id = Column(Integer, primary_key=True, index=True)
    part_number = Column(String, unique=True, index=True)
    photo_path = Column(String, nullable=True)
    quality = Column(String, nullable=True)
    part_type = Column(String, nullable=True)
    part_subtype = Column(String, nullable=True)
    car_make = Column(String, nullable=True)
    manufacturer = Column(String, nullable=True)
    applicable_models = Column(String, nullable=True)
    purchase_cost_yen = Column(Float, default=0.0)
    weight_kg = Column(Float, default=0.0)
    exchange_rate_used = Column(Float, default=0.0)
    shipping_per_kg_used = Column(Float, default=0.0)
    purchase_cost_bdt = Column(Float, nullable=True)
    shipping_cost_bdt = Column(Float, nullable=True)
    landed_cost_bdt = Column(Float, nullable=True)
    suggested_wholesale_bdt = Column(Float, nullable=True)
    suggested_retail_bdt = Column(Float, nullable=True)
    wholesale_actual_bdt = Column(Float, nullable=True)
    retail_actual_bdt = Column(Float, nullable=True)
    available_qty = Column(Integer, default=0)
    sold_wholesale_qty = Column(Integer, default=0)
    sold_retail_qty = Column(Integer, default=0)
    status = Column(String, default="In stock")
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

class SalesLog(Base):
    __tablename__ = "sales_log"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime)
    part_number = Column(String, index=True)
    channel = Column(String)  # Wholesale / Retail
    qty = Column(Integer)
    price_each_bdt = Column(Float)
    subtotal_bdt = Column(Float)
    notes = Column(String, nullable=True)

class InTransit(Base):
    __tablename__ = "intransit"
    id = Column(Integer, primary_key=True, index=True)
    po_id = Column(String, index=True)
    order_date = Column(DateTime)
    supplier_id = Column(String)
    supplier_name = Column(String)
    part_number = Column(String, index=True)
    quality = Column(String)
    part_type = Column(String)
    part_subtype = Column(String)
    car_make = Column(String)
    manufacturer = Column(String)
    qty_ordered = Column(Integer)
    purchase_cost_yen = Column(Float)
    weight_kg = Column(Float)
    exchange_rate_used = Column(Float)
    shipping_per_kg_used = Column(Float)
    landed_cost_bdt = Column(Float)
    status = Column(String, default="Shipping")
    qty_received = Column(Integer, default=0)
    notes = Column(String, nullable=True)
    photo_path = Column(String, nullable=True)
