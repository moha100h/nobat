from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.db.database import get_db
from backend.db.models import ServiceCategory, Service, ServiceSchedule, WorkingHour, Holiday
from backend.deps import get_tenant_id
from pydantic import BaseModel
from typing import Optional
from datetime import time, date

router = APIRouter()
def pt(s): h, m = s.split(":"); return time(int(h), int(m))

class CategoryCreate(BaseModel): name: str; description: Optional[str] = None; sort_order: int = 0
class ServiceCreate(BaseModel):
    category_id: int; name: str; description: Optional[str] = None
    duration_minutes: int = 60; price: int = 0; capacity: int = 1
    requires_payment: bool = False; sort_order: int = 0
class ScheduleCreate(BaseModel): weekday: int; start_time: str; end_time: str; slot_duration: int = 60
class WorkingHourSet(BaseModel): weekday: int; open_time: str; close_time: str; is_open: bool = True
class HolidayCreate(BaseModel): holiday_date: date; description: Optional[str] = None

@router.get("/categories")
async def list_categories(tid: int = Depends(get_tenant_id), db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(ServiceCategory).where(ServiceCategory.tenant_id == tid, ServiceCategory.is_active == True).order_by(ServiceCategory.sort_order))
    return r.scalars().all()

@router.post("/categories")
async def create_category(data: CategoryCreate, tid: int = Depends(get_tenant_id), db: AsyncSession = Depends(get_db)):
    cat = ServiceCategory(tenant_id=tid, **data.model_dump()); db.add(cat); await db.commit(); await db.refresh(cat); return cat

@router.delete("/categories/{cid}")
async def delete_category(cid: int, tid: int = Depends(get_tenant_id), db: AsyncSession = Depends(get_db)):
    cat = await db.get(ServiceCategory, cid)
    if not cat or cat.tenant_id != tid: raise HTTPException(404)
    cat.is_active = False; await db.commit(); return {"ok": True}

@router.get("/")
async def list_services(category_id: Optional[int] = None, tid: int = Depends(get_tenant_id), db: AsyncSession = Depends(get_db)):
    q = select(Service).where(Service.tenant_id == tid, Service.is_active == True)
    if category_id: q = q.where(Service.category_id == category_id)
    r = await db.execute(q.order_by(Service.sort_order)); return r.scalars().all()

@router.post("/")
async def create_service(data: ServiceCreate, tid: int = Depends(get_tenant_id), db: AsyncSession = Depends(get_db)):
    svc = Service(tenant_id=tid, **data.model_dump()); db.add(svc); await db.commit(); await db.refresh(svc); return svc

@router.patch("/{sid}")
async def update_service(sid: int, data: dict, tid: int = Depends(get_tenant_id), db: AsyncSession = Depends(get_db)):
    svc = await db.get(Service, sid)
    if not svc or svc.tenant_id != tid: raise HTTPException(404)
    for k, v in data.items():
        if hasattr(svc, k): setattr(svc, k, v)
    await db.commit(); return {"ok": True}

@router.delete("/{sid}")
async def delete_service(sid: int, tid: int = Depends(get_tenant_id), db: AsyncSession = Depends(get_db)):
    svc = await db.get(Service, sid)
    if not svc or svc.tenant_id != tid: raise HTTPException(404)
    svc.is_active = False; await db.commit(); return {"ok": True}

@router.post("/{sid}/schedules")
async def add_schedule(sid: int, data: ScheduleCreate, tid: int = Depends(get_tenant_id), db: AsyncSession = Depends(get_db)):
    svc = await db.get(Service, sid)
    if not svc or svc.tenant_id != tid: raise HTTPException(404)
    sch = ServiceSchedule(service_id=sid, weekday=data.weekday, start_time=pt(data.start_time), end_time=pt(data.end_time), slot_duration=data.slot_duration)
    db.add(sch); await db.commit(); await db.refresh(sch); return sch

@router.get("/{sid}/schedules")
async def get_schedules(sid: int, db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(ServiceSchedule).where(ServiceSchedule.service_id == sid, ServiceSchedule.is_active == True))
    return r.scalars().all()

@router.post("/working-hours")
async def set_working_hour(data: WorkingHourSet, tid: int = Depends(get_tenant_id), db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(WorkingHour).where(WorkingHour.tenant_id == tid, WorkingHour.weekday == data.weekday))
    wh = r.scalar_one_or_none()
    if wh: wh.open_time = pt(data.open_time); wh.close_time = pt(data.close_time); wh.is_open = data.is_open
    else: db.add(WorkingHour(tenant_id=tid, weekday=data.weekday, open_time=pt(data.open_time), close_time=pt(data.close_time), is_open=data.is_open))
    await db.commit(); return {"ok": True}

@router.get("/working-hours")
async def get_working_hours(tid: int = Depends(get_tenant_id), db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(WorkingHour).where(WorkingHour.tenant_id == tid).order_by(WorkingHour.weekday)); return r.scalars().all()

@router.post("/holidays")
async def add_holiday(data: HolidayCreate, tid: int = Depends(get_tenant_id), db: AsyncSession = Depends(get_db)):
    db.add(Holiday(tenant_id=tid, holiday_date=data.holiday_date, description=data.description))
    try: await db.commit()
    except Exception: await db.rollback(); raise HTTPException(400, "Already exists")
    return {"ok": True}

@router.delete("/holidays/{hid}")
async def delete_holiday(hid: int, tid: int = Depends(get_tenant_id), db: AsyncSession = Depends(get_db)):
    h = await db.get(Holiday, hid)
    if not h or h.tenant_id != tid: raise HTTPException(404)
    await db.delete(h); await db.commit(); return {"ok": True}

@router.get("/holidays")
async def list_holidays(tid: int = Depends(get_tenant_id), db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(Holiday).where(Holiday.tenant_id == tid).order_by(Holiday.holiday_date)); return r.scalars().all()
