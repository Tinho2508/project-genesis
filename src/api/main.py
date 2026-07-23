"""API REST do Project Genesis."""

import logging
import sys
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Adiciona o diretorio raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Project Genesis API",
    description="API de geracao de codigo com Inteligencia Artificial",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instancias globais (lazy loading)
_generator = None
_evaluator = None
_history = None
_lang_manager = None


def _get_generator():
    global _generator
    if _generator is None:
        from src.inference import CodeGenerator
        _generator = CodeGenerator()
        _generator.load_model()
    return _generator


def _get_evaluator():
    global _evaluator
    if _evaluator is None:
        from src.evaluation.evaluator import CodeEvaluator
        _evaluator = CodeEvaluator()
    return _evaluator


def _get_history():
    global _history
    if _history is None:
        from src.history.manager import HistoryManager
        _history = HistoryManager()
    return _history


def _get_lang_manager():
    global _lang_manager
    if _lang_manager is None:
        from src.languages.support import LanguageManager
        _lang_manager = LanguageManager()
    return _lang_manager


# --- Modelos de Request/Response ---

class GenerateRequest(BaseModel):
    prompt: str
    language: str = "python"
    max_tokens: int = 256
    temperature: float = 0.7
    execute: bool = False


class GenerateResponse(BaseModel):
    prompt: str
    code: str
    language: str
    score: float = 0.0
    execution_output: str = ""
    execution_error: str = ""


class HistoryEntryResponse(BaseModel):
    id: str
    prompt: str
    code: str
    language: str
    timestamp: str
    is_favorite: bool
    score: float


class StatsResponse(BaseModel):
    total: int
    favorites: int
    languages: dict
    average_score: float


# --- Endpoints ---

@app.get("/")
def root():
    return {
        "name": "Project Genesis API",
        "version": "0.1.0",
        "status": "online",
        "endpoints": {
            "generate": "POST /generate",
            "languages": "GET /languages",
            "history": "GET /history",
            "favorites": "GET /history/favorites",
            "stats": "GET /history/stats",
        },
    }


@app.post("/generate", response_model=GenerateResponse)
def generate_code(req: GenerateRequest):
    """Gera codigo a partir de uma instrucao em linguagem natural."""
    try:
        generator = _get_generator()
        code = generator.generate(
            prompt=req.prompt,
            max_new_tokens=req.max_tokens,
            temperature=req.temperature,
        )

        result = GenerateResponse(
            prompt=req.prompt,
            code=code,
            language=req.language,
        )

        # Avaliar
        if req.language == "python":
            evaluator = _get_evaluator()
            eval_result = evaluator.evaluate(code, req.language)
            result.score = eval_result.score

        # Executar se solicitado
        if req.execute and req.language in ("python", "javascript"):
            from src.executor.runner import CodeRunner
            runner = CodeRunner()
            exec_result = runner.run(code, req.language)
            result.execution_output = exec_result.output
            result.execution_error = exec_result.error

        # Salvar no historico
        history = _get_history()
        history.add(
            prompt=req.prompt,
            code=code,
            language=req.language,
            score=result.score,
            execution_output=result.execution_output,
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/languages")
def list_languages():
    """Lista todas as linguagens suportadas."""
    manager = _get_lang_manager()
    langs = manager.list_supported()
    return {
        "languages": [
            {
                "name": l.name,
                "extension": l.extension,
                "supports_execution": l.supports_execution,
            }
            for l in langs
        ]
    }


@app.get("/history", response_model=list[HistoryEntryResponse])
def get_history(limit: int = 20):
    """Retorna o historico de geracoes."""
    history = _get_history()
    entries = history.get_recent(limit)
    return entries


@app.get("/history/favorites", response_model=list[HistoryEntryResponse])
def get_favorites():
    """Retorna as geracoes favoritas."""
    history = _get_history()
    return history.get_favorites()


@app.post("/history/{entry_id}/favorite")
def toggle_favorite(entry_id: str):
    """Alterna o status de favorito de uma entrada."""
    history = _get_history()
    is_fav = history.toggle_favorite(entry_id)
    if is_fav is None:
        raise HTTPException(status_code=404, detail="Entrada nao encontrada")
    return {"id": entry_id, "is_favorite": is_fav}


@app.delete("/history/{entry_id}")
def delete_history_entry(entry_id: str):
    """Remove uma entrada do historico."""
    history = _get_history()
    deleted = history.delete(entry_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Entrada nao encontrada")
    return {"deleted": True}


@app.get("/history/search")
def search_history(q: str):
    """Busca no historico."""
    history = _get_history()
    results = history.search(q)
    return {"results": results, "count": len(results)}


@app.get("/history/stats", response_model=StatsResponse)
def get_stats():
    """Retorna estatisticas do historico."""
    history = _get_history()
    return history.stats()


@app.post("/history/undo")
def undo():
    "Desfaz a ultima operacao no historico."
    history = _get_history()
    success = history.undo()
    return {"undone": success}


@app.post("/history/redo")
def redo():
    """Refaz a ultima operacao desfeita."""
    history = _get_history()
    success = history.redo()
    return {"redone": success}
