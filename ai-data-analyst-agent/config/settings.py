"""Central configuration. Change values here, not inside individual modules."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "data" / "uploads"
SAMPLE_DIR = BASE_DIR / "data" / "samples"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# --- LLM ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
LLM_TEMPERATURE = 0.1  # low: this app writes analysis plans/code, not prose

# --- Data limits ---
MAX_FILE_SIZE_MB = 200
MAX_ROWS_PREVIEW = 100
MAX_ROWS_FOR_LLM_SAMPLE = 20        # rows shown to the LLM as context, never the full sheet
ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}

# --- App ---
APP_TITLE = "AI Data Analyst"
APP_TAGLINE = "Upload your data. Ask anything. Let AI analyze it."
HIGH_CARDINALITY_THRESHOLD = 50      # categorical column considered "high cardinality" above this
OUTLIER_Z_THRESHOLD = 3.0
