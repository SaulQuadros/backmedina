"""Bootstrap comum às páginas Streamlit: garante `src/` no sys.path.

As páginas importam ``from _bootstrap import ...`` antes de usar o núcleo.
"""

from __future__ import annotations

import sys
from pathlib import Path

_RAIZ = Path(__file__).resolve().parents[1]
_SRC = _RAIZ / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

RAIZ_PROJETO = _RAIZ
DIR_EXEMPLO = _RAIZ / "z_docs" / "lwd" / "solocap"
