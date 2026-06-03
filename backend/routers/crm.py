from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from backend.db.database import get_db
from backend.db.models import CRMNote, Customer, Booking, Payment
from backend.deps import get_tenant_id
from pydantic import BaseModel

router = APIRouter()
class NoteCreate(BaseModel): customer_id: int; note: str; created_by: int

@router.post("/notes")
async def add_note(data: NoteCreate, tid: int = Depends(get_tenant_id), db: AsyncSession = Depends(get_db)):
    c = await db.get(Customer, data.customer_id)
    if not c or c.tenant_id != tid: raise HTTPException(404)
    n = CRMNote(tenant_id=tid, customer_id=data.customer_id, note=data.note, created_by=data.created_by)
    db.add(n); await db.commit(); await db.refresh(n); return n

@router.get("/notes/{customer_id}")
async def get_notes(customer_id: int, tid: int = Depends(get_tenant_id), db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(CRMNote).where(CRMNote.tenant_id == tid, CRMNote.customer_id == customer_id).order_by(CRMNote.created_at.desc()))
    return r.scalars().all()

@router.get("/dashboard")
async def crm_dashboard(tid: int = Depends(get_tenant_id), db: AsyncSession = Depends(get_db)):
    tc = (await db.execute(select(func.count()).select_from(Customer).where(Customer.tenant_id == tid))).scalar()
    bl = (await db.execute(select(func.count()).select_from(Customer).where(Customer.tenant_id == tid, Customer.is_blocked == True))).scalar()
    tb = (await db.execute(select(func.count()).select_from(Booking).where(Booking.tenant_id == tid))).scalar()
    rev = (await db.execute(select(func.coalesce(func.sum(Payment.amount), 0)).where(Payment.tenant_id == tid, Payment.status == "paid"))).scalar()
    return {"customers": tc, "blocked": bl, "bookings": tb, "revenue": int(rev)}
