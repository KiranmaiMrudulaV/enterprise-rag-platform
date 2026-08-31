from app.core.generation.answer_parser import AnswerParser


def test_extracts_single_citation():
    parser = AnswerParser()
    text = "Employees get 15 days of PTO annually [1]."

    _, used = parser.parse(text, num_context_chunks=2)

    assert used == [0]


def test_extracts_multiple_citations_in_order():
    parser = AnswerParser()
    text = "PTO is 15 days [1], accruing at 1.25 days per month [2]."

    _, used = parser.parse(text, num_context_chunks=3)

    assert used == [0, 1]


def test_deduplicates_repeated_citations():
    parser = AnswerParser()
    text = "Per [1], employees get PTO. This is confirmed again in [1]."

    _, used = parser.parse(text, num_context_chunks=2)

    assert used == [0]


def test_drops_citation_numbers_outside_valid_range():
    """A hallucinated citation like [9] when only 2 chunks were sent must not crash or leak through."""
    parser = AnswerParser()
    text = "This claim is backed by [9], which does not exist."

    _, used = parser.parse(text, num_context_chunks=2)

    assert used == []


def test_no_citations_returns_empty_list():
    parser = AnswerParser()
    text = "I don't have information about that in the available documents."

    _, used = parser.parse(text, num_context_chunks=5)

    assert used == []
