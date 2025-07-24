import openai
from app.config import settings

openai.api_key = settings.OPENAI_API_KEY

def enhance_answer(user_question: str, canonical_answer: str) -> str:
    prompt = (
        f"User asked: {user_question}\n"
        f"Here is our canonical answer:\n{canonical_answer}\n\n"
        "Rewrite it to be clearer and more structured. Do not change facts."
    )
    resp = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return resp["choices"][0]["message"]["content"].strip()

def answer_direct(question: str) -> str:
    resp = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": question}]
    )
    return resp["choices"][0]["message"]["content"].strip()
