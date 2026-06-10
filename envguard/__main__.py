"""Allow running envguard as a module: python -m envguard."""

from envguard.cli import main
import sys

if __name__ == "__main__":
    sys.exit(main())
