import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOADS_DIR = BASE_DIR / "uploads"

# Ensure uploads directory exists on disk
os.makedirs(UPLOADS_DIR, exist_ok=True)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./hasa.db")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")