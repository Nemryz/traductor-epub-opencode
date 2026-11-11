# Clase base abstracta para proveedores de traduccion

import abc


class TranslationProvider(abc.ABC):
    # Interfaz comun que todo proveedor de traduccion debe implementar

    @property
    @abc.abstractmethod
    def name(self) -> str:
        # Nombre identificador del proveedor
        ...

    @abc.abstractmethod
    async def translate(self, text: str, system_prompt: str) -> str:
        # Traduce el texto dado usando el prompt de sistema proporcionado
        ...

    def estimate_tokens(self, text: str) -> int:
        # Estima la cantidad de tokens de un texto. Aproximacion simple
        # Texto latino: un token por cada cuatro caracteres
        # Texto CJK: un token por cada dos caracteres
        cjk_count = sum(
            1 for ch in text if "\u4e00" <= ch <= "\u9fff" or "\u3040" <= ch <= "\u30ff"
        )
        if cjk_count > len(text) * 0.3:
            return len(text) // 2
        return len(text) // 4
