import os
import shutil
import uuid
from pathlib import Path
from typing import List

import structlog
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models.models import Repository, User
from app.schemas.schemas import RepoConnectRequest, RepoRead
from app.services.agents.tools import AgentTools
from app.workers.celery_app import index_repository_task

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/repos")


async def get_current_user(db: AsyncSession = Depends(get_db)) -> User:
    result = await db.execute(select(User).limit(1))
    user = result.scalar_one_or_none()
    if not user:
        user = User(
            id=str(uuid.uuid4()),
            email="demo@agentforge.dev",
            hashed_password="demo",
            full_name="Demo User",
        )
        db.add(user)
        await db.commit()
    return user


@router.get("", response_model=List[RepoRead])
async def list_repositories(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Repository)
        .where(Repository.owner_id == user.id)
        .order_by(Repository.created_at.desc())
    )
    return result.scalars().all()


@router.post("/connect", response_model=RepoRead, status_code=status.HTTP_202_ACCEPTED)
async def connect_github_repository(
    body: RepoConnectRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    url = body.github_url.rstrip("/")
    parts = url.split("/")
    if len(parts) < 2:
        raise HTTPException(status_code=400, detail="Invalid GitHub URL")
    repo_name = parts[-1].replace(".git", "")
    full_name = f"{parts[-2]}/{repo_name}"

    existing = await db.execute(
        select(Repository).where(
            Repository.owner_id == user.id,
            Repository.github_url == body.github_url,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Repository already connected")

    repo = Repository(
        id=str(uuid.uuid4()),
        owner_id=user.id,
        name=repo_name,
        full_name=full_name,
        github_url=body.github_url,
        default_branch=body.branch or "main",
        status="pending",
    )
    db.add(repo)
    await db.commit()
    await db.refresh(repo)

    index_repository_task.apply_async(
        kwargs={
            "repository_id": repo.id,
            "repo_path": "",
            "github_url": body.github_url,
            "github_token": user.github_token or settings.GITHUB_TOKEN,
        },
        queue="indexing",
    )
    return repo


@router.post("/upload", response_model=RepoRead, status_code=status.HTTP_202_ACCEPTED)
async def upload_repository(
    name: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not file.filename or not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only .zip files accepted")

    repo_id = str(uuid.uuid4())
    repo_path = Path(settings.REPO_STORAGE_PATH) / repo_id
    repo_path.mkdir(parents=True, exist_ok=True)
    zip_path = repo_path / "upload.zip"

    try:
        with open(zip_path, "wb") as f:
            while chunk := await file.read(1024 * 1024):
                f.write(chunk)
        import zipfile
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(repo_path / "code")
        zip_path.unlink()
        actual_path = str(repo_path / "code")
    except Exception as e:
        shutil.rmtree(repo_path, ignore_errors=True)
        raise HTTPException(status_code=400, detail=f"Failed to extract: {e}")

    repo = Repository(
        id=repo_id,
        owner_id=user.id,
        name=name,
        local_path=actual_path,
        status="pending",
    )
    db.add(repo)
    await db.commit()
    await db.refresh(repo)

    index_repository_task.apply_async(
        kwargs={"repository_id": repo.id, "repo_path": actual_path},
        queue="indexing",
    )
    return repo


@router.get("/{repo_id}", response_model=RepoRead)
async def get_repository(
    repo_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Repository).where(
            Repository.id == repo_id, Repository.owner_id == user.id
        )
    )
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    return repo


@router.get("/{repo_id}/tree")
async def get_file_tree(
    repo_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Repository).where(
            Repository.id == repo_id, Repository.owner_id == user.id
        )
    )
    repo = result.scalar_one_or_none()
    if not repo or not repo.local_path:
        raise HTTPException(status_code=404, detail="Repository not ready")
    tools = AgentTools(repo.local_path)
    return await tools.get_file_tree(max_depth=6)


@router.get("/{repo_id}/files/{file_path:path}")
async def get_file_content(
    repo_id: str,
    file_path: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Repository).where(
            Repository.id == repo_id, Repository.owner_id == user.id
        )
    )
    repo = result.scalar_one_or_none()
    if not repo or not repo.local_path:
        raise HTTPException(status_code=404, detail="Repository not found")
    tools = AgentTools(repo.local_path)
    content = await tools.read_file(file_path)
    if content is None:
        raise HTTPException(status_code=404, detail="File not found")
    return {
        "path": file_path,
        "content": content,
        "size_bytes": len(content.encode()),
        "line_count": content.count("\n") + 1,
    }


@router.post("/{repo_id}/search")
async def search_codebase(
    repo_id: str,
    query: str,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Repository).where(
            Repository.id == repo_id, Repository.owner_id == user.id
        )
    )
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    from app.services.indexing.vector_store import VectorStore
    vs = VectorStore()
    results = await vs.search_code(query=query, repository_id=repo_id, limit=min(limit, 20))
    return {"query": query, "results": results}


@router.delete("/{repo_id}", status_code=204)
async def delete_repository(
    repo_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Repository).where(
            Repository.id == repo_id, Repository.owner_id == user.id
        )
    )
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    from app.services.indexing.vector_store import VectorStore
    vs = VectorStore()
    await vs.delete_repository(repo_id)
    if repo.local_path and os.path.exists(repo.local_path):
        shutil.rmtree(repo.local_path, ignore_errors=True)
    await db.delete(repo)
    await db.commit()
