# Wrapper de subprocess para ebook-convert de Calibre

import asyncio
from pathlib import Path

SUPPORTED_INPUTS = {".epub", ".mobi", ".azw3", ".fb2", ".rtf", ".docx"}


async def convert_to_epub(input_path: str | Path, output_path: str | Path, timeout: float = 300.0) -> Path:
    # Convierte un archivo a EPUB usando ebook-convert. Devuelve la ruta de salida
    from ..security.validation import check_executable
    check_executable("ebook-convert")
    input_path = Path(input_path)
    output_path = Path(output_path)
    if input_path.suffix.lower() not in SUPPORTED_INPUTS:
        raise ValueError(f"Formato no soportado: {input_path.suffix}")
    proc = await asyncio.create_subprocess_exec(
        "ebook-convert",
        str(input_path),
        str(output_path),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        raise RuntimeError("Timeout en la conversion con Calibre.")
    if proc.returncode != 0:
        err = stderr.decode("utf-8", errors="replace")
        raise RuntimeError(f"ebook-convert fallo: {err}")
    return output_path