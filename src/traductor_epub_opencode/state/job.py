"""Estado de trabajo por capitulo para reanudacion de traducciones."""

import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Literal

ChapterStatus = Literal["pending", "in_progress", "completed"]


@dataclass
class ChapterState:
    """Estado de un capitulo dentro del trabajo de traduccion."""

    index: int
    status: ChapterStatus = "pending"


@dataclass
class TranslationJob:
    """Mantiene el estado del proceso a nivel de capitulo."""

    job_dir: Path
    chapters: list[ChapterState] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.job_dir.mkdir(parents=True, exist_ok=True)
        self._state_path = self.job_dir / "job_state.json"
        if self._state_path.exists():
            self._load()
        else:
            self._save()

    def _load(self) -> None:
        data = json.loads(self._state_path.read_text(encoding="utf-8"))
        self.chapters = [
            ChapterState(index=ch["index"], status=ch["status"])
            for ch in data.get("chapters", [])
        ]

    def _save(self) -> None:
        data = {
            "chapters": [
                {"index": ch.index, "status": ch.status}
                for ch in self.chapters
            ]
        }
        self._state_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def mark_in_progress(self, index: int) -> None:
        for ch in self.chapters:
            if ch.index == index:
                ch.status = "in_progress"
        self._save()

    def mark_completed(self, index: int) -> None:
        for ch in self.chapters:
            if ch.index == index:
                ch.status = "completed"
        self._save()

    def pending_indices(self) -> list[int]:
        return [ch.index for ch in self.chapters if ch.status != "completed"]

    def is_complete(self) -> bool:
        return all(ch.status == "completed" for ch in self.chapters)

    def cleanup(self) -> None:
        if self._state_path.exists():
            self._state_path.unlink()