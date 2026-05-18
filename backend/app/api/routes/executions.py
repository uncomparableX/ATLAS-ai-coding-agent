from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.repos import get_current_user
from app.core.database import get_db
from app.models.models import Execution, Task, User
from app.schemas.schemas import ExecutionRead

router = APIRouter(prefix="/executions")


@router.get("/tasks/{task_id}", response_model=List[ExecutionRead])
async def get_task_executions(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    task_res = await db.execute(
        select(Task).where(Task.id == task_id, Task.user_id == user.id)
    )
    if not task_res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Task not found")
    result = await db.execute(
        select(Execution)
        .where(Execution.task_id == task_id)
        .order_by(Execution.created_at)
    )
    return result.scalars().all()
