from dataclasses import dataclass
from typing import Optional

@dataclass
class Track:
    id: int
    title: str
    file_path: str
    tags: Optional[str] = None
    duration: float = 0.0

@dataclass
class SelectedTrack:
    id: int
    title: str
    file_path: str
    duration: float
    track_id: int
    position: int
    panel_id: int

@dataclass
class Panel:
    id: int
    name: str
    volume: float
    loop_enabled: bool
    fade_enabled: bool
