from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from backend.db.database import get_db
from backend.db.models import Tenant, TenantSubscription, Booking, Customer, Payment
from backend.deps import require_internal
from shared.security import generate_api_key
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional

router = APIRouter()

class TenantCreate(BaseModel):
    name: str; bot_token: str; owner_tg_id: int
    subscription_plan: str = "monthly"; subscription_days: int = 30; amount: int = 0

class TenantUpdate(BaseModel):
    name: Optional[str] = None; welcome_message: Optional[str] = None
    contact_info: Optional[str] = None; custom_policies: Optional[str] = None; logo_file_id: Optional[str] = None

class SubscriptionRenew(BaseModel):
    days: int; plan: str; amount: int; admin_tg_id: int; note: Optional[str] = None

@router.post("/", dependencies=[Depends(require_internal)])
async def create_tenant(data: TenantCreate, db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(Tenant).where(Tenant.bot_token == data.bot_token))
    if r.scalar_one_or_none(): raise HTTPException(400, "Bot token already registered")
    expires = datetime.utcnow() + timedelta(days=data.subscription_days)
    t = Tenant(name=data.name, bot_token=data.bot_token, owner_tg_id=data.owner_tg_id,
               status="active", subscription_plan=data.subscription_plan,
               subscription_expires_at=expires, api_key=generate_api_key())
    db.add(t); await db.flush()
    db.add(TenantSubscription(tenant_id=t.id, plan=data.subscription_plan, amount=data.amount, expires_at=expires, created_by=data.owner_tg_id))
    await db.commit(); await db.refresh(t)
    return {"id": t.id, "api_key": t.api_key, "name": t.name, "expires_at": expires.isoformat()}

@router.get("/", dependencies=[Depends(require_internal)])
async def list_tenants(status: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    q = select(Tenant)
    if status: q = q.where(Tenant.status == status)
    r = await db.execute(q.order_by(Tenant.created_at.desc()))
    return [{"id": t.id, "name": t.name, "status": str(t.status), "plan": t.subscription_plan,
             "expires_at": t.subscription_expires_at, "owner_tg_id": t.owner_tg_id,
             "bot_token": t.bot_token, "api_key": t.api_key} for t in r.scalars().all()]

@router.get("/{tid}", dependencies=[Depends(require_internal)])
async def get_tenant(tid: int, db: AsyncSession = Depends(get_db)):
    t = await db.get(Tenant, tid)
    if not t: raise HTTPException(404)
    return {"id": t.id, "name": t.name, "status": str(t.status), "plan": t.subscription_plan,
            "expires_at": t.subscription_expires_at, "owner_tg_id": t.owner_tg_id,
            "welcome_message": t.welcome_message, "contact_info": t.contact_info}

@router.patch("/{tid}", dependencies=[Depends(require_internal)])
async def update_tenant(tid: int, data: TenantUpdate, db: AsyncSession = Depends(get_db)):
    t = await db.get(Tenant, tid)
    if not t: raise HTTPException(404)
    for k, v in data.model_dump(exclude_none=True).items(): setattr(t, k, v)
    t.updated_at = datetime.utcnow(); await db.commit(); return {"ok": True}

@router.post("/{tid}/suspend", dependencies=[Depends(require_internal)])
async def suspend(tid: int, db: AsyncSession = Depends(get_db)):
    t = await db.get(Tenant, tid)
    if not t: raise HTTPException(404)
    t.status = "suspended"; await db.commit(); return {"ok": True}

@router.post("/{tid}/activate", dependencies=[Depends(require_internal)])
async def activate(tid: int, db: AsyncSession = Depends(get_db)):
    t = await db.get(Tenant, tid)
    if not t: raise HTTPException(404)
    t.status = "active"; await db.commit(); return {"ok": True}

@router.post("/{tid}/renew", dependencies=[Depends(require_internal)])
async def renew(tid: int, data: SubscriptionRenew, db: AsyncSession = Depends(get_db)):
    t = await db.get(Tenant, tid)
    if not t: raise HTTPException(404)
    base = max(t.subscription_expires_at or datetime.utcnow(), datetime.utcnow())
    new_exp = base + timedelta(days=data.days)
    t.subscription_expires_at = new_exp; t.subscription_plan = data.plan; t.status = "active"
    db.add(TenantSubscription(tenant_id=tid, plan=data.plan, amount=data.amount, expires_at=new_exp, created_by=data.admin_tg_id, note=data.note))
    await db.commit(); return {"expires_at": new_exp.isoformat()}

@router.get("/{tid}/stats", dependencies=[Depends(require_internal)])
async def stats(tid: int, db: AsyncSession = Depends(get_db)):
    b = (await db.execute(select(func.count()).select_from(Booking).where(Booking.tenant_id == tid))).scalar()
    c = (await db.execute(select(func.count()).select_from(Customer).where(Customer.tenant_id == tid))).scalar()
    rev = (await db.execute(select(func.coalesce(func.sum(Payment.amount), 0)).where(Payment.tenant_id == tid, Payment.status == "paid"))).scalar()
    return {"bookings": b, "customers": c, "revenue": int(rev)}

@router.get("/{tid}/subscriptions", dependencies=[Depends(require_internal)])
async def sub_history(tid: int, db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(TenantSubscription).where(TenantSubscription.tenant_id == tid).order_by(TenantSubscription.started_at.desc()))
    return r.scalars().all()
