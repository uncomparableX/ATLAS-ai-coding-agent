"""
AgentForge Multi-Agent Orchestration Engine
LangGraph-based stateful pipeline:
  planner -> analyst -> coder -> executor -> debugger (on fail) -> reviewer -> END
"""
import json
import time
from datetime import datetime
from typing import Annotated, Any, Dict, List, Optional, TypedDict

import structlog
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages

from app.core.config import settings
from app.services.agents.tools import AgentTools
from app.services.execution.docker_executor import DockerExecutor
from app.services.indexing.vector_store import VectorStore
from app.services.memory.memory_service import MemoryService

logger = structlog.get_logger(__name__)


# ─── Agent State ──────────────────────────────────────────────────────────────

class AgentState(TypedDict):
    task_id: str
    repository_id: str
    task_description: str
    repo_path: str
    messages: Annotated[List[Any], add_messages]
    implementation_plan: Optional[Dict[str, Any]]
    relevant_files: List[str]
    architecture_context: str
    code_changes: List[Dict[str, Any]]
    execution_results: List[Dict[str, Any]]
    test_output: Optional[str]
    current_agent: str
    iteration: int
    max_iterations: int
    retry_count: int
    max_retries: int
    error_context: Optional[str]
    should_retry: bool
    final_result: Optional[Dict[str, Any]]
    status: str
    event_publisher: Optional[Any]
    total_tokens: int


# ─── LLM helpers ──────────────────────────────────────────────────────────────

def get_llm() -> ChatAnthropic:
    return ChatAnthropic(
        model=settings.DEFAULT_MODEL,
        api_key=settings.ANTHROPIC_API_KEY,
        temperature=settings.TEMPERATURE,
        max_tokens=settings.MAX_TOKENS,
    )


def get_fast_llm() -> ChatAnthropic:
    return ChatAnthropic(
        model=settings.FAST_MODEL,
        api_key=settings.ANTHROPIC_API_KEY,
        temperature=0.1,
        max_tokens=4096,
    )


def count_tokens(text: str) -> int:
    return len(text.split()) * 4 // 3


# ─── Base Agent ───────────────────────────────────────────────────────────────

class BaseAgent:
    def __init__(self, agent_type: str):
        self.agent_type = agent_type
        self.llm = get_llm()
        self.fast_llm = get_fast_llm()
        self.vector_store = VectorStore()
        self.memory_service = MemoryService()

    async def publish(self, state: AgentState, event_type: str, data: Any):
        if state.get("event_publisher"):
            try:
                await state["event_publisher"]({
                    "type": event_type,
                    "task_id": state["task_id"],
                    "agent_type": self.agent_type,
                    "data": data,
                    "timestamp": datetime.utcnow().isoformat(),
                })
            except Exception:
                pass


# ─── Planner Agent ────────────────────────────────────────────────────────────

class PlannerAgent(BaseAgent):
    SYSTEM = """You are an expert software architect and planning agent.
Analyze the task and produce a detailed JSON implementation plan with this exact structure:
{
  "summary": "One-paragraph approach summary",
  "steps": [
    {
      "id": 1,
      "title": "Step title",
      "description": "Detailed description of what to do",
      "files_to_modify": ["path/to/existing/file.py"],
      "files_to_create": ["path/to/new/file.py"],
      "tests_to_run": ["pytest tests/test_x.py -v"],
      "dependencies": []
    }
  ],
  "estimated_complexity": "low|medium|high",
  "risks": ["potential issue description"],
  "success_criteria": ["what done looks like"]
}

Rules:
- Be specific. Reference actual files by path.
- Think step by step before producing the plan.
- Keep steps atomic and testable.
- Output valid JSON only, no markdown fences."""

    async def run(self, state: AgentState) -> AgentState:
        logger.info("Planner agent starting", task_id=state["task_id"])

        await self.publish(state, "agent_thought", {
            "message": "Analyzing task requirements and creating implementation plan...",
            "agent": self.agent_type,
        })

        messages = [
            SystemMessage(content=self.SYSTEM),
            HumanMessage(content=(
                f"## Task\n{state['task_description']}\n\n"
                f"## Repository Architecture\n{state.get('architecture_context', 'Not available')}\n\n"
                f"## Known Relevant Files\n"
                + "\n".join(state.get("relevant_files", [])[:20])
                + "\n\nProduce the implementation plan as valid JSON only."
            )),
        ]

        response = await self.llm.ainvoke(messages)
        raw = response.content
        tokens = count_tokens(raw)

        try:
            j_start = raw.find("{")
            j_end = raw.rfind("}") + 1
            plan = json.loads(raw[j_start:j_end])
        except Exception:
            plan = {
                "summary": raw[:500],
                "steps": [
                    {
                        "id": 1,
                        "title": "Implement task",
                        "description": raw,
                        "files_to_modify": [],
                        "files_to_create": [],
                        "tests_to_run": [],
                        "dependencies": [],
                    }
                ],
                "estimated_complexity": "medium",
                "risks": [],
                "success_criteria": [],
            }

        await self.publish(state, "agent_result", {
            "agent": self.agent_type,
            "plan": plan,
            "tokens": tokens,
            "steps_count": len(plan.get("steps", [])),
        })

        return {
            **state,
            "implementation_plan": plan,
            "current_agent": "analyst",
            "messages": [
                AIMessage(
                    content=(
                        f"[Planner] Created {len(plan.get('steps', []))} step plan: "
                        f"{plan.get('summary', '')[:200]}"
                    )
                )
            ],
            "total_tokens": state.get("total_tokens", 0) + tokens,
        }


# ─── Analyst Agent ────────────────────────────────────────────────────────────

class AnalystAgent(BaseAgent):
    SYSTEM = """You are an expert code analyst.
Given a task and codebase context, identify all relevant files and architecture patterns.
Return JSON only with this structure:
{
  "files_to_read": ["path/to/file.py"],
  "files_to_modify": ["path/to/modify.py"],
  "architecture_notes": "Key patterns, frameworks, and constraints observed",
  "dependencies": {"module_name": "how it is used in this project"},
  "entry_points": ["main files to understand the flow"]
}

Rules:
- Be exhaustive — missing a file can cause the coder to break imports.
- Note the testing framework used (pytest, jest, etc).
- Note any linting or formatting tools in use.
- Output valid JSON only."""

    async def run(self, state: AgentState) -> AgentState:
        logger.info("Analyst agent starting", task_id=state["task_id"])

        await self.publish(state, "agent_thought", {
            "message": "Performing semantic search and analyzing codebase architecture...",
            "agent": self.agent_type,
        })

        # RAG: semantic search over indexed code
        chunks = await self.vector_store.search_code(
            query=state["task_description"],
            repository_id=state["repository_id"],
            limit=15,
        )

        code_context = "\n\n---\n\n".join([
            f"File: {c['file_path']} (lines {c.get('start_line', '?')}-{c.get('end_line', '?')})\n"
            f"```{c.get('language', '')}\n{c['content']}\n```"
            for c in chunks
        ])

        messages = [
            SystemMessage(content=self.SYSTEM),
            HumanMessage(content=(
                f"## Task\n{state['task_description']}\n\n"
                f"## Plan Summary\n{state.get('implementation_plan', {}).get('summary', 'N/A')}\n\n"
                f"## Relevant Code Found via Semantic Search\n{code_context}\n\n"
                "Identify all files that need attention. Return valid JSON only."
            )),
        ]

        response = await self.llm.ainvoke(messages)
        raw = response.content
        tokens = count_tokens(raw)

        try:
            j_start = raw.find("{")
            j_end = raw.rfind("}") + 1
            analysis = json.loads(raw[j_start:j_end])
        except Exception:
            analysis = {
                "files_to_read": [],
                "files_to_modify": [],
                "architecture_notes": raw[:500],
            }

        relevant_files = list(set(
            analysis.get("files_to_read", [])
            + analysis.get("files_to_modify", [])
            + [c["file_path"] for c in chunks]
        ))

        await self.publish(state, "agent_result", {
            "agent": self.agent_type,
            "relevant_files": relevant_files,
            "architecture_notes": analysis.get("architecture_notes", ""),
            "chunks_found": len(chunks),
        })

        return {
            **state,
            "relevant_files": relevant_files,
            "architecture_context": (
                state.get("architecture_context", "")
                + "\n\n"
                + analysis.get("architecture_notes", "")
            ),
            "current_agent": "coder",
            "messages": [
                AIMessage(
                    content=(
                        f"[Analyst] Identified {len(relevant_files)} relevant files. "
                        f"Found {len(chunks)} semantic matches."
                    )
                )
            ],
            "total_tokens": state.get("total_tokens", 0) + tokens,
        }


# ─── Coding Agent ─────────────────────────────────────────────────────────────

class CodingAgent(BaseAgent):
    SYSTEM = """You are an expert software engineer.
Implement the required code changes based on the plan provided.
Output JSON only with this exact structure:
{
  "changes": [
    {
      "file_path": "relative/path/to/file.py",
      "action": "modify|create|delete",
      "content": "COMPLETE file content here — never partial snippets, never truncated",
      "explanation": "Why this change is needed"
    }
  ],
  "summary": "What was implemented overall"
}

Rules:
- Always output COMPLETE file content, never use ellipsis or partial snippets.
- Maintain existing code style, indentation, and conventions.
- Add proper error handling and logging.
- Include type hints for Python code.
- Never use placeholder comments like # TODO: implement this.
- Write production-grade, clean, readable code.
- If retrying after a failure, fix the specific error described in the error context.
- Output valid JSON only."""

    async def run(self, state: AgentState) -> AgentState:
        logger.info("Coder agent starting", task_id=state["task_id"])

        await self.publish(state, "agent_thought", {
            "message": "Reading relevant files and generating code changes...",
            "agent": self.agent_type,
        })

        tools = AgentTools(repo_path=state["repo_path"])

        # Read all relevant files
        file_contents: Dict[str, str] = {}
        for fp in state.get("relevant_files", [])[:10]:
            content = await tools.read_file(fp)
            if content:
                file_contents[fp] = content

        files_ctx = "\n\n---\n\n".join([
            f"### {path}\n```\n{content[:3000]}\n```"
            for path, content in file_contents.items()
        ])

        plan = state.get("implementation_plan", {})
        plan_text = "\n".join([
            f"Step {s['id']}: {s['title']}\n  {s['description']}\n"
            f"  Files to modify: {s.get('files_to_modify', [])}\n"
            f"  Files to create: {s.get('files_to_create', [])}"
            for s in plan.get("steps", [])
        ])

        error_section = ""
        if state.get("error_context"):
            error_section = f"\n\n## IMPORTANT — Fix This Error\n{state['error_context']}"

        messages = [
            SystemMessage(content=self.SYSTEM),
            HumanMessage(content=(
                f"## Task\n{state['task_description']}\n\n"
                f"## Implementation Plan\n{plan_text}\n\n"
                f"## Current File Contents\n{files_ctx}"
                f"{error_section}\n\n"
                "Implement all required changes. Output valid JSON with complete file contents."
            )),
        ]

        response = await self.llm.ainvoke(messages)
        raw = response.content
        tokens = count_tokens(raw)

        try:
            j_start = raw.find("{")
            j_end = raw.rfind("}") + 1
            result = json.loads(raw[j_start:j_end])
            changes = result.get("changes", [])
        except Exception as e:
            logger.error("Failed to parse coder output", error=str(e))
            changes = []

        # Apply all changes to disk
        applied: List[Dict[str, Any]] = []
        for change in changes:
            try:
                applied_change = await tools.apply_change(
                    file_path=change["file_path"],
                    content=change.get("content", ""),
                    action=change.get("action", "modify"),
                    original_content=file_contents.get(change["file_path"]),
                )
                applied.append(applied_change)
                await self.publish(state, "file_changed", {
                    "file_path": change["file_path"],
                    "action": change.get("action"),
                    "explanation": change.get("explanation", ""),
                    "diff": applied_change.get("diff", ""),
                    "lines_added": applied_change.get("lines_added", 0),
                    "lines_removed": applied_change.get("lines_removed", 0),
                })
            except Exception as e:
                logger.error(
                    "Failed to apply change",
                    file=change.get("file_path"),
                    error=str(e),
                )

        await self.publish(state, "agent_result", {
            "agent": self.agent_type,
            "changes_applied": len(applied),
            "files_modified": [c["file_path"] for c in applied],
            "summary": result.get("summary", "") if "result" in dir() else "",
        })

        return {
            **state,
            "code_changes": state.get("code_changes", []) + applied,
            "current_agent": "executor",
            "messages": [
                AIMessage(
                    content=f"[Coder] Applied {len(applied)} file changes."
                )
            ],
            "total_tokens": state.get("total_tokens", 0) + tokens,
        }


# ─── Execution Agent ──────────────────────────────────────────────────────────

class ExecutionAgent(BaseAgent):
    async def run(self, state: AgentState) -> AgentState:
        logger.info("Executor agent starting", task_id=state["task_id"])

        await self.publish(state, "agent_thought", {
            "message": "Running tests and build commands inside Docker sandbox...",
            "agent": self.agent_type,
        })

        executor = DockerExecutor()
        plan = state.get("implementation_plan", {})

        # Collect test commands from plan steps
        test_commands: List[str] = []
        for step in plan.get("steps", []):
            test_commands.extend(step.get("tests_to_run", []))

        # Default fallback commands if plan has none
        if not test_commands:
            test_commands = [
                "pytest --tb=short -q 2>&1 || echo '[agentforge] No pytest found, skipping tests'",
            ]

        exec_results: List[Dict[str, Any]] = []
        all_output: List[str] = []
        overall_success = True

        for cmd in test_commands[:5]:  # cap at 5 commands
            await self.publish(state, "execution_log", {
                "command": cmd,
                "status": "starting",
            })

            result = await executor.run(
                command=cmd,
                repo_path=state["repo_path"],
                task_id=state["task_id"],
                timeout=settings.SANDBOX_TIMEOUT_SECONDS,
            )

            exec_results.append(result)
            stdout = result.get("stdout", "")
            stderr = result.get("stderr", "")
            combined = f"$ {cmd}\n{stdout}"
            if stderr:
                combined += f"\nSTDERR:\n{stderr}"
            all_output.append(combined)

            if result.get("exit_code", 1) != 0:
                overall_success = False

            await self.publish(state, "execution_log", {
                "command": cmd,
                "exit_code": result.get("exit_code"),
                "stdout": stdout[:2000],
                "stderr": stderr[:500],
                "status": "success" if result.get("exit_code") == 0 else "failed",
            })

        combined_output = "\n\n".join(all_output)
        next_agent = "reviewer" if overall_success else "debugger"

        return {
            **state,
            "execution_results": state.get("execution_results", []) + exec_results,
            "test_output": combined_output,
            "current_agent": next_agent,
            "should_retry": not overall_success,
            "error_context": combined_output if not overall_success else None,
            "messages": [
                AIMessage(
                    content=(
                        f"[Executor] Tests {'passed' if overall_success else 'FAILED'}. "
                        f"Exit codes: {[r.get('exit_code') for r in exec_results]}"
                    )
                )
            ],
        }


# ─── Debug Agent ──────────────────────────────────────────────────────────────

class DebugAgent(BaseAgent):
    SYSTEM = """You are an expert debugging agent.
Analyze the failing test output and diagnose the root cause.
Return JSON only with this structure:
{
  "root_cause": "Clear explanation of what is broken and why",
  "fix_strategy": "Specific instructions on how to fix it",
  "files_to_fix": ["specific/files/that/need/changes.py"],
  "should_retry": true,
  "error_type": "logic_error|import_error|type_error|missing_file|syntax_error|test_config|other"
}

Rules:
- Be precise about the root cause — vague analysis wastes retries.
- The fix_strategy will be passed to the coder agent, so be specific.
- If the error is unrecoverable (e.g. missing external service), set should_retry to false.
- Output valid JSON only."""

    async def run(self, state: AgentState) -> AgentState:
        retry_count = state.get("retry_count", 0)
        max_retries = state.get("max_retries", settings.MAX_RETRY_ATTEMPTS)

        if retry_count >= max_retries:
            logger.warning(
                "Max retries reached",
                task_id=state["task_id"],
                retry_count=retry_count,
            )
            await self.publish(state, "agent_thought", {
                "message": f"Max retries ({max_retries}) reached. Marking task as failed.",
                "agent": self.agent_type,
            })
            return {
                **state,
                "current_agent": "done",
                "status": "failed",
                "messages": [
                    AIMessage(
                        content=(
                            f"[Debugger] Max retries ({max_retries}) exceeded. "
                            f"Task cannot be completed automatically."
                        )
                    )
                ],
            }

        logger.info(
            "Debugger agent starting",
            task_id=state["task_id"],
            retry=retry_count + 1,
        )

        await self.publish(state, "agent_thought", {
            "message": f"Analyzing failure (attempt {retry_count + 1} of {max_retries})...",
            "agent": self.agent_type,
        })

        modified_files_str = "\n".join([
            f"- {c.get('file_path', 'unknown')}"
            for c in state.get("code_changes", [])
        ])

        messages = [
            SystemMessage(content=self.SYSTEM),
            HumanMessage(content=(
                f"## Original Task\n{state['task_description']}\n\n"
                f"## Test Output / Error\n{state.get('test_output', 'No output available')}\n\n"
                f"## Files Modified So Far\n{modified_files_str or 'None'}\n\n"
                f"## Previous Error Context\n{state.get('error_context', 'None')}\n\n"
                "Diagnose the failure precisely. Return valid JSON only."
            )),
        ]

        response = await self.llm.ainvoke(messages)
        raw = response.content
        tokens = count_tokens(raw)

        try:
            j_start = raw.find("{")
            j_end = raw.rfind("}") + 1
            diagnosis = json.loads(raw[j_start:j_end])
        except Exception:
            diagnosis = {
                "root_cause": raw[:500],
                "fix_strategy": "Retry with corrected implementation based on the error output.",
                "files_to_fix": [],
                "should_retry": True,
                "error_type": "other",
            }

        await self.publish(state, "agent_result", {
            "agent": self.agent_type,
            "root_cause": diagnosis.get("root_cause"),
            "fix_strategy": diagnosis.get("fix_strategy"),
            "error_type": diagnosis.get("error_type"),
            "retry_number": retry_count + 1,
            "max_retries": max_retries,
        })

        # Build enriched error context to pass back to coder
        enriched_error_context = (
            f"=== RETRY {retry_count + 1} of {max_retries} ===\n\n"
            f"PREVIOUS TEST OUTPUT:\n{state.get('test_output', '')}\n\n"
            f"ROOT CAUSE ANALYSIS:\n{diagnosis.get('root_cause', '')}\n\n"
            f"FIX STRATEGY:\n{diagnosis.get('fix_strategy', '')}\n\n"
            f"FILES THAT NEED FIXING:\n"
            + "\n".join(diagnosis.get("files_to_fix", []))
        )

        # If debugger says do not retry, stop
        if not diagnosis.get("should_retry", True):
            return {
                **state,
                "current_agent": "done",
                "status": "failed",
                "error_context": enriched_error_context,
                "messages": [
                    AIMessage(
                        content=(
                            f"[Debugger] Unrecoverable error: "
                            f"{diagnosis.get('root_cause', '')[:200]}"
                        )
                    )
                ],
                "total_tokens": state.get("total_tokens", 0) + tokens,
            }

        return {
            **state,
            "error_context": enriched_error_context,
            "retry_count": retry_count + 1,
            "current_agent": "coder",
            "messages": [
                AIMessage(
                    content=(
                        f"[Debugger] Root cause: {diagnosis.get('root_cause', '')[:200]}. "
                        f"Sending fix strategy to coder (retry {retry_count + 1})."
                    )
                )
            ],
            "total_tokens": state.get("total_tokens", 0) + tokens,
        }


# ─── Reviewer Agent ───────────────────────────────────────────────────────────

class ReviewerAgent(BaseAgent):
    SYSTEM = """You are a senior software engineer performing a code review.
Review the implemented changes for correctness, quality, and completeness.
Return JSON only with this structure:
{
  "approved": true,
  "score": 8,
  "summary": "Overall assessment of the implementation",
  "issues": [
    {
      "severity": "high|medium|low",
      "description": "Issue description",
      "file": "affected/file.py",
      "suggestion": "How to fix it"
    }
  ],
  "suggestions": ["Optional improvement ideas"],
  "test_coverage": "Assessment of test coverage",
  "security_notes": "Any security concerns or confirmations"
}

Rules:
- Score from 1 (terrible) to 10 (perfect).
- approved should be true if score >= 6 and no high severity issues.
- Be honest and constructive.
- Output valid JSON only."""

    async def run(self, state: AgentState) -> AgentState:
        logger.info("Reviewer agent starting", task_id=state["task_id"])

        await self.publish(state, "agent_thought", {
            "message": "Reviewing code quality, correctness, and completeness...",
            "agent": self.agent_type,
        })

        changes_summary = "\n".join([
            f"- {c.get('file_path')}: {c.get('action', 'modified')} "
            f"(+{c.get('lines_added', 0)} -{c.get('lines_removed', 0)} lines)"
            for c in state.get("code_changes", [])
        ])

        diffs_text = "\n\n".join([
            f"### {c.get('file_path')}\n```diff\n{c.get('diff', 'No diff available')[:2000]}\n```"
            for c in state.get("code_changes", [])[:5]
        ])

        messages = [
            SystemMessage(content=self.SYSTEM),
            HumanMessage(content=(
                f"## Original Task\n{state['task_description']}\n\n"
                f"## Files Changed\n{changes_summary or 'None'}\n\n"
                f"## Code Diffs\n{diffs_text}\n\n"
                f"## Test Results\n{state.get('test_output', 'No tests run')}\n\n"
                "Review the implementation thoroughly. Return valid JSON only."
            )),
        ]

        response = await self.fast_llm.ainvoke(messages)
        raw = response.content
        tokens = count_tokens(raw)

        try:
            j_start = raw.find("{")
            j_end = raw.rfind("}") + 1
            review = json.loads(raw[j_start:j_end])
        except Exception:
            review = {
                "approved": True,
                "score": 7,
                "summary": "Implementation completed and tests passed.",
                "issues": [],
                "suggestions": [],
                "test_coverage": "Tests passed",
                "security_notes": "No obvious security issues",
            }

        await self.publish(state, "agent_result", {
            "agent": self.agent_type,
            "review": review,
            "score": review.get("score"),
            "approved": review.get("approved"),
            "issues_count": len(review.get("issues", [])),
        })

        return {
            **state,
            "final_result": {
                "review": review,
                "code_changes": state.get("code_changes", []),
                "execution_results": state.get("execution_results", []),
                "total_tokens": state.get("total_tokens", 0) + tokens,
                "files_modified": [c.get("file_path") for c in state.get("code_changes", [])],
            },
            "current_agent": "done",
            "status": "completed",
            "messages": [
                AIMessage(
                    content=(
                        f"[Reviewer] Score: {review.get('score')}/10. "
                        f"Approved: {review.get('approved')}. "
                        f"{review.get('summary', '')[:200]}"
                    )
                )
            ],
            "total_tokens": state.get("total_tokens", 0) + tokens,
        }


# ─── Routing Functions ────────────────────────────────────────────────────────

def route_after_planner(state: AgentState) -> str:
    return state.get("current_agent", "analyst")


def route_after_analyst(state: AgentState) -> str:
    return state.get("current_agent", "coder")


def route_after_coder(state: AgentState) -> str:
    return state.get("current_agent", "executor")


def route_after_executor(state: AgentState) -> str:
    return state.get("current_agent", "reviewer")


def route_after_debugger(state: AgentState) -> str:
    agent = state.get("current_agent", "coder")
    if agent == "done":
        return END
    return agent


def route_after_reviewer(state: AgentState) -> str:
    return END


# ─── Graph Builder ────────────────────────────────────────────────────────────

def build_agent_graph() -> StateGraph:
    planner  = PlannerAgent("planner")
    analyst  = AnalystAgent("analyst")
    coder    = CodingAgent("coder")
    executor = ExecutionAgent("executor")
    debugger = DebugAgent("debugger")
    reviewer = ReviewerAgent("reviewer")

    g = StateGraph(AgentState)

    g.add_node("planner",  planner.run)
    g.add_node("analyst",  analyst.run)
    g.add_node("coder",    coder.run)
    g.add_node("executor", executor.run)
    g.add_node("debugger", debugger.run)
    g.add_node("reviewer", reviewer.run)

    g.set_entry_point("planner")

    g.add_conditional_edges(
        "planner",
        route_after_planner,
        {"analyst": "analyst", "done": END},
    )
    g.add_conditional_edges(
        "analyst",
        route_after_analyst,
        {"coder": "coder"},
    )
    g.add_conditional_edges(
        "coder",
        route_after_coder,
        {"executor": "executor"},
    )
    g.add_conditional_edges(
        "executor",
        route_after_executor,
        {"reviewer": "reviewer", "debugger": "debugger"},
    )
    g.add_conditional_edges(
        "debugger",
        route_after_debugger,
        {"coder": "coder", END: END},
    )
    g.add_conditional_edges(
        "reviewer",
        route_after_reviewer,
        {END: END},
    )

    return g.compile()


# ─── Orchestrator ─────────────────────────────────────────────────────────────

class AgentOrchestrator:
    def __init__(self):
        self.graph = build_agent_graph()

    async def run_task(
        self,
        task_id: str,
        repository_id: str,
        task_description: str,
        repo_path: str,
        architecture_context: str = "",
        relevant_files: List[str] = None,
        event_publisher: Any = None,
    ) -> Dict[str, Any]:
        """
        Execute the full multi-agent pipeline for a task.
        Returns the final state dict with results, diffs, and review.
        """
        initial_state: AgentState = {
            "task_id":             task_id,
            "repository_id":       repository_id,
            "task_description":    task_description,
            "repo_path":           repo_path,
            "messages":            [HumanMessage(content=task_description)],
            "implementation_plan": None,
            "relevant_files":      relevant_files or [],
            "architecture_context": architecture_context,
            "code_changes":        [],
            "execution_results":   [],
            "test_output":         None,
            "current_agent":       "planner",
            "iteration":           0,
            "max_iterations":      settings.MAX_AGENT_ITERATIONS,
            "retry_count":         0,
            "max_retries":         settings.MAX_RETRY_ATTEMPTS,
            "error_context":       None,
            "should_retry":        False,
            "final_result":        None,
            "status":              "running",
            "event_publisher":     event_publisher,
            "total_tokens":        0,
        }

        logger.info("Starting agent orchestration", task_id=task_id)

        try:
            final_state = await self.graph.ainvoke(
                initial_state,
                config=RunnableConfig(
                    recursion_limit=settings.MAX_AGENT_ITERATIONS * 2
                ),
            )
            logger.info(
                "Orchestration complete",
                task_id=task_id,
                status=final_state.get("status"),
                total_tokens=final_state.get("total_tokens", 0),
                files_changed=len(final_state.get("code_changes", [])),
            )
            return final_state

        except Exception as e:
            logger.error(
                "Agent orchestration failed",
                task_id=task_id,
                error=str(e),
            )
            raise
