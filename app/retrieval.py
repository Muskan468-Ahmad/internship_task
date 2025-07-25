from typing import Optional, Tuple
from rapidfuzz import fuzz, process

class SimpleRetriever:
    def __init__(self, qa_list):
        self.refresh(qa_list)

    def refresh(self, qa_list):
        """Refresh in-memory index after new QAs are added."""
        self.qa_list = qa_list or []
        self.questions = [q.question for q in self.qa_list]

    def best_match(self, query: str) -> Tuple[Optional[object], float]:
        if not self.qa_list:
            return None, 0.0
        match = process.extractOne(query, self.questions, scorer=fuzz.token_set_ratio)
        if not match:
            return None, 0.0
        _, score, idx = match
        return self.qa_list[idx], score / 100.0
