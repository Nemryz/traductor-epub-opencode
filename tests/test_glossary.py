# Pruebas del glosario y su inyeccion en el prompt

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tests.conftest import make_minimal_epub
from traductor_epub_opencode.core.glossary import load_glossary
from traductor_epub_opencode.core.translator import TranslationConfig, translate_epub
from traductor_epub_opencode.providers.base import TranslationProvider


class RecordingProvider(TranslationProvider):
    # Proveedor que captura los prompts recibidos y devuelve texto fijo

    def __init__(self):
        self.prompts = []
        self.texts = []

    @property
    def name(self):
        return "recording"

    async def translate(self, text, system_prompt):
        self.prompts.append(system_prompt)
        self.texts.append(text)
        return "TRADUCIDO"


def test_load_glossary_mixed(tmp_path):
    # Lineas con igual fijan traduccion y lineas sueltas marcan terminos intactos
    glossary_file = tmp_path / "glosario.txt"
    glossary_file.write_text(
        "# Comentario que se ignora\nMiddle Earth = Tierra Media\n\nFrodo\n",
        encoding="utf-8",
    )
    result = load_glossary(glossary_file)
    assert "Middle Earth -> Tierra Media" in result
    assert "Terminos con traduccion fija" in result
    assert "Frodo" in result
    assert "no deben traducirse" in result


def test_load_glossary_invalid_entry(tmp_path):
    # Una linea con igual pero sin lado completo debe fallar
    glossary_file = tmp_path / "glosario.txt"
    glossary_file.write_text(" = Tierra Media\n", encoding="utf-8")
    try:
        load_glossary(glossary_file)
        assert False
    except ValueError:
        pass


def test_load_glossary_empty_file(tmp_path):
    # Un glosario vacio produce un bloque vacio
    glossary_file = tmp_path / "glosario.txt"
    glossary_file.write_text("# Solo comentarios\n\n", encoding="utf-8")
    assert load_glossary(glossary_file) == ""


def test_glossary_injected_in_prompt(minimal_epub, tmp_path):
    # El proveedor debe recibir el glosario dentro del system prompt
    output = tmp_path / "out.epub"
    provider = RecordingProvider()
    glossary_text = load_glossary_with_content("Middle Earth = Tierra Media")
    config = TranslationConfig(
        target_language="es",
        cache_dir=str(tmp_path / "cache"),
        glossary=glossary_text,
    )
    asyncio.run(translate_epub(minimal_epub, output, provider, config))
    assert provider.prompts
    assert all("Middle Earth -> Tierra Media" in prompt for prompt in provider.prompts)


def test_no_glossary_keeps_prompt_clean(minimal_epub, tmp_path):
    # Sin glosario el prompt no debe contener la seccion de terminos
    output = tmp_path / "out.epub"
    provider = RecordingProvider()
    config = TranslationConfig(target_language="es", cache_dir=str(tmp_path / "cache"))
    asyncio.run(translate_epub(minimal_epub, output, provider, config))
    assert provider.prompts
    assert all("Terminos con traduccion fija" not in prompt for prompt in provider.prompts)


def load_glossary_with_content(content):
    # Utilidad para obtener el bloque de glosario desde texto en memoria
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        glossary_file = Path(tmp) / "glosario.txt"
        glossary_file.write_text(content, encoding="utf-8")
        return load_glossary(glossary_file)


def test_cli_glossary_missing_file():
    # La CLI debe rechazar un glosario inexistente
    from traductor_epub_opencode.cli import build_parser, run

    args = build_parser().parse_args(["input.epub", "--glossary", "no_existe.txt"])
    try:
        asyncio.run(run(args))
        assert False
    except FileNotFoundError:
        pass


def test_minimal_epub_still_translates(minimal_epub, tmp_path):
    # Verificacion de que el EPUB de prueba se traduce con el flujo actual
    output = tmp_path / "out.epub"
    make_minimal_epub(output.with_name("ref.epub"))
    provider = RecordingProvider()
    config = TranslationConfig(target_language="en", cache_dir=str(tmp_path / "cache"))
    result = asyncio.run(translate_epub(minimal_epub, output, provider, config))
    assert result.exists()
