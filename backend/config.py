import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')
MFC_USERNAME = os.getenv('MFC_USERNAME')

if not MFC_USERNAME:
    raise RuntimeError("MFC_USERNAME is not configured")