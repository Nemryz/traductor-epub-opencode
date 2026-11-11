# Pruebas de integracion del orquestador de traduccion

import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from traductor_epub_opencode.core.translator import translate_epub, TranslationConfig
from tests.mock_provider import MockProvider


def test_translate_basic(minimal_epub, tmp_path):
    output = tmp_path / "out.epub"
    provider = MockProvider()
    config = TranslationConfig(target_language="en")
    result = asyncio.run(translate_epub(minimal_epub, output, provider, config))
    assert result.exists()
    assert result == output


def test_translate_read_only(minimal_epub, tmp_path):
    output = tmp_path / "out.epub"
    provider = MockProvider()
    config = TranslationConfig(target_language="en", read_only=True)
    result = asyncio.run(translate_epub(minimal_epub, output, provider, config))
    assert result == output
    assert not output.exists()


def test_translate_high_quality(minimal_epub, tmp_path):
    output = tmp_path / "out.epub"
    provider = MockProvider()
    config = TranslationConfig(target_language="en", quality_mode="high")
    result = asyncio.run(translate_epub(minimal_epub, output, provider, config))
    assert result.exists()


def test_translate_bilingual_mode(minimal_epub, tmp_path):
    output = tmp_path / "out.epub"
    provider = MockProvider()
    config = TranslationConfig(target_language="en", output_mode="bilingual_inline")
    result = asyncio.run(translate_epub(minimal_epub, output, provider, config))
    assert result.exists()