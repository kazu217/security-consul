import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestrator.pipeline import Pipeline


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()

    pipeline = Pipeline(dry_run=args.dry_run)
    pipeline.run()


if __name__ == "__main__":
    main()
