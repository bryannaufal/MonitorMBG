"""Deprecated shim — use ``app.dbctl``.

Kept so ``python -m app.seed`` (documented in older notes) still works.  The
real loader lives in :mod:`app.dbctl`, which also handles scenarios, reset, and
seed-vs-runtime provenance.
"""

from __future__ import annotations

from app.dbctl import main

if __name__ == "__main__":
    print("⚠️  `python -m app.seed` is deprecated — use `python -m app.dbctl seed`.\n")
    import sys

    sys.argv = [sys.argv[0], "seed", *sys.argv[1:]]
    main()
