from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.db.database import get_db
from backend.db.models import AdminUser, Tenant
from backend.deps import require_internal
from shared.security import create_access_token
from pydantic import BaseModel

router = APIRouter()

class BotAuthReq(BaseModel): api_key: str

@router.post("/bot")
async def bot_auth(req: BotAuthReq, db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(Tenant).where(Tenant.api_key == req.api_key))
    t = r.scalar_one_or_none()
    if not t or t.status in ("suspended", "expired"):
        raise HTTPException(401, "Invalid or suspended")
    return {"access_token": create_access_token({"tenant_id": t.id, "type": "bot"}), "tenant_id": t.id, "tenant_name": t.name}

@router.post("/master", dependencies=[Depends(require_internal)])
async def master_auth(tg_id: int, db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(AdminUser).where(AdminUser.tg_id == tg_id, AdminUser.is_active == True))
    admin = r.scalar_one_or_none()
    if not admin: raise HTTPException(403, "Not authorized")
    return {"access_token": create_access_token({"tg_id": tg_id, "role": str(admin.role), "type": "master"}), "role": str(admin.role)}

@router.post("/master/init", dependencies=[Depends(require_internal)])
async def init_master(tg_id: int, full_name: str, db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(AdminUser).where(AdminUser.tg_id == tg_id))
    if r.scalar_one_or_none(): return {"ok": True}
    db.add(AdminUser(tg_id=tg_id, full_name=full_name, role="superadmin"))
    await db.commit()
    return {"ok": True}
