from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import time, logging, os
from backend.db.database import engine, Base
from backend.routers import auth, tenants, services, bookings, users, payments, crm, reports, backups, discounts, tickets

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-8s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="Nobat SaaS API", version="1.0.0", docs_url=None, redoc_url=None)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.middleware("http")
async def log_req(request: Request, call_next):
    t0 = time.time()
    r = await call_next(request)
    logger.info(f"{request.method} {request.url.path} {r.status_code} {time.time()-t0:.3f}s")
    return r

@app.on_event("startup")
async def startup():
    os.makedirs("/app/uploads", exist_ok=True)
    os.makedirs("/app/backups", exist_ok=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("DB tables ready")

@app.get("/health")
async def health(): return {"status": "ok"}

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(tenants.router, prefix="/api/v1/tenants", tags=["tenants"])
app.include_router(services.router, prefix="/api/v1/services", tags=["services"])
app.include_router(bookings.router, prefix="/api/v1/bookings", tags=["bookings"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(payments.router, prefix="/api/v1/payments", tags=["payments"])
app.include_router(crm.router, prefix="/api/v1/crm", tags=["crm"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["reports"])
app.include_router(backups.router, prefix="/api/v1/backups", tags=["backups"])
app.include_router(discounts.router, prefix="/api/v1/discounts", tags=["discounts"])
app.include_router(tickets.router, prefix="/api/v1/tickets", tags=["tickets"])
