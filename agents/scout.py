"""
Scout: imports leads from Google Maps Consul diagnosed folder.
Only picks leads that have an email AND an outdated website to scan.
"""
import json
from pathlib import Path

from agents.base_agent import BaseAgent
from config.settings import GMAP_CONSUL_STATE, STATE_ROOT
from models.lead import SecurityLead


class ScoutAgent(BaseAgent):
    name = "scout"

    def run(self) -> int:
        raw_dir = STATE_ROOT / "leads" / "raw"
        already = {f.stem for f in raw_dir.glob("*.json")}

        scanned_dir = STATE_ROOT / "leads" / "scanned"
        already |= {f.stem for f in scanned_dir.glob("*.json")}

        diagnosed_dir = STATE_ROOT / "leads" / "diagnosed"
        already |= {f.stem for f in diagnosed_dir.glob("*.json")}

        sent_ids = self._sent_lead_ids()
        already |= sent_ids

        source = GMAP_CONSUL_STATE / "leads" / "diagnosed"
        if not source.exists():
            self.log("Google Maps Consul diagnosed folder not found")
            return 0

        queued = 0
        for f in sorted(source.glob("*.json")):
            lead_id = "sec_" + f.stem
            if lead_id in already:
                continue
            try:
                d = json.loads(f.read_text())
                b = d.get("business", {})
                email = b.get("email")
                url = b.get("website_url")
                if not email or not url:
                    continue
                if b.get("website_status") not in ("outdated",):
                    continue

                lead = SecurityLead(
                    lead_id=lead_id,
                    business_name=b.get("name", ""),
                    email=email,
                    website_url=url,
                    city=b.get("city", ""),
                    status="raw",
                )
                path = raw_dir / f"{lead_id}.json"
                lead.save(path)
                queued += 1
                self.log(f"Queued ({queued}): {lead.business_name}")
            except Exception as e:
                self.log(f"Skip {f.name}: {e}")

        self.log(f"Done. Queued={queued}")
        return queued

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
