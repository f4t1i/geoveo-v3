from pathlib import Path

from geoveo.backends.base import VideoBackend
from geoveo.logging import get_logger

log = get_logger(__name__)


class VeoBackend(VideoBackend):
    def render(self, prompt: str, conditioning_bundle_path: str, out_dir: str) -> str:
        out = Path(out_dir) / "video_veo_stub.mp4"
        out.write_text(
            f"stub veo render\nprompt={prompt}\nbundle={conditioning_bundle_path}\n",
            encoding="utf-8",
        )
        log.debug("backend.veo.render", output=str(out), prompt_len=len(prompt))
        return str(out)
