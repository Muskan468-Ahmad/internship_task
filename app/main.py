from flask import Flask, request, jsonify
from pydantic import ValidationError
from app.schemas import AskRequest
from app.config import settings
from app.db import SessionLocal
from app import __init__ as init
from app.crud import (
    create_interaction,
    get_all_qas,
    get_or_create_user,
    get_admin_settings,
    add_qa_pair
)
from app.openai_client import (
    enhance_with_kb,
    answer_with_kb,
    generate_image
)
from app.retrieval import SimpleRetriever

# --- App setup ---
app = Flask(__name__)
init.init_db()  # ensure tables exist

from app.admin import admin_bp
app.register_blueprint(admin_bp, url_prefix="/admin")

# --- Helpers ---
def is_image_request(text: str) -> bool:
    image_keywords = [
        "image", "picture", "photo", "draw", "generate an image",
        "show me an image", "make an image", "create an image",
        "illustration", "art of", "render", "logo", "poster"
    ]
    t = text.lower()
    return any(k in t for k in image_keywords)

# Build retriever cache at startup
def build_retriever():
    db = SessionLocal()
    qas = get_all_qas(db)
    db.close()
    return SimpleRetriever(qas)

retriever = build_retriever()

def refresh_retriever():
    """Reload QAs from DB into retriever after we add a new one."""
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

        # 1) Check admin toggle (silent to user)
        settings_row = get_admin_settings(db)
        gpt_enabled = settings_row.gpt_enabled

        # 2) If GPT is disabled, store and return a neutral message
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
            return jsonify({
                "message": "Your question has been received.",
                "status": "queued"
            }), 202

        # 3) GPT is enabled → proceed
        #    (a) If it's an image request, go generate image
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
            # (Optional) Usually you wouldn't add images to QA KB. Skip.
            return jsonify({
                "type": "image",
                "url": image_url
            })

        #    (b) Text Q&A flow
        qa_match, similarity = retriever.best_match(payload.question)

        # Build KB text (all QAs so far)
        all_qas = get_all_qas(db)
        kb_text = "\n".join([f"Q: {q.question}\nA: {q.answer}" for q in all_qas])

        if qa_match and similarity >= settings.SIM_THRESHOLD:
            final_answer = enhance_with_kb(payload.question, qa_match.answer, kb_text)
            matched = True
        else:
            final_answer = answer_with_kb(payload.question, kb_text)
            matched = False
            similarity = None

        # 4) Save interaction
        create_interaction(
            db,
            user=user.identifier,
            question=payload.question,
            final_answer=final_answer,
            matched=matched,
            similarity=similarity,
            status="answered",
            is_image=False
        )

        # 5) Also append this (Q, A) to qa_pairs so GPT knows it next time
        add_qa_pair(db, payload.question, final_answer)

        # 6) Refresh retriever so it sees the newly added QA
        refresh_retriever()

        return jsonify({
            "type": "text",
            "answer": final_answer
        })

    finally:
        db.close()

if __name__ == "__main__":
    app.run(port=5000, debug=True)

