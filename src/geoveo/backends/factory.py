from geoveo.backends.base import VideoBackend
from geoveo.backends.cogvideox import CogVideoXBackend
from geoveo.backends.animatediff import AnimateDiffBackend
from geoveo.backends.veo import VeoBackend

def get_backend(name: str) -> VideoBackend:
    normalized = name.lower()
    if normalized in {"cogvideox", "cogvideox_stub", "stub"}:
        return CogVideoXBackend()
    if normalized == "animatediff":
        return AnimateDiffBackend()
    if normalized == "veo":
        return VeoBackend()
    raise ValueError(f"Unsupported backend: {name}")
