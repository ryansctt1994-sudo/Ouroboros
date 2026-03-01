"""__main__ shim so the package is runnable as ``python -m geodesic_mycelium_agent``."""

from geodesic_mycelium_agent.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
