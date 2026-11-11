# Orquestador de traduccion de EPUB

import asyncio
from dataclasses import dataclass
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString

from ..calibre.metadata import write_metadata
from ..providers.base import TranslationProvider
from ..security.validation import detect_prompt_injection
from ..state.cache import TranslationCache
from ..state.job import ChapterState, TranslationJob
from .cleaner import clean_html, should_skip
from .packager import repack_epub
from .reader import open_epub
from .restorer import restore_html, sanitize_translated_html

BLOCK_TAGS = {"p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "td", "th", "blockquote", "figcaption"}

_TRANSLATION_SEMAPHORE = asyncio.Semaphore(3)


@dataclass
class TranslationConfig:
    target_language: str
    output_mode: str = "replace"
    quality_mode: str = "normal"
    cache_dir: str | Path = "translations_cache"
    max_file_size: int = 500 * 1024 * 1024
    read_only: bool = False
    glossary: str | None = None


async def translate_epub(
    input_path: str | Path,
    output_path: str | Path,
    provider: TranslationProvider,
    config: TranslationConfig,
    progress_callback=None,
    timeout: float = 3600.0,
) -> Path:
    # Traduce un EPUB y escribe el resultado en output_path
    input_path = Path(input_path)
    output_path = Path(output_path)
    async with _TRANSLATION_SEMAPHORE:
        return await asyncio.wait_for(
            _translate_epub_inner(input_path, output_path, provider, config, progress_callback),
            timeout=timeout,
        )


async def _translate_epub_inner(
    input_path: Path,
    output_path: Path,
    provider: TranslationProvider,
    config: TranslationConfig,
    progress_callback=None,
) -> Path:
    # Logica interna de traduccion
    from ..security.validation import check_file_size

    check_file_size(input_path.stat().st_size)

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
    if config.glossary:
        system_prompt = f"{system_prompt}\n\n{config.glossary}"

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
            injection = detect_prompt_injection(result.text)
            if injection:
                raise ValueError(
                    f"Se detecto posible prompt injection en el capitulo {idx}: {injection}"
                )

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
            restored = sanitize_translated_html(restored)

            # Validacion estricta del HTML restaurado
            from lxml import etree as lxml_et

            try:
                lxml_et.fromstring(f"<root>{restored}</root>")
            except lxml_et.XMLSyntaxError:
                raise ValueError(f"HTML restaurado invalido en capitulo {idx}")

            if config.output_mode == "bilingual_inline":
                element.clear()
                element.append(NavigableString(f"{result.text} {restored}"))
            elif config.output_mode == "bilingual_block":
                element.clear()
                element.append(NavigableString(restored))
                new_p = soup.new_tag("p")
                new_p["class"] = "translation"
                new_p.append(NavigableString(restored))
                element.insert_after(new_p)
            else:
                element.clear()
                element.append(NavigableString(restored))

        translated[chapter.zip_path] = str(soup).encode("utf-8")
        job.mark_completed(idx)

        if progress_callback:
            progress_callback(idx + 1, total)

    book.close()

    if not config.read_only:
        repack_epub(str(input_path), translated, str(output_path))
        try:
            await write_metadata(output_path, language=config.target_language)
        except Exception:
            pass

    if job.is_complete():
        job.cleanup()

    # Log de auditoria
    import logging

    logging.getLogger("traductor").info(
        f"Traduccion completada: {input_path} -> {output_path} idioma={config.target_language}"
    )

    return output_path
