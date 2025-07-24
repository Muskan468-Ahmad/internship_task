from app.db import Base, engine
from app import models

def init_db():
    Base.metadata.create_all(bind=engine)
