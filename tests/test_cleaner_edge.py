# Pruebas adicionales del limpiador y restaurador de HTML

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from bs4 import BeautifulSoup

from traductor_epub_opencode.core.cleaner import clean_html, should_skip
from traductor_epub_opencode.core.restorer import sanitize_translated_html, validate_translation


def test_clean_nested_tags():
    soup = BeautifulSoup("<p>Texto <strong>negrita <em>enfatizado</em></strong> final</p>", "lxml")
    element = soup.find("p")
    result = clean_html(element)
    assert result.fragment_type == "with_tokens"
    assert "[T01]" in result.text
    assert "[T02]" in result.text


def test_clean_non_translatable():
    soup = BeautifulSoup("<p>Texto <img src='a.png'/> final</p>", "lxml")
    element = soup.find("p")
    result = clean_html(element)
    assert "[P01]" in result.text
    assert result.fragment_type == "with_tokens"


def test_clean_comment():
    soup = BeautifulSoup("<p>Texto <!-- comentario --> final</p>", "lxml")
    element = soup.find("p")
    result = clean_html(element)
    assert "[P01]" in result.text


def test_should_skip_image_only():
    soup = BeautifulSoup("<p><img src='a.png'/></p>", "lxml")
    element = soup.find("p")
    assert should_skip(element) is True


def test_sanitize_removes_script():
    html = "<p>Hola</p><script>alert(1)</script>"
    result = sanitize_translated_html(html)
    assert "script" not in result
    assert "Hola" in result


def test_sanitize_removes_event_handler():
    html = '<p onclick="alert(1)">Hola</p>'
    result = sanitize_translated_html(html)
    assert "onclick" not in result


def test_validate_translation_length():
    result = validate_translation("Hello world this is a long text", "Hi")
    assert result.is_valid is False


def test_validate_translation_ok():
    result = validate_translation("Hello world.", "Hola mundo.")
    assert result.is_valid is True
