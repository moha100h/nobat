import httpx
from master_bot.config import settings

class BackendClient:
    def __init__(self):
        self.base = settings.BACKEND_URL
        self._h = {"X-Api-Key": settings.INTERNAL_API_KEY}

    async def _req(self, method, path, tid=None, **kw):
        h = {**self._h}
        if tid: h["X-Tenant-Id"] = str(tid)
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.request(method, f"{self.base}{path}", headers=h, **kw)
            r.raise_for_status()
            return r.json()

    async def get(self, path, tid=None, **kw): return await self._req("GET", path, tid, **kw)
    async def post(self, path, tid=None, **kw): return await self._req("POST", path, tid, **kw)
    async def patch(self, path, tid=None, **kw): return await self._req("PATCH", path, tid, **kw)
    async def delete(self, path, tid=None, **kw): return await self._req("DELETE", path, tid, **kw)

api = BackendClient()
