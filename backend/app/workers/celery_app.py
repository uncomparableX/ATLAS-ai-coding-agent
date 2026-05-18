"""
Celery Application and Task Definitions
Broker: Redis
Backend: Redis

Queues:
  default   - general tasks (agent execution)
  indexing  - repository indexing (CPU/IO heavy)
  execution - docker sandbox runs

Beat schedule:
  - cleanup orphaned Docker containers every 5 minutes
  - purge expired memories every hour
"""
import asyncio
from datetime import datetime
from typing import Optional

import structlog
from celery import Celery
from celery.signals import worker_ready

from app.core.config import settings

logger = structlog.get_logger(__name__)

# ─── Celery app ───────────────────────────────────────────────────────────────

celery_app = Celery(
    "agentforge",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    # Timezone
    timezone="UTC",
    enable_utc=True,
    # Reliability
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    # Results
    result_expires=3600 * 24,  # 24 h
    # Routes
    task_routes={
        "app.workers.celery_app.index_repository_task": {"queue": "indexing"},
        "app.workers.celery_app.run_agent_task":        {"queue": "default"},
        "app.workers.celery_app.cleanup_containers":    {"queue": "default"},
        "app.workers.celery_app.purge_expired_memories":{"queue": "default"},
    },
    # Beat schedule
    beat_schedule={
        "cleanup-containers": {
            "task":     "app.workers.celery_app.cleanup_containers",
            "schedule": 300.0,   # every 5 minutes
        },
        "purge-expired-memories": {
            "task":     "app.workers.celery_app.purge_expired_memories",
            "schedule": 3600.0,  # every hour
        },
    },
)


# ─── Async runner helper ──────────────────────────────────────────────────────

def run_async(coro):
    """Run an async coroutine from a synchronous Celery task."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        try:
            loop.run_until_complete(loop.shutdown_asyncgens())
        except Exception:
            pass
        loop.close()


# ─── Worker signals ───────────────────────────────────────────────────────────

@worker_ready.connect
def on_worker_ready(sender, **kwargs):
    logger.info("Celery worker ready", queues=str(sender.app.amqp.queues))


# ─── Task: Repository Indexing ────────────────────────────────────────────────

@celery_app.task(
    name="app.workers.celery_app.index_repository_task",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    soft_time_limit=1800,
    time_limit=2100,
)
def index_repository_task(
    self,
    repository_id: str,
    repo_path: str,
    github_url: Optional[str] = None,
    github_token: Optional[str] = None,
    branch: Optional[str] = None,
):
    """
    Celery task: clone (if needed) then index a repository.
    Updates repository status in DB and publishes progress via Redis.
    """
    logger.info(
        "index_repository_task started",
        repository_id=repository_id,
        has_github_url=bool(github_url),
    )

    async def _run():
        from app.core.database import AsyncSessionLocal
        from app.core.redis import redis_client
        from app.models.models import Repository
        from app.services.indexing.repository_indexer import RepositoryIndexer
        from sqlalchemy import update

        indexer = RepositoryIndexer()

        async with AsyncSessionLocal() as db:
            try:
                # ── Clone phase ──────────────────────────────────────────────
                if github_url:
                    await db.execute(
                        update(Repository)
                        .where(Repository.id == repository_id)
                        .values(status="cloning")
                    )
                    await db.commit()

                    await redis_client.publish(
                        f"repo:{repository_id}:status",
                        {"status": "cloning", "repository_id": repository_id},
                    )

                    actual_path = await indexer.clone_repository(
                        github_url=github_url,
                        repo_id=repository_id,
                        github_token=github_token,
                        branch=branch,
                    )
                else:
                    actual_path = repo_path

                # ── Indexing phase ───────────────────────────────────────────
                await db.execute(
                    update(Repository)
                    .where(Repository.id == repository_id)
                    .values(status="indexing", local_path=actual_path)
                )
                await db.commit()

                await redis_client.publish(
                    f"repo:{repository_id}:status",
                    {"status": "indexing", "repository_id": repository_id},
                )

                async def progress_callback(progress: dict):
                    await redis_client.publish(
                        f"repo:{repository_id}:progress",
                        {**progress, "repository_id": repository_id},
                    )

                result = await indexer.index_repository(
                    repo_path=actual_path,
                    repository_id=repository_id,
                    progress_callback=progress_callback,
                )

                # ── Done ─────────────────────────────────────────────────────
                await db.execute(
                    update(Repository)
                    .where(Repository.id == repository_id)
                    .values(
                        status="ready",
                        local_path=actual_path,
                        file_count=result["total_files"],
                        indexed_chunks=result["total_chunks"],
                        architecture_summary=result.get("architecture_summary"),
                        language=result.get("dominant_language"),
                        size_mb=result.get("size_mb", 0.0),
                        last_indexed_at=datetime.utcnow(),
                    )
                )
                await db.commit()

                await redis_client.publish(
                    f"repo:{repository_id}:status",
                    {
                        "status":         "ready",
                        "repository_id":  repository_id,
                        "total_files":    result["total_files"],
                        "total_chunks":   result["total_chunks"],
                    },
                )

                logger.info(
                    "index_repository_task complete",
                    repository_id=repository_id,
                    total_files=result["total_files"],
                    total_chunks=result["total_chunks"],
                )

            except Exception as e:
                logger.error(
                    "index_repository_task failed",
                    repository_id=repository_id,
                    error=str(e),
                )
                await db.execute(
                    update(Repository)
                    .where(Repository.id == repository_id)
                    .values(status="error")
                )
                await db.commit()

                await redis_client.publish(
                    f"repo:{repository_id}:status",
                    {
                        "status":        "error",
                        "repository_id": repository_id,
                        "error":         str(e),
                    },
                )
                raise

    try:
        run_async(_run())
    except Exception as exc:
        logger.error("Retrying index_repository_task", error=str(exc))
        raise self.retry(exc=exc)


# ─── Task: Agent Execution ────────────────────────────────────────────────────

@celery_app.task(
    name="app.workers.celery_app.run_agent_task",
    bind=True,
    max_retries=1,
    time_limit=1800,
    soft_time_limit=1700,
)
def run_agent_task(self, task_id: str, user_id: str):
    """
    Celery task: run the full LangGraph multi-agent pipeline for a task.
    Publishes live events to WebSocket subscribers via Redis pub/sub.
    """
    logger.info("run_agent_task started", task_id=task_id, user_id=user_id)

    async def _run():
        from app.core.database import AsyncSessionLocal
        from app.models.models import FileDiff, Repository, Task
        from app.services.agents.orchestrator import AgentOrchestrator
        from app.services.memory.memory_service import MemoryService
        from app.websockets.manager import TaskEventPublisher
        from sqlalchemy import select, update

        publisher    = TaskEventPublisher(task_id)
        orchestrator = AgentOrchestrator()
        memory_svc   = MemoryService()

        async with AsyncSessionLocal() as db:
            # ── Fetch task and repo ──────────────────────────────────────────
            task_res = await db.execute(
                select(Task).where(Task.id == task_id)
            )
            task = task_res.scalar_one_or_none()
            if not task:
                raise ValueError(f"Task {task_id} not found")

            repo_res = await db.execute(
                select(Repository).where(Repository.id == task.repository_id)
            )
            repo = repo_res.scalar_one_or_none()
            if not repo or not repo.local_path:
                raise ValueError(
                    f"Repository not ready for task {task_id}. "
                    "Has it been indexed?"
                )

            # ── Mark as in-progress ──────────────────────────────────────────
            await db.execute(
                update(Task)
                .where(Task.id == task_id)
                .values(
                    status="in_progress",
                    started_at=datetime.utcnow(),
                    celery_task_id=self.request.id,
                )
            )
            await db.commit()
            await publisher.publish_task_status("in_progress")

            await memory_svc.record_task_start(
                task_id=task_id,
                repository_id=repo.id,
                description=task.description,
            )

            try:
                # ── Run agents ───────────────────────────────────────────────
                final_state = await orchestrator.run_task(
                    task_id=task_id,
                    repository_id=task.repository_id,
                    task_description=task.description,
                    repo_path=repo.local_path,
                    architecture_context=repo.architecture_summary or "",
                    event_publisher=publisher,
                )

                # ── Persist file diffs ───────────────────────────────────────
                for change in final_state.get("code_changes", []):
                    diff = FileDiff(
                        task_id=task_id,
                        file_path=change.get("file_path", ""),
                        original_content=change.get("original", ""),
                        modified_content=change.get("modified", ""),
                        diff_unified=change.get("diff", ""),
                        patch_applied=change.get("success", False),
                    )
                    db.add(diff)

                # ── Calculate cost estimate ───────────────────────────────────
                total_tokens = final_state.get("total_tokens", 0)
                # Claude Sonnet pricing: ~$3/$15 per MTok in/out (rough 60/40 split)
                input_cost  = (total_tokens * 0.6) * 3.0  / 1_000_000
                output_cost = (total_tokens * 0.4) * 15.0 / 1_000_000
                cost_usd    = input_cost + output_cost

                new_status = (
                    "completed"
                    if final_state.get("status") == "completed"
                    else "failed"
                )

                # ── Update task record ────────────────────────────────────────
                await db.execute(
                    update(Task)
                    .where(Task.id == task_id)
                    .values(
                        status=new_status,
                        result=final_state.get("final_result"),
                        plan=final_state.get("implementation_plan"),
                        total_tokens=total_tokens,
                        estimated_cost_usd=cost_usd,
                        completed_at=datetime.utcnow(),
                    )
                )
                await db.commit()

                # ── Record completion memory ──────────────────────────────────
                review = (
                    final_state.get("final_result", {}).get("review", {})
                    if final_state.get("final_result")
                    else {}
                )
                if new_status == "completed":
                    await memory_svc.record_task_completion(
                        task_id=task_id,
                        repository_id=repo.id,
                        summary=review.get("summary", task.description[:200]),
                        score=review.get("score", 7),
                    )

                await publisher.publish_task_status(
                    new_status,
                    final_state.get("final_result"),
                )

                logger.info(
                    "run_agent_task complete",
                    task_id=task_id,
                    status=new_status,
                    total_tokens=total_tokens,
                    cost_usd=cost_usd,
                )

            except Exception as e:
                logger.error(
                    "run_agent_task execution failed",
                    task_id=task_id,
                    error=str(e),
                )
                await db.execute(
                    update(Task)
                    .where(Task.id == task_id)
                    .values(
                        status="failed",
                        error_message=str(e)[:2000],
                        completed_at=datetime.utcnow(),
                    )
                )
                await db.commit()
                await publisher.publish_task_status("failed", {"error": str(e)})
                raise

    try:
        run_async(_run())
    except Exception as exc:
        logger.error("run_agent_task raised", task_id=task_id, error=str(exc))
        raise self.retry(exc=exc)


# ─── Task: Container Cleanup ──────────────────────────────────────────────────

@celery_app.task(name="app.workers.celery_app.cleanup_containers")
def cleanup_containers():
    """Periodic task: remove orphaned agentforge Docker containers."""
    async def _run():
        from app.services.execution.docker_executor import DockerExecutor
        executor = DockerExecutor()
        await executor.cleanup_orphaned_containers(prefix="agentforge-")

    run_async(_run())


# ─── Task: Purge expired memories ────────────────────────────────────────────

@celery_app.task(name="app.workers.celery_app.purge_expired_memories")
def purge_expired_memories():
    """Periodic task: delete memories past their TTL."""
    async def _run():
        from app.services.memory.memory_service import MemoryService
        svc = MemoryService()
        await svc.delete_expired()

    run_async(_run())
