from flask import Blueprint, jsonify, request
from app.db import SessionLocal
from app.crud import (
    set_gpt_enabled,
    get_admin_settings,
    get_pending_interactions,
    mark_interaction_answered,
    get_interaction_by_id,
    add_qa_pair,
    get_all_qas
)
from app.retrieval import SimpleRetriever

admin_bp = Blueprint("admin", __name__)

# We will import and use the global retriever from main via a lightweight trick.
# If you prefer, you can move the retriever into a shared module.
from app.main import refresh_retriever

@admin_bp.post("/gpt/enable")
def enable_gpt():
    db = SessionLocal()
    try:
        s = set_gpt_enabled(db, True)
        return jsonify({"gpt_enabled": s.gpt_enabled})
    finally:
        db.close()

@admin_bp.post("/gpt/disable")
def disable_gpt():
    db = SessionLocal()
    try:
        s = set_gpt_enabled(db, False)
        return jsonify({"gpt_enabled": s.gpt_enabled})
    finally:
        db.close()

@admin_bp.get("/gpt/status")
def gpt_status():
    db = SessionLocal()
    try:
        s = get_admin_settings(db)
        return jsonify({"gpt_enabled": s.gpt_enabled})
    finally:
        db.close()

@admin_bp.get("/interactions/pending")
def list_pending():
    db = SessionLocal()
    try:
        items = get_pending_interactions(db)
        data = [
            {
                "id": str(i.id),
                "user": i.user,
                "question": i.question,
                "created_at": i.created_at.isoformat()
            }
            for i in items
        ]
        return jsonify(data)
    finally:
        db.close()

@admin_bp.post("/interactions/answer")
def answer_pending():
    """
    Body: { "interaction_id": "...", "answer": "..." }
    - Marks the interaction as answered
    - Inserts (question, answer) into qa_pairs, so GPT sees it next time
    - Refreshes retriever
    """
    payload = request.get_json()
    interaction_id = payload.get("interaction_id")
    answer = payload.get("answer")
    if not interaction_id or not answer:
        return jsonify({"error": "interaction_id and answer are required"}), 400

    db = SessionLocal()
    try:
        # Get the original pending interaction for the question
        it = get_interaction_by_id(db, interaction_id)
        if not it:
            return jsonify({"error": "Interaction not found"}), 404

        # Mark it answered
        it = mark_interaction_answered(db, interaction_id, answer)

        # Add Q/A to qa_pairs
        add_qa_pair(db, it.question, answer)

        # Refresh retriever with new knowledge
        refresh_retriever()

        return jsonify({"status": "answered"})
    finally:
        db.close()
