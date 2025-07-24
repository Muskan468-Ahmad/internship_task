from pydantic import BaseModel

class AskRequest(BaseModel):
    user: str
    question: str
