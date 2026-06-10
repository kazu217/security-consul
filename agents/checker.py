import json
import re
from pathlib import Path
from datetime import datetime, timezone

from agents.base_agent import BaseAgent
from config.settings import STATE_ROOT
from integrations.openai_client import OpenAIClient
from models.lead import SecurityLead

MIN_QUALITY_SCORE = 5

BLOCKED_PHRASES = [
    "お世話になっております", "突然のご連絡", "よろしければ", "ご検討",
    "貴社", "弊社", "ご提案", "もしよろしければ", "ご多忙",
]

CHECKER_SYSTEM = "あなたはコールドメールの品質レビュアーです。JSONのみ出力してください。"


class CheckerAgent(BaseAgent):
    name = "checker"

    def __init__(self, state_manager=None, dry_run=False):
        super().__init__(state_manager, dry_run)
        self.client = OpenAIClient()

    def run(self) -> tuple[int, int]:
        pending_dir = STATE_ROOT / "messages" / "pending"
        approved_dir = STATE_ROOT / "messages" / "approved"
        blocked_dir = STATE_ROOT / "messages" / "blocked"

        files = list(pending_dir.glob("*.json"))
        if not files:
            self.log("No pending messages")
            return 0, 0

        approved = blocked = 0
        for f in files:
            d = json.loads(f.read_text())
            name = d.get("business_name", "?")
            body = d.get("cold_message", "")

            # L1: rule-based
            reasons = []
            for phrase in BLOCKED_PHRASES:
                if phrase in body:
                    reasons.append(f"NG_PHRASE: {phrase}")
            name_core = re.sub(r'^[㈱㈲]|株式会社|有限会社|\(.+\)|（.+）', '', name).strip()
            if name_core and name_core not in body and name not in body:
                reasons.append(f"MISSING_NAME: {name}")

            if reasons:
                self.log(f"BLOCKED (L1): {name} — {reasons}")
                if not self.dry_run:
                    f.rename(blocked_dir / f.name)
                blocked += 1
                continue

            # L2: GPT quality score
            try:
                prompt = f"店名: {name}\nメッセージ:\n{body}\n\n1〜10点で評価してください。\n{{\"score\": 整数, \"reasons\": [\"理由\"]}}"
                result = self.client.complete_json(CHECKER_SYSTEM, prompt, max_tokens=256)
                score = int(result.get("score", 5))
            except Exception as e:
                self.log(f"L2 check failed: {e} — approving by default")
                score = MIN_QUALITY_SCORE

            if score < MIN_QUALITY_SCORE:
                self.log(f"BLOCKED (L2, score={score}): {name}")
                if not self.dry_run:
                    f.rename(blocked_dir / f.name)
                blocked += 1
            else:
                self.log(f"APPROVED (score={score}): {name}")
                if not self.dry_run:
                    f.rename(approved_dir / f.name)
                approved += 1

        self.log(f"Done. Approved={approved}, Blocked={blocked}")
        return approved, blocked
