"""
AnswerParser — extracts [1][2] citation markers from the LLM's answer text.

Only indices that are both present in the text AND within the range of
chunks actually sent are returned — an invalid or hallucinated citation
number is silently dropped rather than crashing the request.
"""

import re

_CITATION_PATTERN = re.compile(r"\[(\d+)\]")


class AnswerParser:
    def parse(self, answer_text: str, num_context_chunks: int = 0) -> tuple[str, list[int]]:
        """
        Returns (answer_text, used_indices) where used_indices are 0-based
        and deduplicated in first-seen order — [1] in the text maps to index 0.
        """
        raw_matches = _CITATION_PATTERN.findall(answer_text)

        used_indices: list[int] = []
        seen = set()
        for match in raw_matches:
            citation_number = int(match)
            zero_based = citation_number - 1
            if zero_based < 0 or zero_based >= num_context_chunks:
                continue  # invalid/hallucinated citation number — drop it
            if zero_based not in seen:
                seen.add(zero_based)
                used_indices.append(zero_based)

        return answer_text, used_indices
