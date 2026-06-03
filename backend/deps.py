from fastapi import Header, HTTPException
from shared.config import get_settings

settings = get_settings()

def require_internal(x_api_key: str = Header(...)):
    if x_api_key != settings.INTERNAL_API_KEY:
        raise HTTPException(403, "Forbidden")

def get_tenant_id(x_tenant_id: int = Header(...)) -> int:
    return x_tenant_id
