"""
Unit tests for the chunker — pure Python, no database, no HTTP server.
This is the payoff of Clean Architecture (ADR-001): Core logic is testable
in isolation.
"""

from app.core.ingestion.chunker import chunk_text, count_tokens


def test_short_text_produces_a_single_chunk():
    text = "Employees are entitled to fifteen days of paid time off per year."
    chunks = list(chunk_text(text, chunk_size=512, chunk_overlap=50))

    assert len(chunks) == 1
    assert chunks[0]["text"] == text
    assert chunks[0]["chunk_index"] == 0


def test_long_text_is_split_into_multiple_chunks():
    paragraph = "This is a sentence about company policy. " * 200  # far exceeds 512 tokens
    chunks = list(chunk_text(paragraph, chunk_size=512, chunk_overlap=50))

    assert len(chunks) > 1
    for chunk in chunks:
        assert count_tokens(chunk["text"]) <= 512 + 60  # small tolerance for overlap prefix


def test_chunks_carry_the_page_number_through():
    text = "Some policy text on a specific page."
    chunks = list(chunk_text(text, page_number=7))

    assert chunks[0]["page_number"] == 7


def test_consecutive_chunks_overlap():
    # A long enough text that it must split into at least two chunks
    paragraph = "Alpha beta gamma delta epsilon zeta eta theta. " * 150
    chunks = list(chunk_text(paragraph, chunk_size=100, chunk_overlap=20))

    assert len(chunks) >= 2
    # The overlap means chunk[1] should start with tokens drawn from the tail of chunk[0]
    first_words_of_chunk1 = chunks[1]["text"].split()[:3]
    assert any(word in chunks[0]["text"] for word in first_words_of_chunk1)


def test_chunk_index_is_sequential():
    paragraph = "Repeat this filler sentence to force multiple chunks. " * 100
    chunks = list(chunk_text(paragraph, chunk_size=100, chunk_overlap=10))

    indices = [c["chunk_index"] for c in chunks]
    assert indices == list(range(len(chunks)))
