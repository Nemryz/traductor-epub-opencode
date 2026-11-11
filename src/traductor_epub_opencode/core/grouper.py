# Agrupacion de fragmentos por tokens estimados


def estimate_tokens(text: str) -> int:
    # Estima la cantidad de tokens de un texto
    # Texto latino: un token por cada cuatro caracteres
    # Texto CJK: un token por cada dos caracteres
    cjk_count = sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff" or "\u3040" <= ch <= "\u30ff")
    if cjk_count > len(text) * 0.3:
        return len(text) // 2
    return len(text) // 4


def group_fragments(fragments: list[str], max_tokens: int) -> list[list[str]]:
    # Agrupa fragmentos en listas cuya suma estimada de tokens no supera max_tokens
    # Un fragmento individual que exceda el limite forma un grupo propio
    if max_tokens <= 0:
        return [[fragment] for fragment in fragments]
    groups = []
    current = []
    current_tokens = 0
    for fragment in fragments:
        fragment_tokens = estimate_tokens(fragment)
        if current and current_tokens + fragment_tokens > max_tokens:
            groups.append(current)
            current = []
            current_tokens = 0
        current.append(fragment)
        current_tokens += fragment_tokens
        if fragment_tokens > max_tokens:
            groups.append(current)
            current = []
            current_tokens = 0
    if current:
        groups.append(current)
    return groups
