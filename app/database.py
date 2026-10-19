import os
from dotenv import load_dotenv
from sqlmodel import SQLModel, Session, create_engine

# Load environment variables from .env
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./hasa.db")

# check_same_thread=False is required for SQLite in multithreaded FastAPI apps
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

def init_db():
    """Initializes the database and creates all tables."""
    SQLModel.metadata.create_all(engine)

def get_session():
    """FastAPI dependency for database sessions."""
    with Session(engine) as session:
        yield session