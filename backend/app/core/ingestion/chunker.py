"""
Text chunker — recursive splitting with overlap (ADR-004).

512 tokens per chunk, 50-token overlap, split preference order:
paragraph break -> sentence break -> word break -> character.
Both values are configurable via app.config.settings so they can be
tuned without a code change (validated empirically in Phase 05/07).
"""

from typing import Generator

import tiktoken

_ENCODING = tiktoken.get_encoding("cl100k_base")  # same tokenizer family as Claude/GPT


def count_tokens(text: str) -> int:
    return len(_ENCODING.encode(text))


def chunk_text(
    text: str,
    chunk_size: int = 512,
    chunk_overlap: int = 50,
    page_number: int | None = None,
) -> Generator[dict, None, None]:
    """
    Yields {"text", "chunk_index", "page_number", "char_start", "char_end", "token_count"}.
    """
    raw_chunks = _recursive_split(text, ["\n\n", "\n", ". ", " ", ""], chunk_size)
    merged = _apply_overlap(raw_chunks, chunk_overlap)

    char_pos = 0
    for idx, piece in enumerate(merged):
        char_start = text.find(piece.strip()[:50], char_pos) if piece.strip() else -1
        char_end = char_start + len(piece) if char_start != -1 else None
        if char_start != -1:
            char_pos = char_start

        yield {
            "text": piece.strip(),
            "chunk_index": idx,
            "page_number": page_number,
            "char_start": char_start if char_start != -1 else None,
            "char_end": char_end,
            "token_count": count_tokens(piece),
        }


def _recursive_split(text: str, separators: list[str], chunk_size: int) -> list[str]:
    """Try the first separator that keeps pieces under chunk_size; recurse with the next one otherwise."""
    if not separators:
        return [text]

    separator = separators[0]
    pieces = text.split(separator) if separator else list(text)
    result: list[str] = []
    current = ""

    for piece in pieces:
        candidate = current + (separator if current else "") + piece
        if count_tokens(candidate) <= chunk_size:
            current = candidate
            continue

        if current:
            result.append(current)

        if count_tokens(piece) > chunk_size:
            result.extend(_recursive_split(piece, separators[1:], chunk_size))
            current = ""
        else:
            current = piece

    if current:
        result.append(current)

    return result


def _apply_overlap(chunks: list[str], overlap: int) -> list[str]:
    """Prepend the last `overlap` tokens of the previous chunk onto each chunk after the first."""
    if not chunks:
        return []

    result = [chunks[0]]
    for i in range(1, len(chunks)):
        prev_tokens = _ENCODING.encode(chunks[i - 1])
        tail = prev_tokens[-overlap:] if len(prev_tokens) > overlap else prev_tokens
        result.append(_ENCODING.decode(tail) + " " + chunks[i])

    return result
