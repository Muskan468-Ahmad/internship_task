import os
import json
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()  # local dev convenience


def _get_env(name: str, default=None):
    v = os.getenv(name, default)
    if v is None:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return v


@lru_cache(maxsize=1)
def _db_url_from_secrets_manager() -> str:
    """
    Build a SQLAlchemy DB URL from an AWS Secrets Manager JSON secret.
    Falls back to DATABASE_URL if RDS_SECRET_ARN isn't set.
    """
    secret_arn = os.getenv("RDS_SECRET_ARN")
    if not secret_arn:
        # Local dev or simple env-var based prod
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            raise RuntimeError("Neither RDS_SECRET_ARN nor DATABASE_URL is set.")
        return db_url

    # We’re on AWS and want to read from Secrets Manager
    import boto3

    region = os.getenv("AWS_REGION", "ap-south-1")
    client = boto3.client("secretsmanager", region_name=region)
    resp = client.get_secret_value(SecretId=secret_arn)

    secret = json.loads(resp["SecretString"])
    user = secret["username"]
    pwd = secret["password"]
    host = secret["host"]
    port = secret.get("port", 5432)
    dbname = secret["dbname"]

    # Always require SSL to RDS
    return f"postgresql+psycopg2://{user}:{pwd}@{host}:{port}/{dbname}?sslmode=require"


class Settings:
    # LLM
    OPENAI_API_KEY: str = _get_env("OPENAI_API_KEY")
    # Retrieval threshold (used when you plug in semantic/fuzzy match)
    SIM_THRESHOLD: float = float(os.getenv("SIM_THRESHOLD", 0.80))
    # Database URL (resolved from Secrets Manager or plain env)
    DATABASE_URL: str = _db_url_from_secrets_manager()


settings = Settings()
