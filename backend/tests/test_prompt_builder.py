from app.core.generation.prompt_builder import PromptBuilder


def test_numbers_chunks_starting_at_one():
    builder = PromptBuilder()
    chunks = [
        {"document_name": "HR_Policy.pdf", "page_number": 3, "text": "Employees get 15 days PTO."},
        {"document_name": "Benefits.pdf", "page_number": 7, "text": "PTO accrues monthly."},
    ]

    prompt = builder.build("What is the PTO policy?", chunks)

    assert "[1] Source:" in prompt
    assert "[2] Source:" in prompt
    assert "HR_Policy.pdf" in prompt
    assert "Page 3" in prompt


def test_instructs_the_model_to_cite_and_not_guess():
    builder = PromptBuilder()
    prompt = builder.build("Any question", [])

    assert "cite" in prompt.lower()
    assert "do not guess" in prompt.lower()


def test_omits_page_number_when_absent():
    """DOCX/TXT chunks have no page number (system-design.md) — the prompt must not print 'Page None'."""
    builder = PromptBuilder()
    chunks = [{"document_name": "Runbook.md", "page_number": None, "text": "Restart the service."}]

    prompt = builder.build("How do I restart the service?", chunks)

    assert "Page None" not in prompt
    assert "Runbook.md" in prompt


def test_includes_the_question_verbatim():
    builder = PromptBuilder()
    question = "How do I deploy the payment service?"

    prompt = builder.build(question, [])

    assert question in prompt
