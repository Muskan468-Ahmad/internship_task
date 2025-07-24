from sqlalchemy.orm import Session
from app import models

def create_interaction(db: Session, *, user: str, question: str, final_answer: str,
                       matched: bool, similarity: float | None):
    it = models.Interaction(
        user=user,
        question=question,
        final_answer=final_answer,
        matched=matched,
        similarity=similarity
    )
    db.add(it)
    db.commit()
    db.refresh(it)
    return it

def get_all_qas(db: Session):
    return db.query(models.QAPair).all()

def bulk_insert_qas(db: Session, qa_list):
    for qa in qa_list:
        db.add(models.QAPair(question=qa["question"], answer=qa["answer"]))
    db.commit()
