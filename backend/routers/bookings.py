from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.db.database import get_db
from backend.db.models import Booking, Service, ServiceSchedule, WorkingHour, Holiday, Customer, WaitingList, Payment, DiscountCode
from backend.deps import get_tenant_id
from pydantic import BaseModel
from typing import Optional
from datetime import date, time, datetime, timedelta

router = APIRouter()
def pt(s): h, m = s.split(":"); return time(int(h), int(m))

class SlotQuery(BaseModel): service_id: int; date: date
class BookingCreate(BaseModel):
    service_id: int; booking_date: date; start_time: str; customer_id: int
    notes: Optional[str] = None; discount_code: Optional[str] = None
class StatusUpdate(BaseModel): status: str

async def _slots(db, tid, service_id, d):
    svc = await db.get(Service, service_id)
    if not svc or not svc.is_active or svc.tenant_id != tid: return []
    r = await db.execute(select(Holiday).where(Holiday.tenant_id == tid, Holiday.holiday_date == d))
    if r.scalar_one_or_none(): return []
    wd = d.weekday()
    r = await db.execute(select(WorkingHour).where(WorkingHour.tenant_id == tid, WorkingHour.weekday == wd))
    wh = r.scalar_one_or_none()
    if wh and not wh.is_open: return []
    r = await db.execute(select(ServiceSchedule).where(ServiceSchedule.service_id == service_id, ServiceSchedule.weekday == wd, ServiceSchedule.is_active == True))
    schedules = r.scalars().all()
    if not schedules: return []
    r = await db.execute(select(Booking).where(Booking.tenant_id == tid, Booking.service_id == service_id, Booking.booking_date == d, Booking.status.in_(["pending", "confirmed"])))
    counts = {}
    for b in r.scalars().all(): k = (b.start_time, b.end_time); counts[k] = counts.get(k, 0) + 1
    slots = []
    for sch in schedules:
        cur = datetime.combine(d, sch.start_time); end = datetime.combine(d, sch.end_time); dur = timedelta(minutes=sch.slot_duration)
        while cur + dur <= end:
            st = cur.time(); et = (cur + dur).time(); avail = svc.capacity - counts.get((st, et), 0)
            if avail > 0: slots.append({"start": st.strftime("%H:%M"), "end": et.strftime("%H:%M"), "available": avail})
            cur += dur
    return slots

@router.post("/slots")
async def get_slots(data: SlotQuery, tid: int = Depends(get_tenant_id), db: AsyncSession = Depends(get_db)):
    if data.date < date.today(): raise HTTPException(400, "Past date")
    return {"date": str(data.date), "slots": await _slots(db, tid, data.service_id, data.date)}

@router.post("/")
async def create_booking(data: BookingCreate, tid: int = Depends(get_tenant_id), db: AsyncSession = Depends(get_db)):
    cust = await db.get(Customer, data.customer_id)
    if not cust or cust.tenant_id != tid: raise HTTPException(404, "Customer not found")
    if cust.is_blocked: raise HTTPException(403, "Customer blocked")
    svc = await db.get(Service, data.service_id)
    if not svc or not svc.is_active or svc.tenant_id != tid: raise HTTPException(400, "Service unavailable")
    slots = await _slots(db, tid, data.service_id, data.booking_date)
    slot = next((s for s in slots if s["start"] == data.start_time), None)
    if not slot: raise HTTPException(409, "Slot not available")
    discount_amount = 0; discount_id = None
    if data.discount_code:
        r = await db.execute(select(DiscountCode).where(DiscountCode.tenant_id == tid, DiscountCode.code == data.discount_code, DiscountCode.is_active == True))
        dc = r.scalar_one_or_none()
        if dc:
            if dc.expires_at and dc.expires_at < datetime.utcnow(): raise HTTPException(400, "Discount expired")
            if dc.max_uses and dc.used_count >= dc.max_uses: raise HTTPException(400, "Discount exhausted")
            if dc.discount_percent: discount_amount = int(float(svc.price) * dc.discount_percent / 100)
            elif dc.discount_amount: discount_amount = int(dc.discount_amount)
            dc.used_count += 1; discount_id = dc.id
    final_price = max(0, int(float(svc.price)) - discount_amount)
    b = Booking(tenant_id=tid, customer_id=data.customer_id, service_id=data.service_id,
                booking_date=data.booking_date, start_time=pt(data.start_time), end_time=pt(slot["end"]),
                status="pending" if svc.requires_payment else "confirmed",
                price=svc.price, discount_amount=discount_amount, final_price=final_price,
                discount_code_id=discount_id, notes=data.notes)
    db.add(b); await db.flush()
    if svc.requires_payment: db.add(Payment(tenant_id=tid, booking_id=b.id, customer_id=data.customer_id, amount=final_price))
    await db.commit(); await db.refresh(b)
    return {"id": b.id, "status": b.status, "final_price": final_price}

@router.get("/")
async def list_bookings(d: Optional[date] = None, status: Optional[str] = None, tid: int = Depends(get_tenant_id), db: AsyncSession = Depends(get_db)):
    q = select(Booking).where(Booking.tenant_id == tid)
    if d: q = q.where(Booking.booking_date == d)
    if status: q = q.where(Booking.status == status)
    r = await db.execute(q.order_by(Booking.booking_date, Booking.start_time)); return r.scalars().all()

@router.get("/{bid}")
async def get_booking(bid: int, tid: int = Depends(get_tenant_id), db: AsyncSession = Depends(get_db)):
    b = await db.get(Booking, bid)
    if not b or b.tenant_id != tid: raise HTTPException(404)
    return b

@router.patch("/{bid}/status")
async def update_status(bid: int, data: StatusUpdate, tid: int = Depends(get_tenant_id), db: AsyncSession = Depends(get_db)):
    b = await db.get(Booking, bid)
    if not b or b.tenant_id != tid: raise HTTPException(404)
    allowed = {"pending": ["confirmed", "cancelled"], "confirmed": ["completed", "cancelled", "no_show"], "completed": [], "cancelled": [], "no_show": []}
    if data.status not in allowed.get(b.status, []): raise HTTPException(400, f"Cannot {b.status}->{data.status}")
    b.status = data.status; b.updated_at = datetime.utcnow()
    if data.status == "completed":
        c = await db.get(Customer, b.customer_id)
        if c: c.visit_count += 1; c.last_visit = datetime.utcnow(); c.total_payments = float(c.total_payments or 0) + float(b.final_price or 0)
    await db.commit(); return {"ok": True}

@router.delete("/{bid}")
async def cancel_booking(bid: int, tid: int = Depends(get_tenant_id), db: AsyncSession = Depends(get_db)):
    b = await db.get(Booking, bid)
    if not b or b.tenant_id != tid: raise HTTPException(404)
    if b.status in ("completed", "cancelled"): raise HTTPException(400, "Cannot cancel")
    b.status = "cancelled"; b.updated_at = datetime.utcnow(); await db.commit()
    r = await db.execute(select(WaitingList).where(WaitingList.tenant_id == tid, WaitingList.service_id == b.service_id, WaitingList.requested_date == b.booking_date, WaitingList.notified == False).limit(1))
    wl = r.scalar_one_or_none()
    if wl: wl.notified = True; await db.commit(); return {"ok": True, "notify_customer_id": wl.customer_id}
    return {"ok": True}

@router.post("/waiting-list")
async def join_waiting(service_id: int, requested_date: date, customer_id: int, tid: int = Depends(get_tenant_id), db: AsyncSession = Depends(get_db)):
    db.add(WaitingList(tenant_id=tid, customer_id=customer_id, service_id=service_id, requested_date=requested_date))
    await db.commit(); return {"ok": True}
