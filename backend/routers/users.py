from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from backend.db.database import get_db
from backend.db.models import Customer, StaffMember
from backend.deps import get_tenant_id
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class CustomerCreate(BaseModel):
    tg_id: int; first_name: str; last_name: str; phone: str
    secondary_phone: Optional[str] = None; city: Optional[str] = None
class CustomerUpdate(BaseModel):
    first_name: Optional[str] = None; last_name: Optional[str] = None; phone: Optional[str] = None
    secondary_phone: Optional[str] = None; city: Optional[str] = None
    internal_notes: Optional[str] = None; tags: Optional[list] = None
class StaffCreate(BaseModel): tg_id: int; full_name: str; role: str = "staff"
class BlacklistSet(BaseModel): blacklist_type: Optional[str] = None; blacklist_reason: Optional[str] = None

@router.post("/customers")
async def create_customer(data: CustomerCreate, tid: int = Depends(get_tenant_id), db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(Customer).where(Customer.tenant_id == tid, Customer.tg_id == data.tg_id))
    if r.scalar_one_or_none(): raise HTTPException(400, "Customer exists")
    c = Customer(tenant_id=tid, **data.model_dump()); db.add(c); await db.commit(); await db.refresh(c); return c

@router.get("/customers")
async def list_customers(search: Optional[str] = None, tid: int = Depends(get_tenant_id), db: AsyncSession = Depends(get_db)):
    q = select(Customer).where(Customer.tenant_id == tid)
    if search: q = q.where(or_(Customer.first_name.ilike(f"%{search}%"), Customer.last_name.ilike(f"%{search}%"), Customer.phone.ilike(f"%{search}%")))
    r = await db.execute(q.order_by(Customer.created_at.desc())); return r.scalars().all()

@router.get("/customers/{cid}")
async def get_customer(cid: int, tid: int = Depends(get_tenant_id), db: AsyncSession = Depends(get_db)):
    c = await db.get(Customer, cid)
    if not c or c.tenant_id != tid: raise HTTPException(404)
    return c

@router.patch("/customers/{cid}")
async def update_customer(cid: int, data: CustomerUpdate, tid: int = Depends(get_tenant_id), db: AsyncSession = Depends(get_db)):
    c = await db.get(Customer, cid)
    if not c or c.tenant_id != tid: raise HTTPException(404)
    for k, v in data.model_dump(exclude_none=True).items(): setattr(c, k, v)
    await db.commit(); return {"ok": True}

@router.post("/customers/{cid}/block")
async def block_customer(cid: int, data: BlacklistSet, tid: int = Depends(get_tenant_id), db: AsyncSession = Depends(get_db)):
    c = await db.get(Customer, cid)
    if not c or c.tenant_id != tid: raise HTTPException(404)
    c.is_blocked = True; c.blacklist_type = data.blacklist_type; c.blacklist_reason = data.blacklist_reason
    await db.commit(); return {"ok": True}

@router.post("/customers/{cid}/unblock")
async def unblock_customer(cid: int, tid: int = Depends(get_tenant_id), db: AsyncSession = Depends(get_db)):
    c = await db.get(Customer, cid)
    if not c or c.tenant_id != tid: raise HTTPException(404)
    c.is_blocked = False; c.blacklist_type = None; c.blacklist_reason = None
    await db.commit(); return {"ok": True}

@router.post("/staff")
async def add_staff(data: StaffCreate, tid: int = Depends(get_tenant_id), db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(StaffMember).where(StaffMember.tenant_id == tid, StaffMember.tg_id == data.tg_id))
    if r.scalar_one_or_none(): raise HTTPException(400, "Staff exists")
    s = StaffMember(tenant_id=tid, **data.model_dump()); db.add(s); await db.commit(); await db.refresh(s); return s

@router.get("/staff")
async def list_staff(tid: int = Depends(get_tenant_id), db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(StaffMember).where(StaffMember.tenant_id == tid, StaffMember.is_active == True)); return r.scalars().all()

@router.delete("/staff/{sid}")
async def remove_staff(sid: int, tid: int = Depends(get_tenant_id), db: AsyncSession = Depends(get_db)):
    s = await db.get(StaffMember, sid)
    if not s or s.tenant_id != tid: raise HTTPException(404)
    s.is_active = False; await db.commit(); return {"ok": True}
