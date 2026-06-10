from dataclasses import dataclass, field
from typing import Optional
import json


@dataclass
class SecurityFinding:
    severity: str        # "high" | "medium" | "low"
    category: str        # "ssl" | "headers" | "cms" | "exposure"
    title: str
    detail: str

    def to_dict(self):
        return {"severity": self.severity, "category": self.category,
                "title": self.title, "detail": self.detail}

    @classmethod
    def from_dict(cls, d):
        return cls(**d)


@dataclass
class SecurityLead:
    lead_id: str
    business_name: str
    email: str
    website_url: str
    city: str = ""
    findings: list = field(default_factory=list)     # list[SecurityFinding]
    cold_message: str = ""
    subject_line: str = ""
    opportunity_score: float = 5.0
    status: str = "raw"   # raw | scanned | diagnosed

    def to_dict(self):
        return {
            "lead_id": self.lead_id,
            "business_name": self.business_name,
            "email": self.email,
            "website_url": self.website_url,
            "city": self.city,
            "findings": [f.to_dict() if isinstance(f, SecurityFinding) else f
                         for f in self.findings],
            "cold_message": self.cold_message,
            "subject_line": self.subject_line,
            "opportunity_score": self.opportunity_score,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, d):
        findings = [SecurityFinding.from_dict(f) if isinstance(f, dict) else f
                    for f in d.get("findings", [])]
        return cls(
            lead_id=d["lead_id"],
            business_name=d["business_name"],
            email=d["email"],
            website_url=d["website_url"],
            city=d.get("city", ""),
            findings=findings,
            cold_message=d.get("cold_message", ""),
            subject_line=d.get("subject_line", ""),
            opportunity_score=d.get("opportunity_score", 5.0),
            status=d.get("status", "raw"),
        )

    def save(self, path):
        path.write_text(json.dumps(self.to_dict(), ensure_ascii=False, indent=2))

    @classmethod
    def load(cls, path):
        return cls.from_dict(json.loads(path.read_text()))
