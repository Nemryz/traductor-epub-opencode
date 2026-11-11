# Pruebas para el restaurador de HTML.


import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from bs4 import BeautifulSoup
from traductor_epub_opencode.core.cleaner import clean_html
from traductor_epub_opencode.core.restorer import restore_html, count_token_mismatches


def test_restore_preserves_tokens():
    soup = BeautifulSoup("<p>Texto <em>enfatizado</em> final</p>", "lxml")
    element = soup.find("p")
    result = clean_html(element)
    translated = result.text.replace("Texto", "Text").replace("final", "end")
    restored = restore_html(translated, result)
    assert "<em>" in restored
    assert "</em>" in restored


def test_count_mismatches_zero():
    soup = BeautifulSoup("<p>Texto <em>enfatizado</em> final</p>", "lxml")
    element = soup.find("p")
    result = clean_html(element)
    assert count_token_mismatches(result.text, result) == 0