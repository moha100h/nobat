from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from backend.db.database import get_db
from backend.db.models import Customer, Booking, Payment
from backend.deps import get_tenant_id
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from io import BytesIO, StringIO
from datetime import date
from typing import Optional

router = APIRouter()

@router.get("/customers/export")
async def export_customers(fmt: str = "xlsx", tid: int = Depends(get_tenant_id), db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(Customer).where(Customer.tenant_id == tid)); rows = r.scalars().all()
    if fmt == "csv":
        lines = ["id,first_name,last_name,phone,city,visit_count,total_payments,is_blocked"]
        for c in rows: lines.append(f"{c.id},{c.first_name},{c.last_name},{c.phone},{c.city or ''},{c.visit_count},{c.total_payments},{c.is_blocked}")
        return StreamingResponse(StringIO("\n".join(lines)), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=customers.csv"})
    wb = Workbook(); ws = wb.active; ws.title = "Customers"; ws.append(["ID", "Name", "Phone", "City", "Visits", "Revenue", "Blocked"])
    for c in rows: ws.append([c.id, f"{c.first_name} {c.last_name}", c.phone, c.city or "", c.visit_count, float(c.total_payments or 0), c.is_blocked])
    buf = BytesIO(); wb.save(buf); buf.seek(0)
    return StreamingResponse(buf, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=customers.xlsx"})

@router.get("/bookings/export")
async def export_bookings(fmt: str = "xlsx", tid: int = Depends(get_tenant_id), db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(Booking).where(Booking.tenant_id == tid)); rows = r.scalars().all()
    if fmt == "csv":
        lines = ["id,customer_id,service_id,date,start_time,status,final_price"]
        for b in rows: lines.append(f"{b.id},{b.customer_id},{b.service_id},{b.booking_date},{b.start_time},{b.status},{b.final_price}")
        return StreamingResponse(StringIO("\n".join(lines)), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=bookings.csv"})
    wb = Workbook(); ws = wb.active; ws.title = "Bookings"; ws.append(["ID", "Customer", "Service", "Date", "Time", "Status", "Price"])
    for b in rows: ws.append([b.id, b.customer_id, b.service_id, str(b.booking_date), str(b.start_time), b.status, float(b.final_price or 0)])
    buf = BytesIO(); wb.save(buf); buf.seek(0)
    return StreamingResponse(buf, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=bookings.xlsx"})

@router.get("/summary")
async def summary(from_date: Optional[date] = None, to_date: Optional[date] = None, tid: int = Depends(get_tenant_id), db: AsyncSession = Depends(get_db)):
    qb = select(func.count()).select_from(Booking).where(Booking.tenant_id == tid)
    qr = select(func.coalesce(func.sum(Payment.amount), 0)).where(Payment.tenant_id == tid, Payment.status == "paid")
    if from_date: qb = qb.where(Booking.booking_date >= from_date); qr = qr.where(Payment.paid_at >= from_date)
    if to_date: qb = qb.where(Booking.booking_date <= to_date); qr = qr.where(Payment.paid_at <= to_date)
    return {"bookings": (await db.execute(qb)).scalar(), "revenue": int((await db.execute(qr)).scalar())}
