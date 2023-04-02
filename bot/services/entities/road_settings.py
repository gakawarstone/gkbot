from dataclasses import dataclass
from datetime import time


@dataclass
class RoadSettings:
    time_focused: time
    time_relax: time
