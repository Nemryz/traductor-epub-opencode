# Pruebas de agrupacion de fragmentos por tokens

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from traductor_epub_opencode.core.grouper import estimate_tokens, group_fragments


def test_estimate_tokens_latin():
    # Texto latino: un token por cada cuatro caracteres
    assert estimate_tokens("abcd") == 1
    assert estimate_tokens("") == 0


def test_estimate_tokens_cjk():
    # Texto CJK: un token por cada dos caracteres
    text = "你好世界" * 5
    assert estimate_tokens(text) == len(text) // 2


def test_group_fragments_disabled():
    # Con umbral cero cada fragmento forma su propio grupo
    fragments = ["uno", "dos", "tres"]
    assert group_fragments(fragments, 0) == [["uno"], ["dos"], ["tres"]]


def test_group_fragments_accumulates():
    # Los fragmentos pequenos se acumulan hasta el umbral
    fragments = ["aaaa", "bbbb", "cccc"]
    result = group_fragments(fragments, 100)
    assert result == [["aaaa", "bbbb", "cccc"]]


def test_group_fragments_splits_when_full():
    # Cuando el acumulado supera el umbral se abre un nuevo grupo
    fragments = ["a" * 40, "b" * 40, "c" * 40]
    result = group_fragments(fragments, 12)
    assert len(result) >= 2


def test_group_fragments_empty_input():
    # Una lista vacia produce una lista vacia
    assert group_fragments([], 10) == []


def test_group_fragments_oversized_single():
    # Un fragmento que excede el limite forma un grupo propio
    fragments = ["a" * 1000]
    result = group_fragments(fragments, 5)
    assert len(result) == 1
    assert result[0] == ["a" * 1000]


def test_group_fragments_preserves_order():
    # El orden de los fragmentos se conserva
    fragments = ["primero", "segundo", "tercero"]
    result = group_fragments(fragments, 1)
    flattened = [f for group in result for f in group]
    assert flattened == fragments
