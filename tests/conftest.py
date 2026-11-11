# Configuracion compartida para las pruebas

import zipfile

import pytest


def make_minimal_epub(path, chapters=None):
    # Crea un EPUB minimo para pruebas
    if chapters is None:
        chapters = ["<p>Hola mundo</p>"]
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("mimetype", "application/epub+zip")
        zf.writestr(
            "META-INF/container.xml",
            '<?xml version="1.0"?>'
            '<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">'
            '<rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles>'
            "</container>",
        )
        manifest_items = ""
        spine_items = ""
        for i, ch in enumerate(chapters):
            href = f"chapter{i + 1}.xhtml"
            manifest_items += (
                f'<item id="ch{i + 1}" href="{href}" media-type="application/xhtml+xml"/>'
            )
            spine_items += f'<itemref idref="ch{i + 1}"/>'
            zf.writestr(
                f"OEBPS/{href}",
                f'<?xml version="1.0" encoding="utf-8"?><html xmlns="http://www.w3.org/1999/xhtml"><body>{ch}</body></html>',
            )
        opf = (
            '<?xml version="1.0" encoding="utf-8"?>'
            '<package xmlns="http://www.idpf.org/2007/opf" version="3.0">'
            '<metadata><dc:title xmlns:dc="http://purl.org/dc/elements/1.1/">Test</dc:title>'
            '<dc:language xmlns:dc="http://purl.org/dc/elements/1.1/">es</dc:language></metadata>'
            f"<manifest>{manifest_items}</manifest>"
            f"<spine>{spine_items}</spine>"
            "</package>"
        )
        zf.writestr("OEBPS/content.opf", opf)


@pytest.fixture
def minimal_epub(tmp_path):
    path = tmp_path / "test.epub"
    make_minimal_epub(path)
    return path


@pytest.fixture
def multi_chapter_epub(tmp_path):
    path = tmp_path / "multi.epub"
    make_minimal_epub(path, chapters=["<p>Capitulo uno</p>", "<p>Capitulo dos</p>"])
    return path
