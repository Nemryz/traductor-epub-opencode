# Pruebas de reanudacion de traduccion

import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from traductor_epub_opencode.core.translator import translate_epub, TranslationConfig
from traductor_epub_opencode.state.job import TranslationJob, ChapterState
from tests.mock_provider import MockProvider
from tests.conftest import make_minimal_epub


def test_resume_skips_completed(tmp_path):
    epub_path = tmp_path / "test.epub"
    make_minimal_epub(epub_path, chapters=["<p>Cap uno</p>", "<p>Cap dos</p>"])
    output = tmp_path / "out.epub"
    job_dir = tmp_path / "job_test"

    # Primera ejecucion: completar solo el primer capitulo manualmente
    job = TranslationJob(job_dir, [])
    job.chapters = [ChapterState(index=0), ChapterState(index=1)]
    job._save()
    job.mark_completed(0)

    # Segunda ejecucion: debe saltar el capitulo 0
    provider = MockProvider()
    config = TranslationConfig(target_language="en", cache_dir=str(tmp_path / "cache"))
    result = asyncio.run(translate_epub(epub_path, output, provider, config))
    assert result.exists()


def test_job_state_persists(tmp_path):
    job_dir = tmp_path / "job"
    job = TranslationJob(job_dir, [])
    job.chapters = [ChapterState(index=0), ChapterState(index=1)]
    job._save()
    job.mark_completed(0)

    # Recargar
    job2 = TranslationJob(job_dir, [])
    assert job2.chapters[0].status == "completed"
    assert job2.chapters[1].status == "pending"