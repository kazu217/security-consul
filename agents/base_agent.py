import time
import traceback
import json
from datetime import datetime, timezone
from pathlib import Path

from config.settings import STATE_ROOT, MAX_RETRIES, RETRY_BACKOFF


class AgentError(Exception):
    pass


class BaseAgent:
    name = "base"

    def __init__(self, state_manager=None, dry_run: bool = False):
        self.state = state_manager
        self.dry_run = dry_run
        self.errors: list = []

    def log(self, msg: str):
        ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
        print(f"[{ts}] [{self.name.upper()}] {msg}")

    def run_with_retry(self, func, *args, **kwargs):
        last_error = None
        for attempt, wait in enumerate(RETRY_BACKOFF):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_error = e
                self.log(f"Attempt {attempt + 1}/{MAX_RETRIES} failed: {e}")
                if attempt < len(RETRY_BACKOFF) - 1:
                    time.sleep(wait)
        self._record_error(str(last_error))
        raise AgentError(f"{self.name} failed after {MAX_RETRIES} retries: {last_error}")

    def _record_error(self, error_msg: str):
        error_dir = STATE_ROOT / "errors"
        error_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
        path = error_dir / f"{self.name}_{ts}.json"
        path.write_text(json.dumps({
            "agent": self.name,
            "failed_at": datetime.now(timezone.utc).isoformat(),
            "error": error_msg,
            "traceback": traceback.format_exc(),
        }, ensure_ascii=False, indent=2), encoding="utf-8")
