from pathlib import Path
from geoveo.backends.base import VideoBackend

class VeoBackend(VideoBackend):
    def render(self, prompt: str, conditioning_bundle_path: str, out_dir: str) -> str:
        out = Path(out_dir) / "video_veo_stub.mp4"
        out.write_text(f"stub veo render\nprompt={prompt}\nbundle={conditioning_bundle_path}\n", encoding="utf-8")
        return str(out)
