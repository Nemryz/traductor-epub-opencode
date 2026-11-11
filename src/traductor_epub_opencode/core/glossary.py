# Carga y formateo del glosario de terminos para el system prompt

from pathlib import Path


def load_glossary(path: str | Path) -> str:
    # Lee el archivo de glosario y devuelve el bloque de texto para el prompt
    # Las lineas con origen = destino fijan la traduccion y las lineas sueltas marcan terminos que no deben traducirse
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    mappings = []
    keep_terms = []
    for line in lines:
        entry = line.strip()
        if not entry or entry.startswith("#"):
            continue
        if "=" in entry:
            source, _, target = entry.partition("=")
            source = source.strip()
            target = target.strip()
            if not source or not target:
                raise ValueError(f"Entrada de glosario invalida: {entry}")
            mappings.append(f"{source} -> {target}")
        else:
            keep_terms.append(entry)
    if not mappings and not keep_terms:
        return ""
    parts = []
    if mappings:
        parts.append("Terminos con traduccion fija, usa siempre la traduccion indicada.")
        parts.extend(mappings)
    if keep_terms:
        parts.append("Terminos que no deben traducirse, mantenlos tal cual.")
        parts.extend(keep_terms)
    return "\n".join(parts)
