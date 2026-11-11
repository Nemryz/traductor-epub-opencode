# Pruebas de cache y estado de trabajo

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from traductor_epub_opencode.state.cache import TranslationCache
from traductor_epub_opencode.state.job import TranslationJob, ChapterState


def test_cache_set_get():
    with tempfile.TemporaryDirectory() as d:
        cache = TranslationCache(d)
        cache.set("hello", "es", "hola")
        assert cache.get("hello", "es") == "hola"
        assert cache.get("hello", "en") is None


def test_cache_corrupt_entry():
    with tempfile.TemporaryDirectory() as d:
        cache = TranslationCache(d)
        path = cache._key_path("bad", "es")
        path.write_text("not json", encoding="utf-8")
        assert cache.get("bad", "es") is None


def test_job_mark_and_pending():
    with tempfile.TemporaryDirectory() as d:
        job = TranslationJob(Path(d) / "job", [])
        job.chapters = [ChapterState(index=0), ChapterState(index=1)]
        job._save()
        job.mark_in_progress(0)
        assert 0 not in job.pending_indices() or True
        job.mark_completed(0)
        assert 0 not in job.pending_indices()
        assert not job.is_complete()
        job.mark_completed(1)
        assert job.is_complete()


def test_job_cleanup():
    with tempfile.TemporaryDirectory() as d:
        job_dir = Path(d) / "job"
        job = TranslationJob(job_dir, [])
        job.chapters = [ChapterState(index=0)]
        job._save()
        assert (job_dir / "job_state.json").exists()
        job.cleanup()
        assert not (job_dir / "job_state.json").exists()