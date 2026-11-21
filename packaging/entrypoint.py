"""Standalone Linux binary entrypoint; the canonical runtime remains network_core."""
from network_core.server import main

if __name__ == "__main__":
    main()
