"""Validaciones de entrada y archivos para el traductor de EPUB."""

import re
from pathlib import PurePosixPath

MAX_FILE_SIZE_BYTES = 500 * 1024 * 1024


def check_file_size(size_bytes: int) -> None:
    """Lanza ValueError si el archivo supera el tamano maximo permitido."""
    if size_bytes > MAX_FILE_SIZE_BYTES:
        raise ValueError(
            f"El archivo supera el tamano maximo permitido de {MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB."
        )


def validate_filename(filename: str) -> None:
    """Verifica que el nombre del archivo sea seguro para usar en disco."""
    if not filename or not filename.strip():
        raise ValueError("El nombre del archivo no puede estar vacio.")
    if len(filename) > 200:
        raise ValueError("El nombre del archivo supera los 200 caracteres permitidos.")
    if any(c in filename for c in ("/", "\\", "..", "\0", "\r", "\n")):
        raise ValueError("El nombre del archivo contiene caracteres no permitidos.")


def validate_zip_entry_path(zip_path: str) -> None:
    """Verifica que la ruta de un entry dentro del ZIP no escape del directorio raiz."""
    clean = str(PurePosixPath(zip_path))
    if clean.startswith("..") or clean.startswith("/"):
        raise ValueError(f"Ruta de archivo ZIP sospechosa: {zip_path!r}")


_INJECTION_PATTERNS: list[re.Pattern] = [
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"forget\s+your\s+(previous\s+)?(instructions|training)", re.IGNORECASE),
    re.compile(r"(disregard|bypass|override)\s+(all\s+)?instructions", re.IGNORECASE),
]


def detect_prompt_injection(text: str) -> list[str]:
    """Busca patrones de prompt injection en el texto. Devuelve la lista encontrada."""
    found: list[str] = []
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(text):
            found.append(pattern.pattern)
    return found