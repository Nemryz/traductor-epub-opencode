# Cache de traducciones en disco indexada por hash SHA256 y codigo de idioma

import hashlib
import json
from pathlib import Path


class TranslationCache:
    # Guarda y recupera traducciones de fragmentos en disco

    def __init__(self, cache_dir: str | Path = "translations_cache") -> None:
        self._dir = Path(cache_dir)
        self._dir.mkdir(parents=True, exist_ok=True)

    def _key_path(self, text: str, target_language: str) -> Path:
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        return self._dir / f"{digest}_{target_language}.json"

    def get(self, text: str, target_language: str) -> str | None:
        path = self._key_path(text, target_language)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                return None
            translation = data.get("translation")
            if not isinstance(translation, str):
                return None
            return translation
        except (json.JSONDecodeError, OSError):
            # Limpiar entrada corrupta
            try:
                path.unlink()
            except OSError:
                pass
            return None

    def set(self, text: str, target_language: str, translation: str) -> None:
        path = self._key_path(text, target_language)
        path.write_text(
            json.dumps({"translation": translation}, ensure_ascii=False),
            encoding="utf-8",
        )
