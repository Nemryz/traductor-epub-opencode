# Proveedor simulado para pruebas

import asyncio

from traductor_epub_opencode.providers.base import TranslationProvider


class MockProvider(TranslationProvider):
    # Proveedor que devuelve traducciones predefinidas

    def __init__(self, mapping=None):
        self._mapping = mapping or {}
        self._default = "TRADUCIDO"

    @property
    def name(self):
        return "mock"

    async def translate(self, text, system_prompt):
        await asyncio.sleep(0)
        for key, value in self._mapping.items():
            if key in text:
                return value
        return self._default
