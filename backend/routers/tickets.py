from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.db.database import get_db
from backend.db.models import SupportTicket, TicketMessage
from backend.deps import get_tenant_id
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

router = APIRouter()
class TicketCreate(BaseModel): customer_tg_id: int; subject: str
class MessageCreate(BaseModel): sender_tg_id: int; is_staff: bool = False; message: str
class TicketUpdate(BaseModel): status: str

@router.post("/")
async def create_ticket(data: TicketCreate, tid: int = Depends(get_tenant_id), db: AsyncSession = Depends(get_db)):
    t = SupportTicket(tenant_id=tid, customer_tg_id=data.customer_tg_id, subject=data.subject)
    db.add(t); await db.commit(); await db.refresh(t); return t

@router.get("/")
async def list_tickets(status: Optional[str] = None, tid: int = Depends(get_tenant_id), db: AsyncSession = Depends(get_db)):
    q = select(SupportTicket).where(SupportTicket.tenant_id == tid)
    if status: q = q.where(SupportTicket.status == status)
    r = await db.execute(q.order_by(SupportTicket.created_at.desc())); return r.scalars().all()

@router.get("/{ticket_id}")
async def get_ticket(ticket_id: int, tid: int = Depends(get_tenant_id), db: AsyncSession = Depends(get_db)):
    t = await db.get(SupportTicket, ticket_id)
    if not t or t.tenant_id != tid: raise HTTPException(404)
    return t

@router.patch("/{ticket_id}")
async def update_ticket(ticket_id: int, data: TicketUpdate, tid: int = Depends(get_tenant_id), db: AsyncSession = Depends(get_db)):
    t = await db.get(SupportTicket, ticket_id)
    if not t or t.tenant_id != tid: raise HTTPException(404)
    t.status = data.status; t.updated_at = datetime.utcnow(); await db.commit(); return {"ok": True}

@router.post("/{ticket_id}/messages")
async def add_message(ticket_id: int, data: MessageCreate, tid: int = Depends(get_tenant_id), db: AsyncSession = Depends(get_db)):
    t = await db.get(SupportTicket, ticket_id)
    if not t or t.tenant_id != tid: raise HTTPException(404)
    m = TicketMessage(ticket_id=ticket_id, sender_tg_id=data.sender_tg_id, is_staff=data.is_staff, message=data.message)
    db.add(m); await db.commit(); await db.refresh(m); return m

@router.get("/{ticket_id}/messages")
async def get_messages(ticket_id: int, tid: int = Depends(get_tenant_id), db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(TicketMessage).where(TicketMessage.ticket_id == ticket_id).order_by(TicketMessage.created_at))
    return r.scalars().all()
