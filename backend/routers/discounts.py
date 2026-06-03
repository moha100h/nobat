from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.db.database import get_db
from backend.db.models import DiscountCode
from backend.deps import get_tenant_id
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

router = APIRouter()
class DiscountCreate(BaseModel):
    code: str; discount_percent: Optional[int] = None; discount_amount: Optional[int] = None
    max_uses: Optional[int] = None; expires_at: Optional[datetime] = None

@router.post("/")
async def create_discount(data: DiscountCreate, tid: int = Depends(get_tenant_id), db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(DiscountCode).where(DiscountCode.tenant_id == tid, DiscountCode.code == data.code))
    if r.scalar_one_or_none(): raise HTTPException(400, "Code exists")
    dc = DiscountCode(tenant_id=tid, **data.model_dump()); db.add(dc); await db.commit(); await db.refresh(dc); return dc

@router.get("/")
async def list_discounts(tid: int = Depends(get_tenant_id), db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(DiscountCode).where(DiscountCode.tenant_id == tid).order_by(DiscountCode.created_at.desc()))
    return r.scalars().all()

@router.delete("/{did}")
async def delete_discount(did: int, tid: int = Depends(get_tenant_id), db: AsyncSession = Depends(get_db)):
    dc = await db.get(DiscountCode, did)
    if not dc or dc.tenant_id != tid: raise HTTPException(404)
    dc.is_active = False; await db.commit(); return {"ok": True}
