from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.repos import get_current_user
from app.core.database import get_db
from app.models.models import AgentMemory, User
from app.schemas.schemas import MemoryRead

router = APIRouter(prefix="/memory")


@router.get("", response_model=List[MemoryRead])
async def list_memories(
    repository_id: str = None,
    task_id: str = None,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = select(AgentMemory)
    if repository_id:
        query = query.where(AgentMemory.repository_id == repository_id)
    if task_id:
        query = query.where(AgentMemory.task_id == task_id)
    query = query.order_by(AgentMemory.importance.desc()).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/search")
async def search_memory(
    query: str,
    repository_id: str = None,
    limit: int = 5,
    user: User = Depends(get_current_user),
):
    from app.services.indexing.vector_store import VectorStore
    vs = VectorStore()
    filters = {}
    if repository_id:
        filters["repository_id"] = repository_id
    results = await vs.search_memory(query=query, filters=filters, limit=limit)
    return {"query": query, "results": results}
