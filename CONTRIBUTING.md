# Contributing

Thanks for considering a contribution to Security Consul.

## Good First Areas

- Add tests for pipeline state transitions
- Improve scanner adapters and documented checks
- Add safer defaults for local-only dry runs
- Improve setup and troubleshooting documentation
- Add examples for exporting findings to issue trackers

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python orchestrator/main.py --dry-run
```

## Pull Requests

Please keep pull requests focused and include a short explanation of the
workflow or risk being improved. Security-related changes should describe the
threat model and the expected safe behavior.
