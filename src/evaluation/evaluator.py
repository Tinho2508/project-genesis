"""Avaliacao de qualidade do codigo gerado."""

import ast
import logging
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class EvaluationResult:
    """Resultado da avaliacao de um codigo gerado."""

    code: str
    language: str
    is_valid_syntax: bool = False
    is_executable: bool = False
    execution_time_ms: float = 0.0
    output: str = ""
    error: str = ""
    score: float = 0.0
    metrics: dict = field(default_factory=dict)

    @property
    def status(self) -> str:
        if self.is_valid_syntax and self.is_executable:
            return "APROVADO"
        elif self.is_valid_syntax:
            return "SINTAXE_OK"
        else:
            return "ERRO"


class CodeEvaluator:
    """Avalia qualidade do codigo gerado."""

    def __init__(self, timeout_seconds: int = 5):
        self.timeout_seconds = timeout_seconds

    def evaluate(self, code: str, language: str = "python") -> EvaluationResult:
        """Avalia um codigo gerado completamente."""
        result = EvaluationResult(code=code, language=language)

        if language == "python":
            self._evaluate_python(result)
        elif language in ("javascript", "js"):
            self._evaluate_javascript(result)
        else:
            result.metrics["note"] = f"Avaliacao basica para {language}"

        result.score = self._calculate_score(result)
        return result

    def _evaluate_python(self, result: EvaluationResult) -> None:
        """Avalia codigo Python."""
        # 1. Verificar sintaxe
        try:
            ast.parse(result.code)
            result.is_valid_syntax = True
        except SyntaxError as e:
            result.error = f"Erro de sintaxe: {e}"
            result.metrics["syntax_error"] = str(e)
            return

        # 2. Metricas estaticas
        result.metrics.update(self._analyze_python_ast(result.code))

        # 3. Tentar executar
        try:
            exec_result = self._execute_python(result.code)
            result.is_executable = exec_result["success"]
            result.output = exec_result["output"]
            result.execution_time_ms = exec_result["time_ms"]
            if not exec_result["success"]:
                result.error = exec_result["error"]
        except Exception as e:
            result.error = f"Erro na execucao: {e}"

    def _evaluate_javascript(self, result: EvaluationResult) -> None:
        """Avalia codigo JavaScript (basico, sem Node.js)."""
        # Verificacoes basicas de sintaxe
        open_braces = result.code.count("{")
        close_braces = result.code.count("}")
        open_parens = result.code.count("(")
        close_parens = result.code.count(")")

        result.metrics["braces_balanced"] = open_braces == close_braces
        result.metrics["parens_balanced"] = open_parens == close_parens

        if result.metrics["braces_balanced"] and result.metrics["parens_balanced"]:
            result.is_valid_syntax = True
            result.metrics["note"] = "Verificacao basica (Node.js necessario para execucao)"
        else:
            result.error = "Chaves ou parenteses desbalanceados"

    def _analyze_python_ast(self, code: str) -> dict:
        """Analise estatica do AST do codigo Python."""
        tree = ast.parse(code)

        metrics = {
            "num_functions": 0,
            "num_classes": 0,
            "num_imports": 0,
            "num_variables": 0,
            "max_depth": 0,
            "has_docstring": False,
            "has_type_hints": False,
            "lines_of_code": len(code.splitlines()),
            "lines_of_code_stripped": len([l for l in code.splitlines() if l.strip()]),
        }

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                metrics["num_functions"] += 1
                if ast.get_docstring(node):
                    metrics["has_docstring"] = True
                if node.returns:
                    metrics["has_type_hints"] = True
            elif isinstance(node, ast.ClassDef):
                metrics["num_classes"] += 1
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                metrics["num_imports"] += 1
            elif isinstance(node, ast.Assign):
                metrics["num_variables"] += len(node.targets)

        return metrics

    def _execute_python(self, code: str) -> dict:
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

            return {
                "success": proc.returncode == 0,
                "output": proc.stdout.strip(),
                "error": proc.stderr.strip(),
                "time_ms": round(elapsed, 2),
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "output": "",
                "error": f"Timeout apos {self.timeout_seconds}s",
                "time_ms": self.timeout_seconds * 1000,
            }
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": str(e),
                "time_ms": 0,
            }
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def _calculate_score(self, result: EvaluationResult) -> float:
        """Calcula score de 0 a 10 baseado nas metricas."""
        score = 0.0

        # Sintaxe valida (4 pontos)
        if result.is_valid_syntax:
            score += 4.0

        # Executavel (3 pontos)
        if result.is_executable:
            score += 3.0

        # Metricas de qualidade (3 pontos)
        metrics = result.metrics
        if metrics.get("num_functions", 0) > 0:
            score += 1.0
        if metrics.get("has_docstring"):
            score += 0.5
        if metrics.get("has_type_hints"):
            score += 0.5
        if metrics.get("lines_of_code_stripped", 0) > 0:
            score += 1.0

        return min(round(score, 1), 10.0)

    def batch_evaluate(
        self, codes: list[str], language: str = "python"
    ) -> list[EvaluationResult]:
        """Avalia multiplos codigos."""
        return [self.evaluate(code, language) for code in codes]
