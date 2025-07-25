from sqlalchemy.orm import Session
from app import models

# ---------- USERS ----------
def get_or_create_user(db: Session, identifier: str) -> models.User:
    user = db.query(models.User).filter_by(identifier=identifier).first()
    if not user:
        user = models.User(identifier=identifier)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user
# ---------------------------

# ---------- ADMIN SETTINGS ----------
def get_admin_settings(db: Session) -> models.AdminSettings:
    settings = db.query(models.AdminSettings).get(1)
    if not settings:
        settings = models.AdminSettings(id=1, gpt_enabled=True)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings

def set_gpt_enabled(db: Session, enabled: bool) -> models.AdminSettings:
    s = get_admin_settings(db)
    s.gpt_enabled = enabled
    db.commit()
    db.refresh(s)
    return s
# -----------------------------------

def create_interaction(db: Session, *, user: str, question: str, final_answer: str | None,
                       matched: bool, similarity: float | None, status: str = "answered",
                       is_image: bool = False):
    it = models.Interaction(
        user=user,
        question=question,
        final_answer=final_answer,
        matched=matched,
        similarity=similarity,
        status=status,
        is_image=is_image
    )
    db.add(it)
    db.commit()
    db.refresh(it)
    return it

def mark_interaction_answered(db: Session, interaction_id, answer: str):
    it = db.query(models.Interaction).filter(models.Interaction.id == interaction_id).first()
    if not it:
        return None
    it.final_answer = answer
    it.status = "answered"
    db.commit()
    db.refresh(it)
    return it

def get_interaction_by_id(db: Session, interaction_id):
    return db.query(models.Interaction).filter(models.Interaction.id == interaction_id).first()

def get_pending_interactions(db: Session):
    return db.query(models.Interaction).filter(models.Interaction.status == "pending").all()

def get_all_qas(db: Session):
    return db.query(models.QAPair).all()

def add_qa_pair(db: Session, question: str, answer: str) -> models.QAPair:
    qa = models.QAPair(question=question, answer=answer)
    db.add(qa)
    db.commit()
    db.refresh(qa)
    return qa

def bulk_insert_qas(db: Session, qa_list):
    for qa in qa_list:
        db.add(models.QAPair(question=qa["question"], answer=qa["answer"]))
    db.commit()

