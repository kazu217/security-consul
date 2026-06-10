import json
from datetime import datetime, timezone
from pathlib import Path

from config.settings import STATE_ROOT
from agents.scout import ScoutAgent
from agents.scanner import ScannerAgent
from agents.diagnoser import DiagnoserAgent
from agents.checker import CheckerAgent
from agents.pitcher import PitcherAgent
from models.lead import SecurityLead


class Pipeline:
    def __init__(self, dry_run=False):
        self.dry_run = dry_run

    def run(self):
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        print(f"\n{'='*50}\nSecurity Consul run: {today}\n{'='*50}\n")

        scout = ScoutAgent(dry_run=self.dry_run)
        queued = scout.run()
        print(f"[Scout] Queued {queued} leads")

        scanner = ScannerAgent(dry_run=self.dry_run)
        scanned = scanner.run()
        print(f"[Scanner] Scanned {scanned} sites")

        diagnoser = DiagnoserAgent(dry_run=self.dry_run)
        diagnosed = diagnoser.run()
        print(f"[Diagnoser] Diagnosed {diagnosed} leads")

        self._build_pending()

        checker = CheckerAgent(dry_run=self.dry_run)
        approved, blocked_count = checker.run()
        print(f"[Checker] Approved={approved}, Blocked={blocked_count}")

        pitcher = PitcherAgent(dry_run=self.dry_run)
        sent = pitcher.run()
        print(f"[Pitcher] Sent {sent} messages")

        print(f"\nPipeline complete: {today}")

    def _build_pending(self):
        diagnosed_dir = STATE_ROOT / "leads" / "diagnosed"
        pending_dir = STATE_ROOT / "messages" / "pending"
        sent_ids = self._sent_lead_ids()

        for path in diagnosed_dir.glob("*.json"):
            lead = SecurityLead.load(path)
            if not lead.cold_message or not lead.email:
                continue
            msg_path = pending_dir / f"msg_{lead.lead_id}.json"
            if msg_path.exists() or lead.lead_id in sent_ids:
                continue
            msg = {
                "lead_id": lead.lead_id,
                "business_name": lead.business_name,
                "email": lead.email,
                "subject_line": lead.subject_line,
                "cold_message": lead.cold_message,
                "opportunity_score": lead.opportunity_score,
            }
            msg_path.write_text(json.dumps(msg, ensure_ascii=False, indent=2))

    def _sent_lead_ids(self) -> set:
        sent_dir = STATE_ROOT / "messages" / "sent"
        ids = set()
        for f in sent_dir.glob("*.json"):
            try:
                d = json.loads(f.read_text())
                ids.add(d.get("lead_id", ""))
            except Exception:
                pass
        return ids
