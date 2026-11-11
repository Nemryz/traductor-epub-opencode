# Interfaz de linea de comandos para traductor-epub-opencode

import argparse
import asyncio
import logging
import sys
from pathlib import Path

from .core.glossary import load_glossary
from .core.translator import TranslationConfig, translate_epub
from .providers.opencode import OpencodeProvider


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Traduce libros electronicos usando opencode como motor."
    )
    parser.add_argument("input", help="Ruta del archivo de entrada.")
    parser.add_argument("-o", "--output", help="Ruta del archivo de salida.")
    parser.add_argument("-l", "--language", default="es", help="Codigo de idioma de destino.")
    parser.add_argument(
        "-m",
        "--mode",
        default="replace",
        choices=["replace", "bilingual_inline", "bilingual_block"],
    )
    parser.add_argument("-q", "--quality", default="normal", choices=["normal", "high"])
    parser.add_argument("--cache-dir", default="translations_cache")
    parser.add_argument(
        "--glossary",
        help="Ruta del archivo de glosario con terminos de traduccion fija.",
    )
    parser.add_argument(
        "--group-tokens",
        type=int,
        default=0,
        help="Umbral de tokens para agrupar fragmentos. Cero desactiva la agrupacion.",
    )
    parser.add_argument(
        "--read-only",
        action="store_true",
        help="No escribe el EPUB de salida ni actualiza metadatos.",
    )
    parser.add_argument(
        "--audit-log",
        default="audit.log",
        help="Ruta del archivo de log de auditoria.",
    )
    return parser


def _setup_logging(audit_log: str) -> None:
    # Configura el logger de auditoria para escribir en archivo y consola
    logger = logging.getLogger("traductor")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        file_handler = logging.FileHandler(audit_log, encoding="utf-8")
        file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(file_handler)


async def run(args) -> None:
    input_path = Path(args.input)
    if not input_path.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {input_path}")
    output_path = (
        Path(args.output) if args.output else input_path.with_stem(input_path.stem + "_translated")
    )
    provider = OpencodeProvider()
    glossary_text = None
    if args.glossary:
        glossary_path = Path(args.glossary)
        if not glossary_path.exists():
            raise FileNotFoundError(f"Archivo de glosario no encontrado: {glossary_path}")
        glossary_text = load_glossary(glossary_path)
    config = TranslationConfig(
        target_language=args.language,
        output_mode=args.mode,
        quality_mode=args.quality,
        cache_dir=args.cache_dir,
        glossary=glossary_text,
        max_group_tokens=args.group_tokens,
        read_only=args.read_only,
    )
    result = await translate_epub(input_path, output_path, provider, config)
    print(f"Traduccion completada: {result}")


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        _setup_logging(args.audit_log)
        asyncio.run(run(args))
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"Error de validacion: {exc}", file=sys.stderr)
        return 2
    except RuntimeError as exc:
        print(f"Error del proveedor: {exc}", file=sys.stderr)
        return 3
    except Exception as exc:  # noqa: BLE001
        print(f"Error inesperado: {exc}", file=sys.stderr)
        return 4
    return 0


if __name__ == "__main__":
    sys.exit(main())
