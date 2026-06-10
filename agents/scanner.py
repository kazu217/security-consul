from agents.base_agent import BaseAgent
from config.settings import STATE_ROOT, SCANNER_MAX_LEADS_PER_RUN
from integrations.scanner_client import WebSecurityScanner
from models.lead import SecurityLead, SecurityFinding


class ScannerAgent(BaseAgent):
    name = "scanner"

    def run(self) -> int:
        raw_dir = STATE_ROOT / "leads" / "raw"
        scanned_dir = STATE_ROOT / "leads" / "scanned"
        scanner = WebSecurityScanner()

        leads = sorted(raw_dir.glob("*.json"))[:SCANNER_MAX_LEADS_PER_RUN]
        if not leads:
            self.log("No raw leads to scan")
            return 0

        scanned = 0
        for path in leads:
            lead = SecurityLead.load(path)
            self.log(f"Scanning: {lead.business_name} ({lead.website_url})")
            try:
                raw_findings = scanner.scan(lead.website_url)
                lead.findings = [
                    SecurityFinding(
                        severity=f.severity,
                        category=f.category,
                        title=f.title,
                        detail=f.detail,
                    )
                    for f in raw_findings
                ]
                lead.status = "scanned"
                if not self.dry_run:
                    lead.save(scanned_dir / path.name)
                    path.unlink(missing_ok=True)
                self.log(f"  → {len(lead.findings)} findings "
                         f"({sum(1 for f in lead.findings if f.severity=='high')} high)")
                scanned += 1
            except Exception as e:
                self.log(f"Scan failed {lead.lead_id}: {e}")

        self.log(f"Done. Scanned={scanned}")
        return scanned
