"""Gerenciamento de historico de geracoes de codigo."""

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class GenerationEntry:
    """Uma entrada no historico de geracoes."""

    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    prompt: str = ""
    code: str = ""
    language: str = "python"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    is_favorite: bool = False
    score: float = 0.0
    execution_output: str = ""
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "GenerationEntry":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class HistoryManager:
    """Gerencia historico de geracoes de codigo."""

    def __init__(self, history_file: str = "outputs/history.json"):
        self.history_file = Path(history_file)
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        self.entries: list[GenerationEntry] = []
        self._undo_stack: list[list[dict]] = []
        self._redo_stack: list[list[dict]] = []
        self.load()

    def load(self) -> None:
        """Carrega historico do arquivo."""
        if self.history_file.exists():
            data = json.loads(self.history_file.read_text(encoding="utf-8"))
            self.entries = [GenerationEntry.from_dict(e) for e in data]
        else:
            self.entries = []

    def save(self) -> None:
        """Salva historico no arquivo."""
        data = [e.to_dict() for e in self.entries]
        self.history_file.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def add(
        self,
        prompt: str,
        code: str,
        language: str = "python",
        score: float = 0.0,
        execution_output: str = "",
        tags: list[str] = None,
    ) -> GenerationEntry:
        """Adiciona uma nova entrada ao historico."""
        self._save_undo_state()

        entry = GenerationEntry(
            prompt=prompt,
            code=code,
            language=language,
            score=score,
            execution_output=execution_output,
            tags=tags or [],
        )
        self.entries.append(entry)
        self.save()
        return entry

    def get(self, entry_id: str) -> Optional[GenerationEntry]:
        """Busca uma entrada por ID."""
        for e in self.entries:
            if e.id == entry_id:
                return e
        return None

    def toggle_favorite(self, entry_id: str) -> bool:
        """Alterna o status de favorito de uma entrada."""
        entry = self.get(entry_id)
        if entry:
            self._save_undo_state()
            entry.is_favorite = not entry.is_favorite
            self.save()
            return entry.is_favorite
        return False

    def search(self, query: str) -> list[GenerationEntry]:
        """Busca no historico por prompt ou codigo."""
        query_lower = query.lower()
        return [
            e
            for e in self.entries
            if query_lower in e.prompt.lower() or query_lower in e.code.lower()
        ]

    def get_favorites(self) -> list[GenerationEntry]:
        """Retorna apenas as entradas favoritas."""
        return [e for e in self.entries if e.is_favorite]

    def get_by_language(self, language: str) -> list[GenerationEntry]:
        """Retorna entradas filtradas por linguagem."""
        return [e for e in self.entries if e.language == language]

    def get_recent(self, limit: int = 10) -> list[GenerationEntry]:
        """Retorna as N entradas mais recentes."""
        return sorted(self.entries, key=lambda e: e.timestamp, reverse=True)[:limit]

    def delete(self, entry_id: str) -> bool:
        """Remove uma entrada do historico."""
        entry = self.get(entry_id)
        if entry:
            self._save_undo_state()
            self.entries.remove(entry)
            self.save()
            return True
        return False

    def clear(self) -> int:
        """Limpa todo o historico. Retorna numero de entradas removidas."""
        self._save_undo_state()
        count = len(self.entries)
        self.entries = []
        self.save()
        return count

    def undo(self) -> bool:
        """Desfaz a ultima operacao."""
        if self._undo_stack:
            self._redo_stack.append([e.to_dict() for e in self.entries])
            prev_state = self._undo_stack.pop()
            self.entries = [GenerationEntry.from_dict(e) for e in prev_state]
            self.save()
            return True
        return False

    def redo(self) -> bool:
        """Refaz a ultima operacao desfeita."""
        if self._redo_stack:
            self._undo_stack.append([e.to_dict() for e in self.entries])
            next_state = self._redo_stack.pop()
            self.entries = [GenerationEntry.from_dict(e) for e in next_state]
            self.save()
            return True
        return False

    def _save_undo_state(self) -> None:
        """Salva o estado atual para undo."""
        self._undo_stack.append([e.to_dict() for e in self.entries])
        self._redo_stack.clear()

    def stats(self) -> dict:
        """Retorna estatisticas do historico."""
        if not self.entries:
            return {"total": 0}

        languages = {}
        for e in self.entries:
            languages[e.language] = languages.get(e.language, 0) + 1

        scores = [e.score for e in self.entries if e.score > 0]
        avg_score = sum(scores) / len(scores) if scores else 0

        return {
            "total": len(self.entries),
            "favorites": len(self.get_favorites()),
            "languages": languages,
            "average_score": round(avg_score, 1),
        }
