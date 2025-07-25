from typing import List
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from app.config import settings

class VectorRetriever:
    """
    Wraps a FAISS vector store. No GPU required.
    """
    def __init__(self, qas):
        self.emb = OpenAIEmbeddings(api_key=settings.OPENAI_API_KEY,
                                    model=settings.EMBEDDING_MODEL)
        self.build(qas)

    def build(self, qas):
        texts = [f"Q: {q.question}\nA: {q.answer}" for q in qas]
        metadatas = [{"id": str(q.id), "question": q.question, "answer": q.answer} for q in qas]
        if texts:
            self.vs = FAISS.from_texts(texts=texts, embedding=self.emb, metadatas=metadatas)
        else:
            # empty store
            self.vs = None

    def refresh(self, qas):
        self.build(qas)

    def top_k(self, query: str, k: int = 5) -> List[dict]:
        if not self.vs:
            return []
        docs = self.vs.similarity_search(query, k=k)
        return [{"text": d.page_content, **(d.metadata or {})} for d in docs]

