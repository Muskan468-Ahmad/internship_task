import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    SIM_THRESHOLD: float = float(os.getenv("SIM_THRESHOLD", 0.80))

settings = Settings()
