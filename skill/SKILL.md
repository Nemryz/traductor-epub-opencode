---
name: traductor-epub-opencode
description: Traduce libros electronicos usando opencode como motor de inferencia. Acepta EPUB, MOBI, AZW3, FB2, RTF y DOCX. Preserva la estructura del libro. Use when the user wants to translate an ebook file.
---

# Traductor de EPUB con opencode

Esta skill traduce libros electronicos usando los modelos disponibles en opencode.

## Uso

Invoca la skill con la ruta del archivo a traducir y el idioma de destino.

## Comando equivalente

python -m traductor_epub_opencode.cli <archivo> -l <idioma> -m <modo> -q <calidad>

## Parametros

- archivo: ruta del libro a traducir
- idioma: codigo BCP 47 del idioma de destino
- modo: replace, bilingual_inline o bilingual_block
- calidad: normal o high

## Notas

El motor de traduccion es opencode. No se requieren claves de API externas. Calibre debe estar instalado para formatos distintos de EPUB.