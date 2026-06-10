import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).parent.parent
STATE_ROOT = PROJECT_ROOT / "state"

SCANNER_TIMEOUT = 10          # seconds per HTTP request
SCANNER_MAX_LEADS_PER_RUN = 30
PITCHER_DAILY_SEND_LIMIT = 20

GMAP_CONSUL_STATE = Path("/Users/uri/claude/Google-Map-consul/state")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS", "tobira.webdesign@gmail.com")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")

MAX_RETRIES = 3
RETRY_BACKOFF = [5, 15, 45]
