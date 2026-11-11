"""Orquestador de traduccion de EPUB."""

import asyncio
from pathlib import Path
from dataclasses import dataclass

from bs4 import BeautifulSoup, NavigableString

from .reader import open_epub
from .cleaner import clean_html, should_skip
from .restorer import restore_html
from .packager import repack_epub
from ..providers.base import TranslationProvider
from ..state.cache import TranslationCache
from ..state.job import TranslationJob, ChapterState
from ..security.validation import detect_prompt_injection
from ..calibre.metadata import write_metadata


BLOCK_TAGS = {"p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "td", "th", "blockquote", "figcaption"}


@dataclass
class TranslationConfig:
    target_language: str
    output_mode: str = "replace"
    quality_mode: str = "normal"
    cache_dir: str | Path = "translations_cache"


async def translate_epub(
    input_path: str | Path,
    output_path: str | Path,
    provider: TranslationProvider,
    config: TranslationConfig,
    progress_callback=None,
) -> Path:
    """Traduce un EPUB y escribe el resultado en output_path."""
    input_path = Path(input_path)
    output_path = Path(output_path)

    book = open_epub(str(input_path))
    cache = TranslationCache(config.cache_dir)
    job_dir = output_path.parent / f"job_{input_path.stem}"
    job = TranslationJob(job_dir, [])
    if not job.chapters:
        job.chapters = [ChapterState(index=i) for i in range(len(book.chapters))]
        job._save()

    translated: dict[str, bytes] = {}
    total = len(book.chapters)

    system_prompt = (
        f"Traduce el siguiente texto al idioma con codigo {config.target_language}. "
        "Preserva todos los tokens entre corchetes como [T01] o [P01] sin modificarlos. "
        "No agregues explicaciones, solo devuelve la traduccion."
    )

    for idx, chapter in enumerate(book.chapters):
        if idx not in job.pending_indices():
            continue

        job.mark_in_progress(idx)
        raw = book.read_chapter(chapter)

        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            text = raw.decode("latin-1")

        soup = BeautifulSoup(text, "lxml")
        for element in soup.find_all(BLOCK_TAGS):
            if should_skip(element):
                continue
            result = clean_html(element)
            if not result.text.strip():
                continue
            detect_prompt_injection(result.text)

            cached = cache.get(result.text, config.target_language)
            if cached is not None:
                translated_text = cached
            else:
                translated_text = await provider.translate(result.text, system_prompt)
                if config.quality_mode == "high":
                    review_prompt = (
                        "Revisa la siguiente traduccion. Si encuentras nombres propios "
                        "incorrectamente traducidos, terminos del glosario no respetados, "
                        "o frases poco naturales, devuelve la version corregida. "
                        "Si todo esta bien, devuelve la traduccion sin cambios.\n\n"
                        f"Original: {result.text}\n\nTraduccion: {translated_text}"
                    )
                    translated_text = await provider.translate(translated_text, review_prompt)
                cache.set(result.text, config.target_language, translated_text)

            restored = restore_html(translated_text, result)
            element.clear()
            element.append(NavigableString(restored))

        translated[chapter.zip_path] = str(soup).encode("utf-8")
        job.mark_completed(idx)

        if progress_callback:
            progress_callback(idx + 1, total)

    book.close()
    repack_epub(str(input_path), translated, str(output_path))

    try:
        await write_metadata(output_path, language=config.target_language)
    except Exception:
        pass

    if job.is_complete():
        job.cleanup()

    return output_path