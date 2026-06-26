# Security Consul

Agentic website security triage for small teams and independent maintainers.

Security Consul is a Python pipeline that scans small websites, summarizes
findings with an LLM, checks quality and duplicate state, and prepares a clear
remediation note. It is designed as a maintainable OSS reference for lightweight
security review workflows rather than a replacement for professional penetration
testing.

## Why This Exists

Small organizations often ship and maintain websites without a dedicated
security team. Security Consul explores a practical maintainer workflow:

- collect a bounded list of sites to review
- run repeatable HTTP and configuration checks
- convert noisy scan output into human-readable triage
- keep state between runs to avoid duplicate work
- optionally draft an outreach or remediation message

The project is intentionally modular so contributors can replace the scanner,
state backend, LLM provider, or delivery channel without rewriting the pipeline.

## Pipeline

```text
Scout -> Scanner -> Diagnoser -> Checker -> Pitcher
```

| Agent | Responsibility |
| --- | --- |
| Scout | Loads or prepares candidate sites for review |
| Scanner | Runs website security and configuration checks |
| Diagnoser | Uses an LLM to explain findings and remediation priority |
| Checker | Deduplicates, validates quality, and enforces run limits |
| Pitcher | Prepares or sends an optional remediation message |

## Current Features

- File-based state machine for local, auditable runs
- OpenAI-backed diagnosis layer
- Configurable retry and backoff behavior
- Optional Gmail delivery integration
- Dry-run mode for review before any delivery step
- Small dependency footprint: `requests`, `python-dotenv`, and `openai`

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Then edit `.env`:

```bash
OPENAI_API_KEY=your-openai-api-key
GMAIL_ADDRESS=
GMAIL_APP_PASSWORD=
```

Run locally:

```bash
python orchestrator/main.py --dry-run
```

## Configuration

The main settings live in `config/settings.py`.

- `SCANNER_TIMEOUT`: HTTP timeout per request
- `SCANNER_MAX_LEADS_PER_RUN`: maximum reviewed sites per run
- `PITCHER_DAILY_SEND_LIMIT`: safety limit for the optional delivery step
- `STATE_ROOT`: local JSON state directory

## Safety Notes

Use Security Consul only on websites you own, administer, or have permission to
test. Keep `.env` private. The repository ignores `.env`, local virtual
environments, caches, and generated state files by default.

## Roadmap

- Add a pluggable scanner interface with example checks
- Add tests for pipeline idempotency and duplicate suppression
- Add structured JSON output for issue trackers and CI jobs
- Add GitHub Actions examples for scheduled maintainer triage
- Improve documentation for safe, permission-based scanning

## Contributing

Issues and pull requests are welcome. Good first contributions include tests,
scanner adapters, documentation improvements, and safer defaults for local
triage workflows.

## License

MIT
