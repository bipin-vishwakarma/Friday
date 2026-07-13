# ════════════════════════════════════════════════════════════════════
# FRIDAY AI — Config Package
# ════════════════════════════════════════════════════════════════════
#
# Supports both:
#   from src.friday.config import settings      (module-level access)
#   from src.friday.config import DB_PATH        (direct attribute access)

from src.friday.config.settings import *   # noqa: F401,F403
from src.friday.config import settings     # noqa: F401
