# Pruebas para el limpiador de HTML.


import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from bs4 import BeautifulSoup
from traductor_epub_opencode.core.cleaner import clean_html, should_skip


def test_clean_plain_text():
    soup = BeautifulSoup("<p>Hola mundo</p>", "lxml")
    element = soup.find("p")
    result = clean_html(element)
    assert result.text == "Hola mundo"
    assert result.fragment_type == "plain"
    assert result.token_map == {}


def test_clean_inline_tag():
    soup = BeautifulSoup("<p>Texto <em>enfatizado</em> final</p>", "lxml")
    element = soup.find("p")
    result = clean_html(element)
    assert "[T01]" in result.text
    assert "[/T01]" in result.text
    assert result.fragment_type == "with_tokens"
    assert "[T01]" in result.token_map


def test_should_skip_empty():
    soup = BeautifulSoup("<p>   </p>", "lxml")
    element = soup.find("p")
    assert should_skip(element) is True


def test_should_not_skip_with_text():
    soup = BeautifulSoup("<p>Texto</p>", "lxml")
    element = soup.find("p")
    assert should_skip(element) is False