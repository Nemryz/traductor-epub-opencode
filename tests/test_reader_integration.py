# Pruebas de integracion del lector de EPUB

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from traductor_epub_opencode.core.reader import open_epub


def test_open_minimal_epub(minimal_epub):
    book = open_epub(str(minimal_epub))
    assert len(book.chapters) == 1
    assert book.meta.title == "Test"
    raw = book.read_chapter(book.chapters[0])
    assert b"Hola mundo" in raw
    book.close()


def test_open_multi_chapter(multi_chapter_epub):
    book = open_epub(str(multi_chapter_epub))
    assert len(book.chapters) == 2
    book.close()


def test_read_chapter_returns_bytes(minimal_epub):
    book = open_epub(str(minimal_epub))
    raw = book.read_chapter(book.chapters[0])
    assert isinstance(raw, bytes)
    book.close()
