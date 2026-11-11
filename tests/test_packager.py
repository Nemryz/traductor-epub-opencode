# Pruebas del empaquetador de EPUB

import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from traductor_epub_opencode.core.packager import repack_epub


def test_repack_preserves_structure(minimal_epub, tmp_path):
    # minimal_epub viene de conftest
    output = tmp_path / "out.epub"
    repack_epub(str(minimal_epub), {}, str(output))
    assert output.exists()
    with zipfile.ZipFile(output, "r") as zf:
        assert "META-INF/container.xml" in zf.namelist()


def test_repack_replaces_chapter(minimal_epub, tmp_path):
    book_zip = zipfile.ZipFile(minimal_epub, "r")
    names = book_zip.namelist()
    book_zip.close()
    # Encontrar el zip_path del capitulo
    import traductor_epub_opencode.core.reader as r
    book = r.open_epub(str(minimal_epub))
    chapter = book.chapters[0]
    book.close()
    translated = {chapter.zip_path: b"<html><body>Traducido</body></html>"}
    output = tmp_path / "out.epub"
    repack_epub(str(minimal_epub), translated, str(output))
    with zipfile.ZipFile(output, "r") as zf:
        assert b"Traducido" in zf.read(chapter.zip_path)