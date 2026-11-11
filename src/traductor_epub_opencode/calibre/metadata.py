"""Wrapper de subprocess para ebook-meta de Calibre."""

import asyncio
from pathlib import Path


async def read_metadata(epub_path: str | Path) -> dict[str, str]:
    """Lee metadatos del EPUB usando ebook-meta. Devuelve un diccionario."""
    proc = await asyncio.create_subprocess_exec(
        "ebook-meta",
        str(epub_path),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await proc.communicate()
    result: dict[str, str] = {}
    for line in stdout.decode("utf-8", errors="replace").splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            result[key.strip()] = value.strip()
    return result


async def write_metadata(
    epub_path: str | Path,
    title: str | None = None,
    language: str | None = None,
    timeout: float = 60.0,
) -> None:
    """Actualiza metadatos del EPUB usando ebook-meta."""
    args = ["ebook-meta", str(epub_path)]
    if title:
        args += ["--title", title]
    if language:
        args += ["--language", language]
    proc = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        raise RuntimeError("Timeout al escribir metadatos con ebook-meta.")