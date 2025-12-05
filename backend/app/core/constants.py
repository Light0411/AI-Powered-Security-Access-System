from collections import OrderedDict
from typing import Dict

ROLE_LADDER = ["guest", "student", "staff", "security", "admin"]
ROLE_WEIGHTS: Dict[str, int] = OrderedDict((role, idx) for idx, role in enumerate(ROLE_LADDER))
GATE_MIN_ROLE = {
    "outer": "guest",
    "inner": "staff",
}
DEFAULT_PROGRAMMES = [
    "Engineering",
    "Computer Science",
    "Business",
    "Media",
]
