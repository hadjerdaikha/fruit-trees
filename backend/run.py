"""Run the Oasis backend (uvicorn)."""

import os

import uvicorn

if __name__ == "__main__":
    from app.database import Base, SessionLocal, engine
    from app.seed_data import seed_species

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_species(db)
    finally:
        db.close()

    if os.getenv("SEED_DEMO") == "1":
        from app.demo_data import create_demo_data
        create_demo_data()
        print("Demo data seeded.")

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
