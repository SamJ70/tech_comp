# backend/app/config.py
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
PLOTS_DIR = os.path.join(BASE_DIR, "plots")
DB_PATH = os.getenv("TRACKER_DB", os.path.join(DATA_DIR, "tracker.db"))

# Paths to expected files (you said you placed Wassenaar PDF there)
WASSENAAR_PDF = os.getenv("WASSENAAR_PDF", os.path.join(DATA_DIR, "wassenaar_list.pdf"))
WASSENAAR_INDEX = os.getenv("WASSENAAR_INDEX", os.path.join(DATA_DIR, "wassenaar_index.json"))
TIM_EXPORT = os.getenv("TIM_EXPORT", os.path.join(DATA_DIR, "tim_du_export.json"))
ASPI_EXPORT = os.getenv("ASPI_EXPORT", os.path.join(DATA_DIR, "aspi_export.json"))

# API keys (optional)
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")
# Fact verifier model
VERIFIER_MODEL = os.getenv("VERIFIER_MODEL", "all-MiniLM-L6-v2")

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(PLOTS_DIR, exist_ok=True)
