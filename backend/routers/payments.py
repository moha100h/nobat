from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.db.database import get_db
from backend.db.models import Payment, Booking
from backend.deps import get_tenant_id
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

router = APIRouter()
class PaymentConfirm(BaseModel): method: str = "manual"; reference: Optional[str] = None

@router.get("/")
async def list_payments(status: Optional[str] = None, tid: int = Depends(get_tenant_id), db: AsyncSession = Depends(get_db)):
    q = select(Payment).where(Payment.tenant_id == tid)
    if status: q = q.where(Payment.status == status)
    r = await db.execute(q.order_by(Payment.created_at.desc())); return r.scalars().all()

@router.get("/{pid}")
async def get_payment(pid: int, tid: int = Depends(get_tenant_id), db: AsyncSession = Depends(get_db)):
    p = await db.get(Payment, pid)
    if not p or p.tenant_id != tid: raise HTTPException(404)
    return p

@router.post("/{pid}/confirm")
async def confirm_payment(pid: int, data: PaymentConfirm, tid: int = Depends(get_tenant_id), db: AsyncSession = Depends(get_db)):
    p = await db.get(Payment, pid)
    if not p or p.tenant_id != tid: raise HTTPException(404)
    if p.status != "pending": raise HTTPException(400, "Already processed")
    p.status = "paid"; p.method = data.method; p.reference = data.reference; p.paid_at = datetime.utcnow()
    b = await db.get(Booking, p.booking_id)
    if b: b.status = "confirmed"; b.updated_at = datetime.utcnow()
    await db.commit(); return {"ok": True}

@router.post("/{pid}/refund")
async def refund_payment(pid: int, tid: int = Depends(get_tenant_id), db: AsyncSession = Depends(get_db)):
    p = await db.get(Payment, pid)
    if not p or p.tenant_id != tid: raise HTTPException(404)
    if p.status != "paid": raise HTTPException(400, "Not paid")
    p.status = "refunded"
    b = await db.get(Booking, p.booking_id)
    if b: b.status = "cancelled"; b.updated_at = datetime.utcnow()
    await db.commit(); return {"ok": True}
