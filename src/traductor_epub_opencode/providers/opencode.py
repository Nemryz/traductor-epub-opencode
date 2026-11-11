"""Adaptador de opencode como proveedor de traduccion."""

import asyncio
import os

from .base import TranslationProvider


class OpencodeProvider(TranslationProvider):
    """Proveedor que invoca opencode como proceso hijo para traducir texto."""

    def __init__(
        self,
        command: list[str] | None = None,
        timeout: float = 120.0,
    ) -> None:
        # El comando por defecto invoca opencode en modo no interactivo.
        # Se puede sobrescribir con la variable de entorno OPENCODE_COMMAND.
        if command is None:
            env_cmd = os.getenv("OPENCODE_COMMAND", "")
            if env_cmd:
                command = env_cmd.split()
            else:
                command = ["opencode", "run"]
        self._command = command
        self._timeout = timeout

    @property
    def name(self) -> str:
        return "opencode"

    async def translate(self, text: str, system_prompt: str) -> str:
        full_prompt = f"{system_prompt}\n\n---\n\n{text}"
        proc = await asyncio.create_subprocess_exec(
            *self._command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(full_prompt.encode("utf-8")),
                timeout=self._timeout,
            )
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            raise RuntimeError("Timeout al invocar opencode para traduccion.")
        if proc.returncode != 0:
            err = stderr.decode("utf-8", errors="replace")
            raise RuntimeError(f"opencode fallo con codigo {proc.returncode}: {err}")
        return stdout.decode("utf-8", errors="replace").strip()