import json
from app.db import SessionLocal
from app.crud import bulk_insert_qas
from app import __init__ as init

def main():
    init.init_db()
    db = SessionLocal()
    data = json.load(open("qa_data.json"))
    bulk_insert_qas(db, data)
    db.close()

if __name__ == "__main__":
    main()
