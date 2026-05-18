"""Initial schema — create all tables

Revision ID: 0001_initial_schema
Revises:
Create Date: 2025-01-01 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    # ── users ────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id",               sa.String(36),  primary_key=True),
        sa.Column("email",            sa.String(255), nullable=False, unique=True),
        sa.Column("hashed_password",  sa.String(255), nullable=False),
        sa.Column("full_name",        sa.String(255), nullable=True),
        sa.Column("github_token",     sa.Text(),      nullable=True),
        sa.Column("is_active",        sa.Boolean(),   server_default="true",  nullable=False),
        sa.Column("is_superuser",     sa.Boolean(),   server_default="false", nullable=False),
        sa.Column("created_at",       sa.DateTime(),  server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at",       sa.DateTime(),  server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # ── repositories ─────────────────────────────────────────────────────────
    op.create_table(
        "repositories",
        sa.Column("id",                   sa.String(36),  primary_key=True),
        sa.Column("owner_id",             sa.String(36),  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name",                 sa.String(255), nullable=False),
        sa.Column("full_name",            sa.String(512), nullable=True),
        sa.Column("github_url",           sa.Text(),      nullable=True),
        sa.Column("local_path",           sa.Text(),      nullable=True),
        sa.Column("default_branch",       sa.String(100), server_default="main",    nullable=False),
        sa.Column("status",               sa.String(20),  server_default="pending", nullable=False),
        sa.Column("language",             sa.String(100), nullable=True),
        sa.Column("description",          sa.Text(),      nullable=True),
        sa.Column("architecture_summary", sa.Text(),      nullable=True),
        sa.Column("file_count",           sa.Integer(),   server_default="0", nullable=False),
        sa.Column("indexed_chunks",       sa.Integer(),   server_default="0", nullable=False),
        sa.Column("size_mb",              sa.Float(),     server_default="0", nullable=False),
        sa.Column("metadata",             postgresql.JSON(), nullable=True),
        sa.Column("last_indexed_at",      sa.DateTime(),  nullable=True),
        sa.Column("created_at",           sa.DateTime(),  server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at",           sa.DateTime(),  server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_repo_owner_name", "repositories", ["owner_id", "name"])
    op.create_index("ix_repo_status",     "repositories", ["status"])

    # ── repository_files ─────────────────────────────────────────────────────
    op.create_table(
        "repository_files",
        sa.Column("id",             sa.String(36),  primary_key=True),
        sa.Column("repository_id",  sa.String(36),  sa.ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False),
        sa.Column("path",           sa.Text(),      nullable=False),
        sa.Column("language",       sa.String(50),  nullable=True),
        sa.Column("size_bytes",     sa.Integer(),   server_default="0", nullable=False),
        sa.Column("line_count",     sa.Integer(),   server_default="0", nullable=False),
        sa.Column("chunk_count",    sa.Integer(),   server_default="0", nullable=False),
        sa.Column("ast_summary",    sa.Text(),      nullable=True),
        sa.Column("last_modified",  sa.DateTime(),  nullable=True),
        sa.Column("created_at",     sa.DateTime(),  server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_repofile_repo_path", "repository_files", ["repository_id", "path"])

    # ── tasks ─────────────────────────────────────────────────────────────────
    op.create_table(
        "tasks",
        sa.Column("id",                  sa.String(36),  primary_key=True),
        sa.Column("user_id",             sa.String(36),  sa.ForeignKey("users.id",         ondelete="CASCADE"), nullable=False),
        sa.Column("repository_id",       sa.String(36),  sa.ForeignKey("repositories.id",  ondelete="CASCADE"), nullable=False),
        sa.Column("title",               sa.String(500), nullable=False),
        sa.Column("description",         sa.Text(),      nullable=False),
        sa.Column("status",              sa.String(30),  server_default="queued", nullable=False),
        sa.Column("plan",                postgresql.JSON(), nullable=True),
        sa.Column("result",              postgresql.JSON(), nullable=True),
        sa.Column("error_message",       sa.Text(),      nullable=True),
        sa.Column("retry_count",         sa.Integer(),   server_default="0", nullable=False),
        sa.Column("celery_task_id",      sa.String(255), nullable=True),
        sa.Column("total_tokens",        sa.Integer(),   server_default="0", nullable=False),
        sa.Column("estimated_cost_usd",  sa.Float(),     server_default="0", nullable=False),
        sa.Column("started_at",          sa.DateTime(),  nullable=True),
        sa.Column("completed_at",        sa.DateTime(),  nullable=True),
        sa.Column("created_at",          sa.DateTime(),  server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at",          sa.DateTime(),  server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_tasks_user_id",       "tasks", ["user_id"])
    op.create_index("ix_tasks_repository_id", "tasks", ["repository_id"])
    op.create_index("ix_tasks_status",        "tasks", ["status"])
    op.create_index("ix_tasks_created_at",    "tasks", ["created_at"])

    # ── agent_runs ────────────────────────────────────────────────────────────
    op.create_table(
        "agent_runs",
        sa.Column("id",          sa.String(36), primary_key=True),
        sa.Column("task_id",     sa.String(36), sa.ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("agent_type",  sa.String(30), nullable=False),
        sa.Column("iteration",   sa.Integer(),  server_default="0", nullable=False),
        sa.Column("input_data",  postgresql.JSON(), nullable=True),
        sa.Column("output_data", postgresql.JSON(), nullable=True),
        sa.Column("thoughts",    sa.Text(),     nullable=True),
        sa.Column("actions",     postgresql.JSON(), nullable=True),
        sa.Column("tokens_used", sa.Integer(),  server_default="0", nullable=False),
        sa.Column("duration_ms", sa.Integer(),  server_default="0", nullable=False),
        sa.Column("status",      sa.String(50), server_default="running", nullable=False),
        sa.Column("created_at",  sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_agent_runs_task_id", "agent_runs", ["task_id"])

    # ── executions ────────────────────────────────────────────────────────────
    op.create_table(
        "executions",
        sa.Column("id",           sa.String(36), primary_key=True),
        sa.Column("task_id",      sa.String(36), sa.ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("command",      sa.Text(),     nullable=False),
        sa.Column("working_dir",  sa.Text(),     nullable=True),
        sa.Column("status",       sa.String(20), server_default="pending", nullable=False),
        sa.Column("exit_code",    sa.Integer(),  nullable=True),
        sa.Column("stdout",       sa.Text(),     nullable=True),
        sa.Column("stderr",       sa.Text(),     nullable=True),
        sa.Column("duration_ms",  sa.Integer(),  server_default="0", nullable=False),
        sa.Column("container_id", sa.String(255), nullable=True),
        sa.Column("created_at",   sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_executions_task_id", "executions", ["task_id"])

    # ── file_diffs ─────────────────────────────────────────────────────────────
    op.create_table(
        "file_diffs",
        sa.Column("id",               sa.String(36), primary_key=True),
        sa.Column("task_id",          sa.String(36), sa.ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("file_path",        sa.Text(),     nullable=False),
        sa.Column("original_content", sa.Text(),     nullable=True),
        sa.Column("modified_content", sa.Text(),     nullable=True),
        sa.Column("diff_unified",     sa.Text(),     nullable=True),
        sa.Column("patch_applied",    sa.Boolean(),  server_default="false", nullable=False),
        sa.Column("created_at",       sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_file_diffs_task_id", "file_diffs", ["task_id"])

    # ── chat_messages ─────────────────────────────────────────────────────────
    op.create_table(
        "chat_messages",
        sa.Column("id",            sa.String(36), primary_key=True),
        sa.Column("task_id",       sa.String(36), sa.ForeignKey("tasks.id",        ondelete="SET NULL"), nullable=True),
        sa.Column("repository_id", sa.String(36), sa.ForeignKey("repositories.id", ondelete="CASCADE"),  nullable=True),
        sa.Column("user_id",       sa.String(36), sa.ForeignKey("users.id",        ondelete="CASCADE"),  nullable=False),
        sa.Column("role",          sa.String(20), nullable=False),
        sa.Column("content",       sa.Text(),     nullable=False),
        sa.Column("tokens",        sa.Integer(),  server_default="0", nullable=False),
        sa.Column("metadata",      postgresql.JSON(), nullable=True),
        sa.Column("created_at",    sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_chat_repo_user",    "chat_messages", ["repository_id", "user_id"])
    op.create_index("ix_chat_task_id",      "chat_messages", ["task_id"])
    op.create_index("ix_chat_created_at",   "chat_messages", ["created_at"])

    # ── agent_memories ────────────────────────────────────────────────────────
    op.create_table(
        "agent_memories",
        sa.Column("id",            sa.String(36), primary_key=True),
        sa.Column("task_id",       sa.String(36), sa.ForeignKey("tasks.id",        ondelete="SET NULL"), nullable=True),
        sa.Column("repository_id", sa.String(36), sa.ForeignKey("repositories.id", ondelete="CASCADE"),  nullable=True),
        sa.Column("memory_type",   sa.String(50), nullable=False),
        sa.Column("content",       sa.Text(),     nullable=False),
        sa.Column("embedding_id",  sa.String(255), nullable=True),
        sa.Column("importance",    sa.Float(),    server_default="0.5", nullable=False),
        sa.Column("access_count",  sa.Integer(),  server_default="0",   nullable=False),
        sa.Column("metadata",      postgresql.JSON(), nullable=True),
        sa.Column("expires_at",    sa.DateTime(), nullable=True),
        sa.Column("created_at",    sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("last_accessed", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_memories_repo_id",   "agent_memories", ["repository_id"])
    op.create_index("ix_memories_task_id",   "agent_memories", ["task_id"])
    op.create_index("ix_memories_type",      "agent_memories", ["memory_type"])
    op.create_index("ix_memories_importance","agent_memories", ["importance"])
    op.create_index("ix_memories_expires_at","agent_memories", ["expires_at"])


def downgrade() -> None:
    op.drop_table("agent_memories")
    op.drop_table("chat_messages")
    op.drop_table("file_diffs")
    op.drop_table("executions")
    op.drop_table("agent_runs")
    op.drop_table("tasks")
    op.drop_table("repository_files")
    op.drop_table("repositories")
    op.drop_table("users")
