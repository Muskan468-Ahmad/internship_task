import openai
from app.config import settings

openai.api_key = settings.OPENAI_API_KEY

def enhance_with_kb(user_question: str, canonical_answer: str, kb_text: str) -> str:
    """
    Enhance the canonical answer but let the model see the whole KB too.
    """
    prompt = (
        "You are given a knowledge base composed of Q&A pairs. "
        "Use it to provide a clear, structured, and accurate answer. "
        "Do not contradict the canonical answer facts.\n\n"
        f"KNOWLEDGE BASE:\n{kb_text}\n\n"
        f"USER QUESTION:\n{user_question}\n\n"
        f"CANONICAL ANSWER:\n{canonical_answer}\n\n"
        "Rewrite and enhance the canonical answer without introducing new unsupported facts."
    )
    resp = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return resp["choices"][0]["message"]["content"].strip()

def answer_with_kb(question: str, kb_text: str) -> str:
    """
    If we don't have a solid match, answer using the whole KB as context.
    """
    prompt = (
        "You are given a knowledge base composed of Q&A pairs. "
        "Answer the user's question based strictly on this knowledge. "
        "If the answer isn't covered, say so clearly.\n\n"
        f"KNOWLEDGE BASE:\n{kb_text}\n\n"
        f"USER QUESTION:\n{question}\n\n"
        "Answer:"
    )
    resp = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return resp["choices"][0]["message"]["content"].strip()

# Keep if you still want direct/simple calls:
def answer_direct(question: str) -> str:
    resp = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": question}]
    )
    return resp["choices"][0]["message"]["content"].strip()

# If you still want image generation:
def generate_image(prompt: str) -> str:
    response = openai.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        size="1024x1024"
    )
    return response.data[0].url

