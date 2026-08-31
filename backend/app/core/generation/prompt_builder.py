"""
PromptBuilder — assembles the numbered-context, citation-instructed prompt
(system-design.md, section 3: "The Citation Mechanism").

This file is where hallucination-prevention actually lives: the instruction
to answer ONLY from context, and to say so explicitly when it can't.
"""

SYSTEM_INSTRUCTION = (
    "You are an enterprise knowledge assistant. Answer the question using ONLY "
    "the numbered context sections below. Cite every factual claim using the "
    "matching bracket number, e.g. [1], [2]. If the context does not contain "
    "the answer, say so plainly — do not guess or use outside knowledge."
)


class PromptBuilder:
    def build(self, query: str, context_chunks: list[dict]) -> str:
        """
        context_chunks: [{"document_name", "page_number", "text"}], in retrieval-rank order.
        The order here IS the citation numbering — chunk 0 becomes [1], chunk 1 becomes [2], etc.
        """
        context_block = "\n\n".join(self._format_chunk(i, chunk) for i, chunk in enumerate(context_chunks))

        return (
            f"{SYSTEM_INSTRUCTION}\n\n"
            f"CONTEXT:\n{context_block}\n\n"
            f"QUESTION: {query}\n\n"
            f"Answer with citations:"
        )

    @staticmethod
    def _format_chunk(index: int, chunk: dict) -> str:
        page_part = f", Page {chunk['page_number']}" if chunk.get("page_number") else ""
        return f'[{index + 1}] Source: "{chunk["document_name"]}"{page_part}\n    "{chunk["text"]}"'
