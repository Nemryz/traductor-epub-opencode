# Validaciones de entrada y archivos para el traductor de EPUB

import os
import re
import shutil
import zipfile
from pathlib import PurePosixPath

MAX_FILE_SIZE_BYTES = int(os.getenv("MAX_FILE_SIZE_BYTES", str(500 * 1024 * 1024)))
MAX_UNCOMPRESSED_BYTES = int(os.getenv("MAX_UNCOMPRESSED_BYTES", str(2 * 1024 * 1024 * 1024)))
MAX_ZIP_ENTRIES = int(os.getenv("MAX_ZIP_ENTRIES", "10000"))


def check_file_size(size_bytes: int) -> None:
    # Lanza ValueError si el archivo supera el tamano maximo permitido
    if size_bytes > MAX_FILE_SIZE_BYTES:
        raise ValueError(
            f"El archivo supera el tamano maximo permitido de {MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB."
        )


def validate_filename(filename: str) -> None:
    # Verifica que el nombre del archivo sea seguro para usar en disco
    if not filename or not filename.strip():
        raise ValueError("El nombre del archivo no puede estar vacio.")
    if len(filename) > 200:
        raise ValueError("El nombre del archivo supera los 200 caracteres permitidos.")
    if any(c in filename for c in ("/", "\\", "..", "\0", "\r", "\n")):
        raise ValueError("El nombre del archivo contiene caracteres no permitidos.")


def validate_zip_entry_path(zip_path: str) -> None:
    # Verifica que la ruta de un entry dentro del ZIP no escape del directorio raiz
    # Normaliza barras invertidas a barras diagonales antes de validar
    normalized = zip_path.replace("\\", "/")
    clean = str(PurePosixPath(normalized))
    if clean.startswith("..") or clean.startswith("/") or ".." in PurePosixPath(normalized).parts:
        raise ValueError(f"Ruta de archivo ZIP sospechosa: {zip_path!r}")


def validate_zip_integrity(zf: zipfile.ZipFile) -> None:
    # Verifica el tamano total descomprimido y el numero de entradas del ZIP
    entries = zf.infolist()
    if len(entries) > MAX_ZIP_ENTRIES:
        raise ValueError(f"El ZIP contiene demasiadas entradas: {len(entries)}")
    total_size = sum(info.file_size for info in entries)
    if total_size > MAX_UNCOMPRESSED_BYTES:
        raise ValueError(f"El tamaño descomprimido del ZIP supera el limite: {total_size} bytes")


def detect_drm(zf: zipfile.ZipFile) -> bool:
    # Detecta si el EPUB tiene DRM verificando la presencia de META-INF/container.xml
    names = set(zf.namelist())
    if "META-INF/container.xml" not in names:
        return True
    # Verificar archivos de cifrado
    if "META-INF/encryption.xml" in names:
        return True
    return False


_INJECTION_PATTERNS: list[re.Pattern] = [
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"forget\s+your\s+(previous\s+)?(instructions|training)", re.IGNORECASE),
    re.compile(r"(disregard|bypass|override)\s+(all\s+)?instructions", re.IGNORECASE),
    re.compile(r"new\s+system\s+prompt", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(a|an)\s+\w+", re.IGNORECASE),
]


def detect_prompt_injection(text: str) -> list[str]:
    # Busca patrones de prompt injection en el texto. Devuelve la lista encontrada
    found: list[str] = []
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(text):
            found.append(pattern.pattern)
    return found


def check_executable(name: str) -> None:
    # Verifica que un ejecutable exista en el PATH del sistema
    if shutil.which(name) is None:
        raise RuntimeError(f"El ejecutable '{name}' no se encuentra en el PATH del sistema.")
