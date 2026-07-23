"""Execucao segura de codigo gerado."""

import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class ExecutionResult:
    """Resultado da execucao de codigo."""

    success: bool
    output: str
    error: str
    exit_code: int
    execution_time_ms: float
    language: str
    timed_out: bool = False


class CodeRunner:
    """Executa codigo gerado de forma segura."""

    def __init__(self, timeout_seconds: int = 10):
        self.timeout_seconds = timeout_seconds

    def run(self, code: str, language: str = "python") -> ExecutionResult:
        """Executa codigo e retorna o resultado."""
        if language == "python":
            return self._run_python(code)
        elif language in ("javascript", "js"):
            return self._run_javascript(code)
        else:
            return ExecutionResult(
                success=False,
                output="",
                error=f"Linguagem '{language}' nao suportada para execucao",
                exit_code=1,
                execution_time_ms=0,
                language=language,
            )

    def _run_python(self, code: str) -> ExecutionResult:
        """Executa codigo Python em subprocess isolado."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as f:
            f.write(code)
            temp_path = f.name

        try:
            start = time.time()
            proc = subprocess.run(
                ["python", temp_path],
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
            )
            elapsed = (time.time() - start) * 1000

            return ExecutionResult(
                success=proc.returncode == 0,
                output=proc.stdout.strip(),
                error=proc.stderr.strip(),
                exit_code=proc.returncode,
                execution_time_ms=round(elapsed, 2),
                language="python",
            )
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                success=False,
                output="",
                error=f"Timeout apos {self.timeout_seconds}s",
                exit_code=-1,
                execution_time_ms=self.timeout_seconds * 1000,
                language="python",
                timed_out=True,
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                output="",
                error=str(e),
                exit_code=1,
                execution_time_ms=0,
                language="python",
            )
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def _run_javascript(self, code: str) -> ExecutionResult:
        """Executa codigo JavaScript via Node.js."""
        try:
            start = time.time()
            proc = subprocess.run(
                ["node", "-e", code],
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
            )
            elapsed = (time.time() - start) * 1000

            return ExecutionResult(
                success=proc.returncode == 0,
                output=proc.stdout.strip(),
                error=proc.stderr.strip(),
                exit_code=proc.returncode,
                execution_time_ms=round(elapsed, 2),
                language="javascript",
            )
        except FileNotFoundError:
            return ExecutionResult(
                success=False,
                output="",
                error="Node.js nao encontrado. Instale o Node.js para executar JavaScript.",
                exit_code=1,
                execution_time_ms=0,
                language="javascript",
            )
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                success=False,
                output="",
                error=f"Timeout apos {self.timeout_seconds}s",
                exit_code=-1,
                execution_time_ms=self.timeout_seconds * 1000,
                language="javascript",
                timed_out=True,
            )
