# Pruebas de Calibre con subprocess simulado

import sys
import asyncio
from pathlib import Path
from unittest.mock import patch, AsyncMock

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from traductor_epub_opencode.calibre.converter import convert_to_epub, SUPPORTED_INPUTS
from traductor_epub_opencode.calibre.metadata import read_metadata, write_metadata


def test_supported_inputs():
    assert ".epub" in SUPPORTED_INPUTS
    assert ".mobi" in SUPPORTED_INPUTS


def test_convert_unsupported_format(tmp_path):
    try:
        asyncio.run(convert_to_epub(tmp_path / "test.xyz", tmp_path / "out.epub"))
        assert False
    except ValueError:
        pass


@patch("traductor_epub_opencode.calibre.converter.asyncio.create_subprocess_exec")
def test_convert_success(mock_exec, tmp_path):
    mock_proc = AsyncMock()
    mock_proc.communicate.return_value = (b"", b"")
    mock_proc.returncode = 0
    mock_exec.return_value = mock_proc

    inp = tmp_path / "test.epub"
    inp.write_text("dummy")
    out = tmp_path / "out.epub"
    result = asyncio.run(convert_to_epub(inp, out))
    assert result == out


@patch("traductor_epub_opencode.calibre.metadata.asyncio.create_subprocess_exec")
def test_read_metadata(mock_exec):
    mock_proc = AsyncMock()
    mock_proc.communicate.return_value = (b"Title   : Test Book\nAuthor  : Test Author", b"")
    mock_exec.return_value = mock_proc
    result = asyncio.run(read_metadata("test.epub"))
    assert "Title" in result


@patch("traductor_epub_opencode.calibre.metadata.asyncio.create_subprocess_exec")
def test_write_metadata(mock_exec, tmp_path):
    mock_proc = AsyncMock()
    mock_proc.communicate.return_value = (b"", b"")
    mock_exec.return_value = mock_proc
    asyncio.run(write_metadata(tmp_path / "test.epub", language="es"))