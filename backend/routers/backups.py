from fastapi import APIRouter, Depends, HTTPException
from backend.deps import require_internal
from fastapi.responses import StreamingResponse
from io import BytesIO
import os, subprocess, datetime

router = APIRouter()

@router.post("/db", dependencies=[Depends(require_internal)])
async def backup_db():
    d = os.environ.get("BACKUP_DIR", "/app/backups"); os.makedirs(d, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S"); fp = os.path.join(d, f"nobat_{ts}.sql")
    db_url = os.environ.get("DATABASE_URL", "").replace("+asyncpg", "")
    p = subprocess.run(["pg_dump", db_url, "-f", fp], capture_output=True, text=True)
    if p.returncode != 0: raise HTTPException(500, f"Backup failed: {p.stderr}")
    return {"ok": True, "file": os.path.basename(fp)}

@router.get("/list", dependencies=[Depends(require_internal)])
async def list_backups():
    d = os.environ.get("BACKUP_DIR", "/app/backups")
    if not os.path.exists(d): return []
    files = sorted([f for f in os.listdir(d) if f.endswith(".sql")], reverse=True)
    return [{"name": f, "size": os.path.getsize(os.path.join(d, f))} for f in files]

@router.get("/download/{filename}", dependencies=[Depends(require_internal)])
async def download_backup(filename: str):
    d = os.environ.get("BACKUP_DIR", "/app/backups"); fp = os.path.join(d, filename)
    if not os.path.exists(fp): raise HTTPException(404)
    with open(fp, "rb") as f:
        return StreamingResponse(BytesIO(f.read()), media_type="application/octet-stream", headers={"Content-Disposition": f"attachment; filename={filename}"})
