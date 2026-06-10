from agents.base_agent import BaseAgent
from config.settings import STATE_ROOT
from integrations.openai_client import OpenAIClient
from models.lead import SecurityLead


SYSTEM_PROMPT = """あなたは中小企業向けWebセキュリティの専門家です。
自然な日本語で書いてください。営業っぽい表現・ビジネス用語・AI臭い表現は一切使わないこと。
以下のフレーズは絶対に使わないこと：「ご検討」「よろしければ」「お世話になっております」「突然のご連絡」
「貴社」「弊社」「ソリューション」「セキュリティ対策を強化」「リスクを低減」「ご提案」「もしよろしければ」。
締めは「藤原 / tobira-webdesign.com」だけ。JSONのみを出力してください。"""


def _build_prompt(lead: SecurityLead) -> str:
    from integrations.scanner_client import WebSecurityScanner
    scanner = WebSecurityScanner()
    top = scanner.get_top_finding(lead.findings) if lead.findings else None

    findings_text = "\n".join(
        f"- [{f.severity.upper()}] {f.title}: {f.detail}"
        for f in lead.findings
    ) or "セキュリティヘッダー未設定"

    if top:
        finding_intro = (
            f"「{lead.business_name}さんの{_domain(lead.website_url)}を拝見したところ、"
            f"{top.title}が確認されました」という旨を自然な1〜2文で（店名・ドメイン必須）"
        )
        opportunity = 8 if top.severity == "high" else 6
    else:
        finding_intro = (
            f"「{lead.business_name}さんの{_domain(lead.website_url)}を拝見したところ、"
            f"セキュリティ設定にいくつか気になる点がありました」という旨を自然な1〜2文で（店名・ドメイン必須）"
        )
        opportunity = 5

    return f"""店名: {lead.business_name}
ウェブサイト: {lead.website_url}
所在地: {lead.city}
発見した問題:
{findings_text}

以下のJSONを出力してください:
{{
  "cold_message": "以下の形式で出力すること：①「はじめまして、慶應義塾大学 理工学研究科の藤原と申します。」の後に空行\\n②{finding_intro}\\n③「サイト修正だけじゃなく業務の自動化も対応してます」に近い口語1文（ビジネス語・褒め言葉禁止）\\n④「興味があればご連絡ください。」の直後に改行なしで「藤原 / tobira-webdesign.com」。合計170〜220文字。",
  "subject_line": "20文字以内の件名（具体的な問題名を入れる）",
  "opportunity_score": {opportunity}
}}"""


def _domain(url: str) -> str:
    try:
        return url.split("/")[2]
    except Exception:
        return url


class DiagnoserAgent(BaseAgent):
    name = "diagnoser"

    def __init__(self, state_manager=None, dry_run=False):
        super().__init__(state_manager, dry_run)
        self.client = OpenAIClient()

    def run(self) -> int:
        scanned_dir = STATE_ROOT / "leads" / "scanned"
        diagnosed_dir = STATE_ROOT / "leads" / "diagnosed"

        leads_paths = list(scanned_dir.glob("*.json"))
        if not leads_paths:
            self.log("No scanned leads to diagnose")
            return 0

        diagnosed = 0
        for path in leads_paths:
            lead = SecurityLead.load(path)
            if not lead.findings:
                self.log(f"Skip (no findings): {lead.business_name}")
                if not self.dry_run:
                    path.unlink(missing_ok=True)
                continue

            self.log(f"Diagnosing: {lead.business_name}")
            try:
                prompt = _build_prompt(lead)
                result = self.run_with_retry(
                    self.client.complete_json,
                    SYSTEM_PROMPT, prompt,
                    max_tokens=512, use_cache=True,
                )
                lead.cold_message = result.get("cold_message", "")
                lead.subject_line = result.get("subject_line", "")
                lead.opportunity_score = float(result.get("opportunity_score", 5))
                lead.status = "diagnosed"
                if not self.dry_run:
                    lead.save(diagnosed_dir / path.name)
                    path.unlink(missing_ok=True)
                diagnosed += 1
            except Exception as e:
                self.log(f"Failed {lead.lead_id}: {e}")

        self.log(f"Done. Diagnosed={diagnosed}")
        return diagnosed
