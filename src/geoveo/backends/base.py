from abc import ABC, abstractmethod

class VideoBackend(ABC):
    @abstractmethod
    def render(self, prompt: str, conditioning_bundle_path: str, out_dir: str) -> str:
        raise NotImplementedError
