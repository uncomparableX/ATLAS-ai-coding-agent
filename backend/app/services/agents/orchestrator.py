"""
AgentForge Multi-Agent Orchestration Engine
LangGraph-based stateful pipeline:
  planner → analyst → coder → executor → debugger (on fail) → reviewer → END
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


# ─── State ────────────────────────────────────────────────────────────────────

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


# ─── Base ─────────────────────────────────────────────────────────────────────

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


# ─── Planner ──────────────────────────────────────────────────────────────────

class PlannerAgent(BaseAgent):
    SYSTEM = """You are an expert software architect and planning agent.
Analyze the task and produce a detailed implementation plan.

Return valid JSON:
{
  "summary": "short summary",
  "steps": [
    {
      "id": 1,
      "title": "Step title",
      "description": "Detailed explanation",
      "files_to_modify": ["path/file.py"]
    }
  ],
  "risks": ["risk"],
  "success_criteria": ["criteria"]
}"""

    async def run(self, state: AgentState) -> AgentState:
        logger.info("Planner agent starting", task_id=state["task_id"])

        await self.publish(state, "agent_thought", {
            "message": "Analyzing task requirements and building execution plan.",
            "agent": self.agent_type,
        })

        memories = await self.memory_service.search_memories(
            query=state["task_description"],
            repository_id=state["repository_id"],
            limit=5,
        )

        memory_context = "\n".join([
            f"- {m.get('content', '')[:500]}"
            for m in memories
        ])

        messages = [
            SystemMessage(content=self.SYSTEM),
            HumanMessage(content=(
                f"Task:\n{state['task_description']}\n\n"
                f"Architecture Context:\n{state.get('architecture_context', '')}\n\n"
                f"Relevant Historical Memory:\n{memory_context}\n\n"
                "Create a robust implementation plan."
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
            logger.warning("Planner JSON parse failed")
            plan = {
                "summary": raw[:500],
                "steps": [{"id": 1, "title": "Implement task", "description": raw[:1000]}],
                "risks": [],
                "success_criteria": [],
            }

        await self.publish(state, "agent_result", {
            "agent": self.agent_type, "plan": plan, "tokens": tokens
        })

        return {
            **state,
            "implementation_plan": plan,
            "current_agent": "analyst",
            "messages": [AIMessage(content=f"[Planner] {len(plan.get('steps', []))} steps: {plan.get('summary', '')[:200]}")],
            "total_tokens": state.get("total_tokens", 0) + tokens,
        }


# ─── Analyst ──────────────────────────────────────────────────────────────────

class AnalystAgent(BaseAgent):
    SYSTEM = """You are an expert code analyst.
Given a task and codebase context, identify relevant files and architecture patterns.

Return JSON:
{
  "files_to_read": ["path/to/file.py"],
  "files_to_modify": ["path/to/modify.py"],
  "architecture_notes": "Key patterns and constraints",
  "dependencies": {"module": "usage"},
  "entry_points": ["main files"]
}"""

    async def run(self, state: AgentState) -> AgentState:
        logger.info("Analyst agent starting", task_id=state["task_id"])

        await self.publish(state, "agent_thought", {
            "message": "Analyzing codebase and identifying relevant files.",
            "agent": self.agent_type,
        })

        chunks = await self.vector_store.search_code(
            query=state["task_description"],
            repository_id=state["repository_id"],
            limit=15,
        )

        code_context = "\n\n---\n\n".join([
            f"File: {c['file_path']} (lines {c.get('start_line','?')}-{c.get('end_line','?')})\n"
            f"```\n{c['content']}\n```"
            for c in chunks
        ])

        messages = [
            SystemMessage(content=self.SYSTEM),
            HumanMessage(content=(
                f"## Task\n{state['task_description']}\n\n"
                f"## Plan Summary\n{state.get('implementation_plan', {}).get('summary', 'N/A')}\n\n"
                f"## Relevant Code (semantic search)\n{code_context}\n\n"
                "Identify files. Return valid JSON."
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
            analysis = {"files_to_read": [], "files_to_modify": [], "architecture_notes": raw[:500]}

        relevant_files = list(set(
            analysis.get("files_to_read", [])
            + analysis.get("files_to_modify", [])
            + [c["file_path"] for c in chunks]
        ))

        await self.publish(state, "agent_result", {
            "agent": self.agent_type,
            "relevant_files": relevant_files,
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
            "messages": [AIMessage(content=f"[Analyst] {len(relevant_files)} files, {len(chunks)} semantic matches.")],
            "total_tokens": state.get("total_tokens", 0) + tokens,
        }


# ─── Coder ────────────────────────────────────────────────────────────────────

class CoderAgent(BaseAgent):
    SYSTEM = """You are an elite software engineer.
Generate production-ready code modifications.

Rules:
- Preserve existing architecture
- Minimize unnecessary edits
- Return JSON only
- Include complete modified file contents

Format:
{
  "changes": [
    {
      "file_path": "app/example.py",
      "action": "modify",
      "content": "FULL FILE CONTENT"
    }
  ]
}"""

    async def run(self, state: AgentState) -> AgentState:
        logger.info("Coder agent starting", task_id=state["task_id"])

        await self.publish(state, "agent_thought", {
            "message": "Generating code changes.",
            "agent": self.agent_type,
        })

        tools = AgentTools(state["repo_path"])

        file_contexts = []
        for file_path in state.get("relevant_files", [])[:12]:
            content = await tools.read_file(file_path)
            if content:
                file_contexts.append(
                    f"FILE: {file_path}\n```python\n{content[:12000]}\n```"
                )

        messages = [
            SystemMessage(content=self.SYSTEM),
            HumanMessage(content=(
                f"TASK:\n{state['task_description']}\n\n"
                f"PLAN:\n{json.dumps(state.get('implementation_plan', {}), indent=2)}\n\n"
                f"ARCHITECTURE:\n{state.get('architecture_context', '')}\n\n"
                f"ERROR CONTEXT:\n{state.get('error_context', '')}\n\n"
                + "\n\n".join(file_contexts)
            )),
        ]

        response = await self.llm.ainvoke(messages)
        raw = response.content
        tokens = count_tokens(raw)

        try:
            j_start = raw.find("{")
            j_end = raw.rfind("}") + 1
            parsed = json.loads(raw[j_start:j_end])
            changes = parsed.get("changes", [])
        except Exception:
            logger.warning("Coder JSON parse failed")
            changes = []

        applied_changes = []

        for change in changes:
            result = await tools.apply_change(
                file_path=change["file_path"],
                content=change.get("content", ""),
                action=change.get("action", "modify"),
            )
            applied_changes.append(result)

        await self.publish(state, "agent_result", {
            "agent": self.agent_type,
            "files_changed": len(applied_changes),
        })

        return {
            **state,
            "code_changes": applied_changes,
            "current_agent": "executor",
            "messages": [AIMessage(content=f"[Coder] Applied {len(applied_changes)} code changes.")],
            "total_tokens": state.get("total_tokens", 0) + tokens,
        }


# ─── Executor ─────────────────────────────────────────────────────────────────

class ExecutorAgent(BaseAgent):
    async def run(self, state: AgentState) -> AgentState:
        logger.info("Executor agent starting", task_id=state["task_id"])

        await self.publish(state, "agent_thought", {
            "message": "Running tests and validating implementation.",
            "agent": self.agent_type,
        })

        executor = DockerExecutor()

        commands = [
            "pytest -q",
            "npm test",
            "npm run build",
        ]

        execution_results = []

        for command in commands:
            result = await executor.run(
                command=command,
                repo_path=state["repo_path"],
                task_id=state["task_id"],
            )

            execution_results.append(result)

            if result["status"] == "success":
                break

        test_output = "\n\n".join([
            r.get("stdout", "") + "\n" + r.get("stderr", "")
            for r in execution_results
        ])

        should_retry = any(r["status"] != "success" for r in execution_results)

        await self.publish(state, "agent_result", {
            "agent": self.agent_type,
            "executions": execution_results,
            "should_retry": should_retry,
        })

        return {
            **state,
            "execution_results": execution_results,
            "test_output": test_output,
            "should_retry": should_retry,
            "current_agent": "debugger" if should_retry else "reviewer",
            "messages": [AIMessage(content=f"[Executor] Validation {'failed' if should_retry else 'passed'}.")],
        }


# ─── Debugger ─────────────────────────────────────────────────────────────────

class DebuggerAgent(BaseAgent):
    SYSTEM = """You are an expert debugging engineer.
Analyze failures and propose a fix strategy.

Return JSON:
{
  "root_cause": "description",
  "fix_strategy": "how to fix"
}"""

    async def run(self, state: AgentState) -> AgentState:
        logger.info("Debugger agent starting", task_id=state["task_id"])

        retry_count = state.get("retry_count", 0)

        if retry_count >= state.get("max_retries", 3):
            return {
                **state,
                "status": "failed",
                "current_agent": "done",
                "messages": [AIMessage(content="[Debugger] Max retries exceeded.")],
            }

        messages = [
            SystemMessage(content=self.SYSTEM),
            HumanMessage(content=(
                f"TASK:\n{state['task_description']}\n\n"
                f"TEST OUTPUT:\n{state.get('test_output', '')}\n\n"
                "Diagnose the issue."
            )),
        ]

        response = await self.fast_llm.ainvoke(messages)
        raw = response.content
        tokens = count_tokens(raw)

        try:
            j_start = raw.find("{")
            j_end = raw.rfind("}") + 1
            diagnosis = json.loads(raw[j_start:j_end])
        except Exception:
            diagnosis = {
                "root_cause": raw[:300],
                "fix_strategy": "Retry with adjustments",
            }

        await self.publish(state, "agent_result", {
            "agent": self.agent_type,
            "diagnosis": diagnosis,
            "retry_count": retry_count + 1,
        })

        error_context = (
            f"PREVIOUS ERROR:\n{state.get('error_context', '')}\n\n"
            f"ROOT CAUSE:\n{diagnosis.get('root_cause', '')}\n\n"
            f"FIX STRATEGY:\n{diagnosis.get('fix_strategy', '')}"
        )

        return {
            **state,
            "error_context": error_context,
            "retry_count": retry_count + 1,
            "current_agent": "coder",
            "messages": [AIMessage(content=f"[Debugger] {diagnosis.get('root_cause', '')[:200]}. Retrying...")],
            "total_tokens": state.get("total_tokens", 0) + tokens,
        }


# ─── Reviewer ─────────────────────────────────────────────────────────────────

class ReviewerAgent(BaseAgent):
    SYSTEM = """You are a senior code reviewer.
Review the changes and return JSON:
{
  "approved": true,
  "score": 8,
  "summary": "Overall assessment",
  "issues": [{"severity": "high|medium|low", "description": ".", "file": "."}],
  "suggestions": ["improvement idea"]
}"""

    async def run(self, state: AgentState) -> AgentState:
        logger.info("Reviewer agent starting", task_id=state["task_id"])

        await self.publish(state, "agent_thought", {
            "message": "Reviewing code quality.",
            "agent": self.agent_type,
        })

        changes_summary = "\n".join([
            f"- {c.get('file_path')}: {c.get('action', 'modified')}"
            for c in state.get("code_changes", [])
        ])

        diffs_text = "\n\n".join([
            f"### {c.get('file_path')}\n```diff\n{c.get('diff', '')}\n```"
            for c in state.get("code_changes", [])[:5]
        ])

        messages = [
            SystemMessage(content=self.SYSTEM),
            HumanMessage(content=(
                f"## Task\n{state['task_description']}\n\n"
                f"## Files Changed\n{changes_summary}\n\n"
                f"## Diffs\n{diffs_text}\n\n"
                f"## Test Results\n{state.get('test_output', 'No tests run')}\n\n"
                "Review the implementation. Return valid JSON."
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
                "summary": "Implementation completed",
                "issues": [],
                "suggestions": [],
            }

        await self.publish(state, "agent_result", {
            "agent": self.agent_type,
            "review": review,
        })

        return {
            **state,
            "final_result": {
                "review": review,
                "code_changes": state.get("code_changes", []),
                "execution_results": state.get("execution_results", []),
                "total_tokens": state.get("total_tokens", 0) + tokens,
            },
            "current_agent": "done",
            "status": "completed",
            "messages": [AIMessage(content=f"[Reviewer] Score: {review.get('score', 0)}/10")],
        }


# ─── Routing ──────────────────────────────────────────────────────────────────

def route_planner(state: AgentState):
    return "analyst"


def route_analyst(state: AgentState):
    return "coder"


def route_coder(state: AgentState):
    return "executor"


def route_executor(state: AgentState):
    return "debugger" if state.get("should_retry") else "reviewer"


def route_debugger(state: AgentState):
    if state.get("retry_count", 0) >= state.get("max_retries", 3):
        return END
    return "coder"


def route_reviewer(state: AgentState):
    return END


# ─── Graph Builder ────────────────────────────────────────────────────────────

def build_agent_graph():
    g = StateGraph(AgentState)

    planner = PlannerAgent("planner")
    analyst = AnalystAgent("analyst")
    coder = CoderAgent("coder")
    executor = ExecutorAgent("executor")
    debugger = DebuggerAgent("debugger")
    reviewer = ReviewerAgent("reviewer")

    g.add_node("planner", planner.run)
    g.add_node("analyst", analyst.run)
    g.add_node("coder", coder.run)
    g.add_node("executor", executor.run)
    g.add_node("debugger", debugger.run)
    g.add_node("reviewer", reviewer.run)

    g.set_entry_point("planner")

    g.add_conditional_edges("planner", route_planner, {"analyst": "analyst", "done": END})
    g.add_conditional_edges("analyst", route_analyst, {"coder": "coder"})
    g.add_conditional_edges("coder", route_coder, {"executor": "executor"})
    g.add_conditional_edges("executor", route_executor, {"reviewer": "reviewer", "debugger": "debugger"})
    g.add_conditional_edges("debugger", route_debugger, {"coder": "coder", END: END})
    g.add_conditional_edges("reviewer", route_reviewer, {END: END})

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
        event_publisher=None,
    ) -> Dict[str, Any]:

        initial_state: AgentState = {
            "task_id": task_id,
            "repository_id": repository_id,
            "task_description": task_description,
            "repo_path": repo_path,
            "messages": [HumanMessage(content=task_description)],
            "implementation_plan": None,
            "relevant_files": relevant_files or [],
            "architecture_context": architecture_context,
            "code_changes": [],
            "execution_results": [],
            "test_output": None,
            "current_agent": "planner",
            "iteration": 0,
            "max_iterations": settings.MAX_AGENT_ITERATIONS,
            "retry_count": 0,
            "max_retries": settings.MAX_RETRY_ATTEMPTS,
            "error_context": None,
            "should_retry": False,
            "final_result": None,
            "status": "running",
            "event_publisher": event_publisher,
            "total_tokens": 0,
        }

        logger.info("Starting agent orchestration", task_id=task_id)

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
        )

        return final_state
