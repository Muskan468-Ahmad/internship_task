from typing import Optional, Tuple
from rapidfuzz import fuzz, process

# We’ll build the index on startup from DB (list of (id, question, answer))
class SimpleRetriever:
    def __init__(self, qa_list):
        # Store tuples: (id, question, answer)
        self.qa_list = qa_list
        self.questions = [q.question for q in qa_list]

    def best_match(self, query: str) -> Tuple[Optional[object], float]:
        if not self.qa_list:
            return None, 0.0
        # RapidFuzz returns (choice, score, idx)
        match = process.extractOne(query, self.questions, scorer=fuzz.token_set_ratio)
        if not match:
            return None, 0.0
        _, score, idx = match
        return self.qa_list[idx], score / 100.0  # normalize 0-1

