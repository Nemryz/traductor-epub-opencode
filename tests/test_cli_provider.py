# Pruebas de CLI y proveedor de opencode

import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from traductor_epub_opencode.cli import build_parser, run
from traductor_epub_opencode.providers.base import TranslationProvider
from traductor_epub_opencode.providers.opencode import OpencodeProvider


def test_base_estimate_tokens():
    class Dummy(TranslationProvider):
        @property
        def name(self):
            return "dummy"

        async def translate(self, text, system_prompt):
            return text

    p = Dummy()
    assert p.estimate_tokens("hello world") > 0


@patch("traductor_epub_opencode.providers.opencode.asyncio.create_subprocess_exec")
def test_opencode_provider_success(mock_exec):
    mock_proc = AsyncMock()
    mock_proc.communicate.return_value = (b"traducido", b"")
    mock_proc.returncode = 0
    mock_exec.return_value = mock_proc
    provider = OpencodeProvider(command=["python"])
    result = asyncio.run(provider.translate("hello", "system"))
    assert result == "traducido"


@patch("traductor_epub_opencode.providers.opencode.asyncio.create_subprocess_exec")
def test_opencode_provider_failure(mock_exec):
    mock_proc = AsyncMock()
    mock_proc.communicate.return_value = (b"", b"error")
    mock_proc.returncode = 1
    mock_exec.return_value = mock_proc
    provider = OpencodeProvider(command=["python"])
    try:
        asyncio.run(provider.translate("hello", "system"))
        assert False
    except RuntimeError:
        pass


def test_cli_parser():
    parser = build_parser()
    args = parser.parse_args(["input.epub", "-l", "en", "-q", "high"])
    assert args.language == "en"
    assert args.quality == "high"


@patch("traductor_epub_opencode.cli.translate_epub", new_callable=AsyncMock)
@patch("traductor_epub_opencode.cli.OpencodeProvider")
def test_cli_run(mock_provider, mock_translate, tmp_path):
    inp = tmp_path / "test.epub"
    inp.write_text("dummy")
    mock_translate.return_value = tmp_path / "out.epub"
    (tmp_path / "out.epub").write_text("result")
    args = build_parser().parse_args([str(inp), "-o", str(tmp_path / "out.epub")])
    asyncio.run(run(args))
    assert mock_translate.called
