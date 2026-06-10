import json
from datetime import datetime, timezone
from pathlib import Path

from agents.base_agent import BaseAgent
from config.settings import STATE_ROOT, PITCHER_DAILY_SEND_LIMIT
from integrations.gmail_client import GmailClient
from models.lead import SecurityLead


class PitcherAgent(BaseAgent):
    name = "pitcher"

    def __init__(self, state_manager=None, dry_run=False):
        super().__init__(state_manager, dry_run)
        self.gmail = GmailClient()

    def run(self) -> int:
        approved_dir = STATE_ROOT / "messages" / "approved"
        sent_dir = STATE_ROOT / "messages" / "sent"

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        sent_today = self._count_sent_today(sent_dir, today)
        remaining = PITCHER_DAILY_SEND_LIMIT - sent_today

        if remaining <= 0:
            self.log(f"Daily limit ({PITCHER_DAILY_SEND_LIMIT}) reached")
            return 0

        files = sorted(approved_dir.glob("*.json"))[:remaining]
        if not files:
            self.log("No approved messages to send")
            return 0

        sent = 0
        for f in files:
            d = json.loads(f.read_text())
            name = d.get("business_name", "?")
            email = d.get("email", "")
            subject = d.get("subject_line", "セキュリティ診断のご報告")
            body = d.get("cold_message", "")

            self.log(f"Sending: {name} → {email}")
            try:
                if not self.dry_run:
                    self.gmail.send(email, subject, body)
                    d["sent_at"] = datetime.now(timezone.utc).isoformat()
                    d["date"] = today
                    dest = sent_dir / f.name
                    dest.write_text(json.dumps(d, ensure_ascii=False, indent=2))
                    f.unlink()
                sent += 1
            except Exception as e:
                self.log(f"Send failed {name}: {e}")

        self.log(f"Done. Sent={sent}")
        return sent

    def _count_sent_today(self, sent_dir: Path, today: str) -> int:
        count = 0
        for f in sent_dir.glob("*.json"):
            try:
                d = json.loads(f.read_text())
                if d.get("date") == today:
                    count += 1
            except Exception:
                pass
        return count
