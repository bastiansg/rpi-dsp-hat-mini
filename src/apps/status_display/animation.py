import random
from collections import OrderedDict
from collections.abc import Iterable
from pathlib import Path

from PIL import Image


class FrameAnimation:
    def __init__(self, path: Path, frame_duration: float):
        self.path = path
        paths = sorted(path.glob("*.png"))
        if not paths:
            raise ValueError(f"No PNG frames found in directory: {path}")

        self.frames = tuple(load_png_frame(path) for path in paths)
        self.frame_duration = frame_duration
        self.index = 0

    def next_frame(self) -> Image.Image:
        frame = self.frames[self.index]
        self.index = (self.index + 1) % len(self.frames)
        return frame

    def reset(self) -> None:
        self.index = 0

    def close(self) -> None:
        for frame in self.frames:
            frame.close()


class FrameAnimationDeck:
    def __init__(
        self,
        paths: Iterable[Path],
        frame_duration: float,
        max_cached_animations: int = 1,
    ):
        self.paths = list(paths)
        if not self.paths:
            raise ValueError("No frame directories found")

        random.shuffle(self.paths)
        self.index = -1
        self.frame_duration = frame_duration
        self.max_cached_animations = max(max_cached_animations, 1)
        self.animation_cache: OrderedDict[Path, FrameAnimation] = OrderedDict()

    def next_animation(self) -> FrameAnimation:
        self.index = (self.index + 1) % len(self.paths)
        return self.current_animation()

    def previous_animation(self) -> FrameAnimation:
        self.index = (self.index - 1) % len(self.paths)
        return self.current_animation()

    def current_animation(self) -> FrameAnimation:
        path = self.paths[self.index]
        animation = self.animation_cache.get(path)
        if animation is None:
            while len(self.animation_cache) >= self.max_cached_animations:
                _path, old_animation = self.animation_cache.popitem(last=False)
                old_animation.close()

            animation = FrameAnimation(path, self.frame_duration)
            self.animation_cache[path] = animation
        else:
            self.animation_cache.move_to_end(path)

        animation.reset()
        return animation

    def close(self) -> None:
        for animation in self.animation_cache.values():
            animation.close()

        self.animation_cache.clear()


def load_png_frame(path: Path) -> Image.Image:
    with Image.open(path) as image:
        return image.copy()


def frame_directories(directory: Path) -> Iterable[Path]:
    paths = sorted(path for path in directory.iterdir() if path.is_dir())
    if not paths:
        raise ValueError(f"No frame directories found in directory: {directory}")

    return iter(paths)
