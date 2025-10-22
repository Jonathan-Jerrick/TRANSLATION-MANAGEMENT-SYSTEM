"""Pytest configuration for translation management system tests."""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure the repository root is on ``sys.path`` so that ``app`` can be imported
# when the test suite is executed without installing the package.  This mirrors
# the behaviour developers expect when running ``pytest`` locally.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
