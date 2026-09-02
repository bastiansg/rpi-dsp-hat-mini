import random
from collections import OrderedDict, deque
from collections.abc import Iterable
from pathlib import Path
from threading import Condition, Thread

from PIL import Image


class FrameAnimation:
    def __init__(self, path: Path, frame_duration: float, frame_buffer_size: int):
        self.path = path
        self.paths = tuple(sorted(path.glob("*.png")))
        if not self.paths:
            raise ValueError(f"No PNG frames found in directory: {path}")

        self.frame_duration = frame_duration
        self.frame_buffer_size = max(frame_buffer_size, 1)
        self._condition = Condition()
        self._frames: deque[Image.Image] = deque()
        self._next_index = 0
        self._generation = 0
        self._error: Exception | None = None
        self._closed = False
        self._worker = Thread(
            target=self._preload_frames,
            name=f"frame-preloader-{path.name}",
            daemon=True,
        )
        self._worker.start()

    def next_frame(self) -> Image.Image:
        with self._condition:
            self._condition.wait_for(
                lambda: bool(self._frames) or self._error is not None or self._closed
            )
            if self._error is not None:
                raise RuntimeError(
                    f"Failed to preload frames from: {self.path}"
                ) from self._error
            if self._closed:
                raise RuntimeError(f"Animation is closed: {self.path}")

            frame = self._frames.popleft()
            self._condition.notify()
            return frame

    def reset(self) -> None:
        with self._condition:
            self._generation += 1
            self._next_index = 0
            self._close_frames()
            self._condition.notify_all()

    def close(self) -> None:
        with self._condition:
            self._closed = True
            self._condition.notify_all()

        self._worker.join()
        self._close_frames()

    def _preload_frames(self) -> None:
        while True:
            with self._condition:
                self._condition.wait_for(
                    lambda: len(self._frames) < self.frame_buffer_size or self._closed
                )
                if self._closed:
                    return

                path = self.paths[self._next_index]
                self._next_index = (self._next_index + 1) % len(self.paths)
                generation = self._generation

            try:
                frame = load_png_frame(path)
            except Exception as exc:
                with self._condition:
                    self._error = exc
                    self._condition.notify_all()
                return

            with self._condition:
                if generation != self._generation or self._closed:
                    frame.close()
                    continue

                self._frames.append(frame)
                self._condition.notify()

    def _close_frames(self) -> None:
        for frame in self._frames:
            frame.close()

        self._frames.clear()


class FrameAnimationDeck:
    def __init__(
        self,
        paths: Iterable[Path],
        frame_duration: float,
        frame_buffer_size: int,
        max_cached_animations: int = 1,
    ):
        self.paths = list(paths)
        if not self.paths:
            raise ValueError("No frame directories found")

        random.shuffle(self.paths)
        self.index = -1
        self.frame_duration = frame_duration
        self.frame_buffer_size = max(frame_buffer_size, 1)
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

            animation = FrameAnimation(
                path,
                self.frame_duration,
                self.frame_buffer_size,
            )

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
