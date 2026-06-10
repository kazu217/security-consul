import re
import ssl
import socket
import datetime
import requests
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse


@dataclass
class SecurityFinding:
    severity: str
    category: str
    title: str
    detail: str


class WebSecurityScanner:
    """
    Scans publicly accessible web endpoints only.
    No authentication, no exploit — read-only HTTP requests.
    """

    SECURITY_HEADERS = [
        ("Strict-Transport-Security", "HSTS未設定", "medium"),
        ("Content-Security-Policy", "CSP（コンテンツセキュリティポリシー）未設定", "medium"),
        ("X-Frame-Options", "クリックジャッキング対策なし", "low"),
        ("X-Content-Type-Options", "MIMEスニッフィング対策なし", "low"),
    ]

    def scan(self, url: str) -> list[SecurityFinding]:
        if not url.startswith("http"):
            url = "https://" + url
        findings = []
        try:
            resp = requests.get(
                url, timeout=10, allow_redirects=True,
                headers={"User-Agent": "Mozilla/5.0 (compatible; SecurityCheck/1.0)"},
            )
            findings.extend(self._check_headers(resp))
            findings.extend(self._detect_cms(url, resp))
        except requests.exceptions.SSLError:
            findings.append(SecurityFinding("high", "ssl", "SSL証明書エラー",
                "SSL証明書の検証に失敗しました（期限切れまたは設定ミス）"))
        except Exception:
            pass

        findings.extend(self._check_ssl(url))
        return findings

    def _check_headers(self, resp) -> list[SecurityFinding]:
        findings = []
        for header, title, severity in self.SECURITY_HEADERS:
            if header not in resp.headers:
                findings.append(SecurityFinding(severity, "headers", title,
                    f"HTTPレスポンスに {header} ヘッダーが設定されていません"))
        return findings

    def _detect_cms(self, url: str, resp) -> list[SecurityFinding]:
        findings = []
        content = resp.text

        # WordPress detection
        if re.search(r'wp-content|wp-includes', content, re.I):
            version = self._get_wp_version(url, content)
            if version:
                try:
                    major = int(version.split(".")[0])
                    minor = int(version.split(".")[1]) if len(version.split(".")) > 1 else 0
                    if major < 6 or (major == 6 and minor < 4):
                        findings.append(SecurityFinding(
                            "high", "cms",
                            f"WordPress {version}（古いバージョン）",
                            f"WordPressのバージョンが{version}と古く、"
                            f"既知のXSS・SQLインジェクション脆弱性が存在します",
                        ))
                except Exception:
                    pass
            # Exposed login page
            try:
                r = requests.get(url.rstrip("/") + "/wp-login.php", timeout=5)
                if r.status_code == 200:
                    findings.append(SecurityFinding(
                        "medium", "exposure",
                        "WordPress管理画面が外部公開",
                        "/wp-login.php が誰でもアクセスできる状態です（ブルートフォース攻撃のリスク）",
                    ))
            except Exception:
                pass

        return findings

    def _get_wp_version(self, url: str, content: str) -> Optional[str]:
        m = re.search(r'<meta[^>]+generator[^>]+WordPress ([0-9.]+)', content, re.I)
        if m:
            return m.group(1)
        try:
            r = requests.get(url.rstrip("/") + "/readme.html", timeout=5)
            m = re.search(r'[Vv]ersion\s*([0-9]+\.[0-9.]+)', r.text)
            if m:
                return m.group(1)
        except Exception:
            pass
        # feed-based version
        try:
            r = requests.get(url.rstrip("/") + "/feed/", timeout=5)
            m = re.search(r'\?v=([0-9.]+)', r.text)
            if m:
                return m.group(1)
        except Exception:
            pass
        return None

    def _check_ssl(self, url: str) -> list[SecurityFinding]:
        findings = []
        parsed = urlparse(url)
        if parsed.scheme != "https":
            findings.append(SecurityFinding(
                "high", "ssl", "HTTPS未対応",
                "サイトがHTTPS化されていません。フォーム入力やCookieが平文で送信されます",
            ))
            return findings

        host = parsed.netloc.split(":")[0]
        try:
            ctx = ssl.create_default_context()
            with socket.create_connection((host, 443), timeout=5) as sock:
                with ctx.wrap_socket(sock, server_hostname=host) as ssock:
                    cert = ssock.getpeercert()
                    not_after = datetime.datetime.strptime(
                        cert["notAfter"], "%b %d %H:%M:%S %Y %Z"
                    )
                    days_left = (not_after - datetime.datetime.utcnow()).days
                    if days_left < 30:
                        findings.append(SecurityFinding(
                            "high", "ssl",
                            f"SSL証明書が{days_left}日で期限切れ",
                            f"SSL証明書の有効期限が {not_after.strftime('%Y年%m月%d日')} に切れます",
                        ))
        except ssl.SSLCertVerificationError:
            findings.append(SecurityFinding("high", "ssl", "SSL証明書エラー",
                "SSL証明書の検証に失敗しました"))
        except Exception:
            pass
        return findings

    def get_top_finding(self, findings: list) -> Optional[SecurityFinding]:
        order = {"high": 0, "medium": 1, "low": 2}
        return min(findings, key=lambda f: order.get(f.severity, 9), default=None)
