import uuid
from typing import List

import structlog
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.repos import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models.models import ChatMessage, Repository, User
from app.schemas.schemas import ChatMessageRead, ChatRequest, ChatResponse

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/chat")


@router.post("", response_model=ChatResponse)
async def chat_with_codebase(
    body: ChatRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    repo_result = await db.execute(
        select(Repository).where(
            Repository.id == body.repository_id,
            Repository.owner_id == user.id,
        )
    )
    repo = repo_result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    if repo.status != "ready":
        raise HTTPException(status_code=400, detail="Repository not indexed yet")

    sources = []
    context_text = ""

    if body.use_rag:
        from app.services.indexing.vector_store import VectorStore
        vs = VectorStore()
        results = await vs.search_code(
            query=body.message,
            repository_id=body.repository_id,
            limit=8,
        )
        sources = results
        context_text = "\n\n---\n\n".join([
            f"File: {r['file_path']} (lines {r.get('start_line','?')}-{r.get('end_line','?')})\n"
            f"```{r.get('language','')}\n{r['content']}\n```"
            for r in results
        ])

    history_result = await db.execute(
        select(ChatMessage)
        .where(
            ChatMessage.repository_id == body.repository_id,
            ChatMessage.user_id == user.id,
        )
        .order_by(ChatMessage.created_at.desc())
        .limit(10)
    )
    history = list(reversed(history_result.scalars().all()))

    from langchain_anthropic import ChatAnthropic
    from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

    llm = ChatAnthropic(
        model=settings.FAST_MODEL,
        api_key=settings.ANTHROPIC_API_KEY,
        max_tokens=4096,
    )

    system_prompt = (
        f"You are an expert software engineer assistant with deep knowledge of the codebase.\n"
        f"Repository: {repo.name}\n"
        f"Architecture: {repo.architecture_summary or 'Not available'}\n\n"
        f"Answer questions accurately using the provided code context. "
        f"Reference specific files and line numbers when relevant. "
        f"Be concise but thorough. Use code blocks for examples."
    )

    messages = [SystemMessage(content=system_prompt)]
    for msg in history[-6:]:
        if msg.role == "user":
            messages.append(HumanMessage(content=msg.content))
        else:
            messages.append(AIMessage(content=msg.content))

    user_message = body.message
    if context_text:
        user_message = f"{body.message}\n\n## Relevant Code Context\n{context_text}"
    messages.append(HumanMessage(content=user_message))

    response = await llm.ainvoke(messages)
    assistant_content = response.content
    tokens_used = (len(body.message.split()) + len(assistant_content.split())) * 4 // 3

    user_msg = ChatMessage(
        id=str(uuid.uuid4()),
        repository_id=body.repository_id,
        task_id=body.task_id,
        user_id=user.id,
        role="user",
        content=body.message,
        tokens=len(body.message.split()) * 4 // 3,
    )
    assistant_msg = ChatMessage(
        id=str(uuid.uuid4()),
        repository_id=body.repository_id,
        task_id=body.task_id,
        user_id=user.id,
        role="assistant",
        content=assistant_content,
        tokens=tokens_used,
    )
    db.add(user_msg)
    db.add(assistant_msg)
    await db.commit()
    await db.refresh(assistant_msg)

    return ChatResponse(
        message=ChatMessageRead.model_validate(assistant_msg),
        sources=[
            {
                "file_path": s["file_path"],
                "chunk_content": s["content"][:300],
                "relevance_score": s.get("relevance_score", 0),
                "start_line": s.get("start_line", 0),
                "end_line": s.get("end_line", 0),
                "language": s.get("language"),
            }
            for s in sources[:5]
        ],
        total_tokens=tokens_used,
    )


@router.get("/history/{repository_id}", response_model=List[ChatMessageRead])
async def get_chat_history(
    repository_id: str,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ChatMessage)
        .where(
            ChatMessage.repository_id == repository_id,
            ChatMessage.user_id == user.id,
        )
        .order_by(ChatMessage.created_at.asc())
        .limit(limit)
    )
    return result.scalars().all()


@router.delete("/history/{repository_id}", status_code=204)
async def clear_chat_history(
    repository_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ChatMessage).where(
            ChatMessage.repository_id == repository_id,
            ChatMessage.user_id == user.id,
        )
    )
    for msg in result.scalars().all():
        await db.delete(msg)
    await db.commit()
