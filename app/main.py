from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime

from .db import Base, engine, get_db
from . import models, schemas
from .utils.formulas import compute_costs

app = FastAPI(title="Inventory Management API", version="1.0.0")

# CORS (adjust origins for your domain)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables on startup (simple for v1; you can switch to Alembic later)
Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {"ok": True, "service": "inventory-app", "version": "1.0.0"}

# ---------- Settings ----------
@app.get("/settings", response_model=schemas.SettingsOut)
def get_settings(db: Session = Depends(get_db)):
    s = db.query(models.Settings).first()
    if not s:
        s = models.Settings(
            exchange_rate_yen_to_bdt=0.0,
            shipping_cost_per_kg_bdt=0.0,
            part_types=[],
            part_subtypes={},
            car_makes=[],
            manufacturers=[],
            last_recalc=None,
        )
        db.add(s)
        db.commit()
        db.refresh(s)
    return s

@app.put("/settings", response_model=schemas.SettingsOut)
def update_settings(payload: schemas.SettingsUpdate, db: Session = Depends(get_db)):
    s = db.query(models.Settings).first()
    if not s:
        s = models.Settings()
        db.add(s)

    if payload.exchange_rate_yen_to_bdt is not None:
        s.exchange_rate_yen_to_bdt = payload.exchange_rate_yen_to_bdt
    if payload.shipping_cost_per_kg_bdt is not None:
        s.shipping_cost_per_kg_bdt = payload.shipping_cost_per_kg_bdt
    if payload.part_types is not None:
        s.part_types = payload.part_types
    if payload.part_subtypes is not None:
        s.part_subtypes = payload.part_subtypes
    if payload.car_makes is not None:
        s.car_makes = payload.car_makes
    if payload.manufacturers is not None:
        s.manufacturers = payload.manufacturers

    db.commit()
    db.refresh(s)
    return s

@app.post("/settings/recalc", response_model=dict)
def recalc_all(db: Session = Depends(get_db)):
    s = db.query(models.Settings).first()
    if not s:
        raise HTTPException(400, "Settings not configured")

    inv = db.query(models.Inventory).all()
    for row in inv:
        c = compute_costs(
            purchase_cost_yen=row.purchase_cost_yen or 0.0,
            weight_kg=row.weight_kg or 0.0,
            exchange_rate=s.exchange_rate_yen_to_bdt or 0.0,
            shipping_per_kg=s.shipping_cost_per_kg_bdt or 0.0,
        )
        row.exchange_rate_used = s.exchange_rate_yen_to_bdt
        row.shipping_per_kg_used = s.shipping_cost_per_kg_bdt
        row.purchase_cost_bdt = c["purchase_cost_bdt"]
        row.shipping_cost_bdt = c["shipping_cost_bdt"]
        row.landed_cost_bdt = c["landed_cost_bdt"]
        row.suggested_wholesale_bdt = c["suggested_wholesale_bdt"]
        row.suggested_retail_bdt = c["suggested_retail_bdt"]
        row.updated_at = datetime.utcnow()

    s.last_recalc = datetime.utcnow()
    db.commit()
    return {"recalculated": len(inv)}

# ---------- Suppliers ----------
@app.post("/suppliers", response_model=schemas.SupplierOut)
def create_supplier(payload: schemas.SupplierCreate, db: Session = Depends(get_db)):
    sup = models.Supplier(**payload.model_dump())
    db.add(sup)
    db.commit()
    db.refresh(sup)
    return sup

@app.get("/suppliers", response_model=list[schemas.SupplierOut])
def list_suppliers(active_only: bool | None = None, db: Session = Depends(get_db)):
    q = db.query(models.Supplier)
    if active_only is True:
        q = q.filter(models.Supplier.active.is_(True))
    return q.order_by(models.Supplier.name.asc()).all()

# ---------- Inventory ----------
@app.post("/inventory", response_model=schemas.InventoryOut)
def add_part(payload: schemas.InventoryCreate, db: Session = Depends(get_db)):
    exists = db.query(models.Inventory).filter_by(part_number=payload.part_number).first()
    if exists:
        raise HTTPException(409, "Part number already exists")

    s = db.query(models.Settings).first()
    if not s:
        raise HTTPException(400, "Settings not configured")

    costs = compute_costs(
        payload.purchase_cost_yen, payload.weight_kg,
        s.exchange_rate_yen_to_bdt, s.shipping_cost_per_kg_bdt
    )

    row = models.Inventory(
        **payload.model_dump(),
        exchange_rate_used=s.exchange_rate_yen_to_bdt,
        shipping_per_kg_used=s.shipping_cost_per_kg_bdt,
        purchase_cost_bdt=costs["purchase_cost_bdt"],
        shipping_cost_bdt=costs["shipping_cost_bdt"],
        landed_cost_bdt=costs["landed_cost_bdt"],
        suggested_wholesale_bdt=costs["suggested_wholesale_bdt"],
        suggested_retail_bdt=costs["suggested_retail_bdt"],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row

@app.get("/inventory", response_model=list[schemas.InventoryOut])
def search_inventory(
    part_number: str | None = None,
    applicable_models: str | None = None,
    status: str | None = None,
    part_type: str | None = None,
    part_subtype: str | None = None,
    car_make: str | None = None,
    manufacturer: str | None = None,
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db),
):
    q = db.query(models.Inventory)
    if part_number:
        q = q.filter(models.Inventory.part_number.ilike(f"%{part_number}%"))
    if applicable_models:
        q = q.filter(models.Inventory.applicable_models.ilike(f"%{applicable_models}%"))
    if status:
        q = q.filter(models.Inventory.status == status)
    if part_type:
        q = q.filter(models.Inventory.part_type == part_type)
    if part_subtype:
        q = q.filter(models.Inventory.part_subtype == part_subtype)
    if car_make:
        q = q.filter(models.Inventory.car_make == car_make)
    if manufacturer:
        q = q.filter(models.Inventory.manufacturer == manufacturer)

    q = q.order_by(models.Inventory.part_number.asc())
    offset = (page - 1) * page_size
    return q.offset(offset).limit(page_size).all()

@app.get("/inventory/{part_number}", response_model=schemas.InventoryOut)
def get_part(part_number: str, db: Session = Depends(get_db)):
    row = db.query(models.Inventory).filter_by(part_number=part_number).first()
    if not row:
        raise HTTPException(404, "Not found")
    return row

@app.put("/inventory/{part_number}", response_model=schemas.InventoryOut)
def update_part(part_number: str, payload: schemas.InventoryUpdate, db: Session = Depends(get_db)):
    row = db.query(models.Inventory).filter_by(part_number=part_number).first()
    if not row:
        raise HTTPException(404, "Not found")
    data = payload.model_dump(exclude_none=True)
    for k, v in data.items():
        setattr(row, k, v)
    row.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(row)
    return row

# ---------- Sales ----------
@app.post("/sales/finalize", response_model=list[schemas.SalesLogOut])
def finalize_sale(payload: schemas.SalesCartIn, db: Session = Depends(get_db)):
    logs: list[models.SalesLog] = []

    # stock checks first
    for item in payload.items:
        inv = db.query(models.Inventory).filter_by(part_number=item.part_number).with_for_update().first()
        if not inv:
            raise HTTPException(404, f"Part {item.part_number} not found")
        if item.quantity <= 0 or item.price_each_bdt <= 0:
            raise HTTPException(400, f"Invalid qty/price for {item.part_number}")
        if inv.available_qty < item.quantity:
            raise HTTPException(400, f"Insufficient stock for {item.part_number}")

    # apply changes
    for item in payload.items:
        inv = db.query(models.Inventory).filter_by(part_number=item.part_number).with_for_update().first()
        inv.available_qty -= item.quantity
        if item.channel == "Wholesale":
            inv.sold_wholesale_qty = (inv.sold_wholesale_qty or 0) + item.quantity
        else:
            inv.sold_retail_qty = (inv.sold_retail_qty or 0) + item.quantity
        if inv.available_qty == 0:
            inv.status = "Out of stock"
        inv.updated_at = datetime.utcnow()

        log = models.SalesLog(
            date=datetime.utcnow(),
            part_number=item.part_number,
            channel=item.channel,
            qty=item.quantity,
            price_each_bdt=item.price_each_bdt,
            subtotal_bdt=item.quantity * item.price_each_bdt,
            notes=payload.note or "",
        )
        db.add(log)
        logs.append(log)

    db.commit()
    for l in logs:
        db.refresh(l)
    return logs

# ---------- Purchases / In-Transit ----------
@app.post("/po", response_model=schemas.POCreated)
def create_po(payload: schemas.POIn, db: Session = Depends(get_db)):
    from uuid import uuid4
    po_id = f"PO-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid4())[:8]}"

    s = db.query(models.Settings).first()
    if not s:
        raise HTTPException(400, "Settings not configured")

    rows = []
    for line in payload.lines:
        costs = compute_costs(
            line.purchase_cost_yen, line.weight_kg,
            s.exchange_rate_yen_to_bdt, s.shipping_cost_per_kg_bdt
        )
        it = models.InTransit(
            po_id=po_id,
            order_date=datetime.utcnow(),
            supplier_id=payload.supplier_id,
            supplier_name=payload.supplier_name,
            part_number=line.part_number,
            quality=line.quality,
            part_type=line.part_type,
            part_subtype=line.part_subtype,
            car_make=line.car_make,
            manufacturer=line.manufacturer,
            qty_ordered=line.qty_ordered,
            purchase_cost_yen=line.purchase_cost_yen,
            weight_kg=line.weight_kg,
            exchange_rate_used=s.exchange_rate_yen_to_bdt,
            shipping_per_kg_used=s.shipping_cost_per_kg_bdt,
            landed_cost_bdt=costs["landed_cost_bdt"],
            status="Shipping",
            qty_received=0,
            notes=line.notes,
            photo_path=line.photo_path,
        )
        db.add(it)
        rows.append(it)

    db.commit()
    for r in rows:
        db.refresh(r)
    return schemas.POCreated(po_id=po_id, lines=len(rows))

@app.post("/intransit/{row_id}/receive", response_model=schemas.InTransitOut)
def receive(row_id: int, qty_received: int, db: Session = Depends(get_db)):
    if qty_received < 0:
        raise HTTPException(400, "qty_received cannot be negative")

    row = db.query(models.InTransit).filter_by(id=row_id).with_for_update().first()
    if not row:
        raise HTTPException(404, "Not found")
    if row.status != "Shipping":
        raise HTTPException(400, "Row not in Shipping state")
    if qty_received + (row.qty_received or 0) > row.qty_ordered:
        raise HTTPException(400, "Cannot receive more than ordered")

    # ensure inventory exists or create
    inv = db.query(models.Inventory).filter_by(part_number=row.part_number).with_for_update().first()
    if not inv:
        inv = models.Inventory(
            part_number=row.part_number,
            quality=row.quality,
            part_type=row.part_type,
            part_subtype=row.part_subtype,
            car_make=row.car_make,
            manufacturer=row.manufacturer,
            applicable_models="",
            purchase_cost_yen=row.purchase_cost_yen,
            weight_kg=row.weight_kg,
            exchange_rate_used=row.exchange_rate_used,
            shipping_per_kg_used=row.shipping_per_kg_used,
            purchase_cost_bdt=None,
            shipping_cost_bdt=None,
            landed_cost_bdt=row.landed_cost_bdt,
            suggested_wholesale_bdt=None,
            suggested_retail_bdt=None,
            wholesale_actual_bdt=None,
            retail_actual_bdt=None,
            available_qty=0,
            sold_wholesale_qty=0,
            sold_retail_qty=0,
            status="In stock",
            photo_path=row.photo_path,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(inv)

    inv.available_qty = (inv.available_qty or 0) + qty_received
    inv.status = "In stock" if inv.available_qty > 0 else inv.status
    inv.updated_at = datetime.utcnow()

    row.qty_received = (row.qty_received or 0) + qty_received
    if row.qty_received == row.qty_ordered:
        row.status = "Received"

    db.commit()
    db.refresh(row)
    return row
