from fastapi import APIRouter
from app.core.redis import redis_client

router = APIRouter()


@router.get("/health")
async def health_check():
    redis_ok = False
    try:
        await redis_client.client.ping()
        redis_ok = True
    except Exception:
        pass
    return {"status": "ok", "services": {"api": True, "redis": redis_ok}}
