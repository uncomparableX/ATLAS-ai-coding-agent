"""
Test Runner
Detects the test framework in a repository and runs tests
inside the Docker sandbox. Returns structured results.
"""
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import structlog

from app.services.execution.docker_executor import DockerExecutor, ExecutionResult
from app.core.config import settings

logger = structlog.get_logger(__name__)


# ─── Test result model ────────────────────────────────────────────────────────

class TestResult:
    def __init__(
        self,
        passed: int,
        failed: int,
        errors: int,
        skipped: int,
        total: int,
        duration_ms: int,
        coverage_pct: Optional[float],
        raw_output: str,
        exit_code: int,
        framework: str,
        command: str,
    ):
        self.passed       = passed
        self.failed       = failed
        self.errors       = errors
        self.skipped      = skipped
        self.total        = total
        self.duration_ms  = duration_ms
        self.coverage_pct = coverage_pct
        self.raw_output   = raw_output
        self.exit_code    = exit_code
        self.framework    = framework
        self.command      = command
        self.success      = exit_code == 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed":       self.passed,
            "failed":       self.failed,
            "errors":       self.errors,
            "skipped":      self.skipped,
            "total":        self.total,
            "duration_ms":  self.duration_ms,
            "coverage_pct": self.coverage_pct,
            "raw_output":   self.raw_output,
            "exit_code":    self.exit_code,
            "framework":    self.framework,
            "command":      self.command,
            "success":      self.success,
        }


# ─── Framework detection ──────────────────────────────────────────────────────

def detect_test_framework(repo_path: str) -> str:
    """
    Detect the primary test framework for a repository.
    Returns one of: pytest | jest | go_test | npm_test | unknown
    """
    base = Path(repo_path)

    # Python
    if (base / "pytest.ini").exists() or (base / "pyproject.toml").exists():
        try:
            content = (base / "pyproject.toml").read_text(encoding="utf-8") \
                if (base / "pyproject.toml").exists() else ""
            if "pytest" in content or (base / "pytest.ini").exists():
                return "pytest"
        except OSError:
            pass

    if any((base / f).exists() for f in ["setup.py", "setup.cfg", "requirements.txt"]):
        # Check for pytest in requirements
        for req_file in ["requirements.txt", "requirements-dev.txt"]:
            rf = base / req_file
            if rf.exists():
                try:
                    if "pytest" in rf.read_text(encoding="utf-8"):
                        return "pytest"
                except OSError:
                    pass

    if list(base.rglob("test_*.py")) or list(base.rglob("*_test.py")):
        return "pytest"

    # JavaScript / TypeScript
    pkg = base / "package.json"
    if pkg.exists():
        try:
            import json
            data = json.loads(pkg.read_text(encoding="utf-8"))
            scripts = data.get("scripts", {})
            if "test" in scripts:
                test_cmd = scripts["test"]
                if "jest" in test_cmd:
                    return "jest"
                if "vitest" in test_cmd:
                    return "vitest"
                return "npm_test"
        except Exception:
            pass
        return "npm_test"

    # Go
    if list(base.rglob("*_test.go")):
        return "go_test"

    # Rust
    if (base / "Cargo.toml").exists():
        return "cargo_test"

    return "unknown"


# ─── Output parsers ───────────────────────────────────────────────────────────

def parse_pytest_output(output: str, exit_code: int) -> Dict[str, Any]:
    """Extract pass/fail counts from pytest output."""
    passed = failed = errors = skipped = 0
    coverage_pct: Optional[float] = None

    # Match: "3 passed, 1 failed, 2 errors in 0.42s"
    summary = re.search(
        r"(\d+) passed|(\d+) failed|(\d+) error|(\d+) skipped",
        output,
        re.IGNORECASE,
    )
    if summary:
        for m in re.finditer(r"(\d+) (passed|failed|error|skipped)", output, re.IGNORECASE):
            n   = int(m.group(1))
            lbl = m.group(2).lower()
            if lbl == "passed":
                passed = n
            elif lbl == "failed":
                failed = n
            elif lbl == "error":
                errors = n
            elif lbl == "skipped":
                skipped = n

    # Coverage line: "TOTAL    1234    456    63%"
    cov_match = re.search(r"TOTAL\s+\d+\s+\d+\s+(\d+)%", output)
    if cov_match:
        coverage_pct = float(cov_match.group(1))

    total = passed + failed + errors
    return {
        "passed":       passed,
        "failed":       failed,
        "errors":       errors,
        "skipped":      skipped,
        "total":        max(total, 1) if exit_code == 0 else total,
        "coverage_pct": coverage_pct,
    }


def parse_jest_output(output: str, exit_code: int) -> Dict[str, Any]:
    """Extract pass/fail counts from Jest output."""
    passed = failed = 0

    # "Tests: 3 passed, 1 failed, 4 total"
    for m in re.finditer(r"(\d+) (passed|failed)", output, re.IGNORECASE):
        n   = int(m.group(1))
        lbl = m.group(2).lower()
        if lbl == "passed":
            passed = n
        elif lbl == "failed":
            failed = n

    total_m = re.search(r"(\d+) total", output, re.IGNORECASE)
    total   = int(total_m.group(1)) if total_m else passed + failed

    cov_m   = re.search(r"All files\s+\|\s+([\d.]+)", output)
    cov_pct = float(cov_m.group(1)) if cov_m else None

    return {
        "passed":       passed,
        "failed":       failed,
        "errors":       0,
        "skipped":      0,
        "total":        total,
        "coverage_pct": cov_pct,
    }


def parse_go_output(output: str, exit_code: int) -> Dict[str, Any]:
    """Extract pass/fail from go test output."""
    passed = output.count("--- PASS")
    failed = output.count("--- FAIL")
    return {
        "passed":       passed,
        "failed":       failed,
        "errors":       1 if exit_code != 0 and failed == 0 else 0,
        "skipped":      output.count("--- SKIP"),
        "total":        passed + failed,
        "coverage_pct": None,
    }


# ─── Test Runner ──────────────────────────────────────────────────────────────

class TestRunner:
    """
    Detects and runs tests for a repository inside the Docker sandbox.
    Returns a structured TestResult.
    """

    FRAMEWORK_COMMANDS = {
        "pytest":     "pytest --tb=short -q 2>&1",
        "jest":       "npx jest --passWithNoTests 2>&1",
        "vitest":     "npx vitest run 2>&1",
        "npm_test":   "npm test -- --passWithNoTests 2>&1",
        "go_test":    "go test ./... 2>&1",
        "cargo_test": "cargo test 2>&1",
        "unknown":    "echo '[AgentForge] No test framework detected'",
    }

    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.executor  = DockerExecutor()
        self.framework = detect_test_framework(repo_path)
        self.command   = self.FRAMEWORK_COMMANDS.get(
            self.framework, self.FRAMEWORK_COMMANDS["unknown"]
        )

    async def run(
        self,
        task_id: str,
        custom_command: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> TestResult:
        """Execute tests and return a parsed TestResult."""
        cmd     = custom_command or self.command
        timeout = timeout or settings.SANDBOX_TIMEOUT_SECONDS

        language_map = {
            "pytest":     "python",
            "jest":       "javascript",
            "vitest":     "javascript",
            "npm_test":   "javascript",
            "go_test":    "go",
            "cargo_test": "rust",
        }
        language = language_map.get(self.framework)

        logger.info(
            "Running tests",
            framework=self.framework,
            command=cmd,
            task_id=task_id,
        )

        result: ExecutionResult = await self.executor.run(
            command=cmd,
            repo_path=self.repo_path,
            task_id=task_id,
            language=language,
            timeout=timeout,
        )

        combined = result.stdout
        if result.stderr:
            combined += f"\nSTDERR:\n{result.stderr}"

        # Parse framework-specific output
        parser_map = {
            "pytest":     parse_pytest_output,
            "jest":       parse_jest_output,
            "vitest":     parse_jest_output,
            "go_test":    parse_go_output,
            "cargo_test": parse_go_output,
        }
        parser = parser_map.get(self.framework)
        counts = parser(combined, result.exit_code) if parser else {
            "passed": 0 if result.exit_code != 0 else 1,
            "failed": 0 if result.exit_code == 0 else 1,
            "errors": 0, "skipped": 0, "total": 1,
            "coverage_pct": None,
        }

        return TestResult(
            passed=counts["passed"],
            failed=counts["failed"],
            errors=counts["errors"],
            skipped=counts["skipped"],
            total=counts["total"],
            duration_ms=result.duration_ms,
            coverage_pct=counts.get("coverage_pct"),
            raw_output=combined[:8000],
            exit_code=result.exit_code,
            framework=self.framework,
            command=cmd,
        )
