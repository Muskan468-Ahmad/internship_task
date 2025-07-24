from flask import Flask, request, jsonify
from pydantic import ValidationError
from app.schemas import AskRequest
from app.config import settings
from app.db import SessionLocal
from app import __init__ as init
from app.crud import create_interaction, get_all_qas
from app.openai_client import enhance_answer, answer_direct, generate_image   # <-- NEW
from app.retrieval import SimpleRetriever

# --- App setup ---
app = Flask(__name__)
init.init_db()  # ensure tables exist

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
        # 1) If it's an image request, skip the QA retrieval and go straight to image gen
        if is_image_request(payload.question):
            try:
                image_url = generate_image(payload.question)
            except Exception as ex:
                # Make sure you log ex in real code
                return jsonify({"error": "Image generation failed"}), 500

            # Persist interaction (you can add an `is_image` column later if you like)
            create_interaction(
                db,
                user=payload.user,
                question=payload.question,
                final_answer=image_url,
                matched=False,
                similarity=None
            )

            return jsonify({
                "type": "image",
                "url": image_url
            })

        # 2) Otherwise, do normal QA flow
        qa_match, similarity = retriever.best_match(payload.question)

        if qa_match and similarity >= settings.SIM_THRESHOLD:
            final_answer = enhance_answer(payload.question, qa_match.answer)
            matched = True
        else:
            final_answer = answer_direct(payload.question)
            matched = False
            similarity = None

        create_interaction(
            db,
            user=payload.user,
            question=payload.question,
            final_answer=final_answer,
            matched=matched,
            similarity=similarity
        )

        return jsonify({
            "type": "text",
            "answer": final_answer,
            "matched": matched,
            "similarity": similarity
        })

    finally:
        db.close()

if __name__ == "__main__":
    app.run(port=5000, debug=True)
