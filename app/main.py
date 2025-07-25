from flask import Flask, request, jsonify
from pydantic import ValidationError
from app.schemas import AskRequest
from app.db import SessionLocal
from app import __init__ as init
from app.config import settings
from app.crud import (
    create_interaction,
    get_all_qas,
    get_or_create_user,
    get_admin_settings,
    add_qa_pair
)
from app.openai_client import (
    enhance_with_context,
    answer_with_context,
    generate_image
)
from app.retrieval import VectorRetriever

# --- App setup ---
app = Flask(__name__)
init.init_db()

from app.admin import admin_bp
app.register_blueprint(admin_bp, url_prefix="/admin")

def is_image_request(text: str) -> bool:
    image_keywords = [
        "image", "picture", "photo", "draw", "generate an image",
        "show me an image", "make an image", "create an image",
        "illustration", "art of", "render", "logo", "poster"
    ]
    t = text.lower()
    return any(k in t for k in image_keywords)

def build_retriever():
    db = SessionLocal()
    qas = get_all_qas(db)
    db.close()
    return VectorRetriever(qas)

retriever = build_retriever()

def refresh_retriever():
    db = SessionLocal()
    try:
        qas = get_all_qas(db)
        retriever.refresh(qas)
    finally:
        db.close()

@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok"}

@app.route("/ask", methods=["POST"])
def ask():
    try:
        payload = AskRequest(**request.get_json())
    except ValidationError as e:
        return jsonify({"error": e.errors()}), 400

    db = SessionLocal()
    try:
        # 0) Ensure user exists
        user = get_or_create_user(db, payload.user)

        # 1) Admin toggle
        gpt_enabled = get_admin_settings(db).gpt_enabled
        if not gpt_enabled:
            create_interaction(
                db,
                user=user.identifier,
                question=payload.question,
                final_answer=None,
                matched=False,
                similarity=None,
                status="pending",
                is_image=is_image_request(payload.question)
            )
            return jsonify({"message": "Your question has been received.", "status": "queued"}), 202

        # 2) Image?
        if is_image_request(payload.question):
            try:
                image_url = generate_image(payload.question)
            except Exception:
                return jsonify({"error": "Image generation failed"}), 500

            create_interaction(
                db,
                user=user.identifier,
                question=payload.question,
                final_answer=image_url,
                matched=False,
                similarity=None,
                status="answered",
                is_image=True
            )
            return jsonify({"type": "image", "url": image_url})

        # 3) Text: Top-K retrieve
        top_ctx = retriever.top_k(payload.question, k=5)

        # If we *want* to keep a "matched" flag, define as "ctx not empty"
        matched = len(top_ctx) > 0

        if matched:
            # Use the first doc's answer as canonical (optional)
            canonical = top_ctx[0].get("answer", "")
            final_answer = enhance_with_context(payload.question, canonical, top_ctx)
        else:
            final_answer = answer_with_context(payload.question, top_ctx)

        # 4) Save interaction
        create_interaction(
            db,
            user=user.identifier,
            question=payload.question,
            final_answer=final_answer,
            matched=matched,
            similarity=None,  # similarity not used in vector version
            status="answered",
            is_image=False
        )

        # 5) Persist new QA into KB + refresh retriever
        add_qa_pair(db, payload.question, final_answer)
        refresh_retriever()

        return jsonify({"type": "text", "answer": final_answer})

    finally:
        db.close()

if __name__ == "__main__":
    app.run(port=5000, debug=True)


