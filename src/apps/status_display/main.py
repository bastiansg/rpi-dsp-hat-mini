import signal
import time
from importlib import import_module
from pathlib import Path
from random import shuffle
from typing import Any

from PIL import Image, ImageOps, ImageSequence, UnidentifiedImageError
from rich.console import Console

from src.apps.status_display.hardware import ButtonPressReader, DisplayHatMiniScreen
from src.apps.status_display.settings import settings

console = Console()
ROOT_DIR = Path(__file__).resolve().parents[3]
GIF_DIR = ROOT_DIR / "gif"


def clamp(value: float, minimum: float, maximum: float) -> float:
    return min(max(value, minimum), maximum)


def discover_gifs() -> list[Path]:
    gifs = sorted(GIF_DIR.glob("*.gif"))
    shuffle(gifs)
    return gifs


class GifPlayer:
    def __init__(
        self,
        paths: list[Path],
        width: int,
        height: int,
        fallback_frame_seconds: float,
    ):
        if not paths:
            msg = f"No GIF files found in {GIF_DIR}"
            raise RuntimeError(msg)

        self.paths = paths
        self.size = (width, height)
        self.fallback_frame_seconds = fallback_frame_seconds
        self.index = 0
        self.frame_index = 0
        self.frame_started = time.monotonic()
        self.frames: list[Image.Image] = []
        self.durations: list[float] = []
        self.load_current()

    @property
    def current_path(self) -> Path:
        return self.paths[self.index]

    def load_current(self) -> None:
        for frame in self.frames:
            frame.close()

        self.frames = []
        self.durations = []
        self.frame_index = 0
        self.frame_started = time.monotonic()

        try:
            with Image.open(self.current_path) as image:
                for raw_frame in ImageSequence.Iterator(image):
                    duration_ms = raw_frame.info.get("duration", 0)
                    self.durations.append(
                        max(duration_ms / 1000, self.fallback_frame_seconds)
                    )
                    self.frames.append(self._fit(raw_frame.convert("RGB")))
        except (OSError, UnidentifiedImageError) as exc:
            msg = f"Could not load GIF {self.current_path}"
            raise RuntimeError(msg) from exc

        if not self.frames:
            msg = f"GIF has no frames: {self.current_path}"
            raise RuntimeError(msg)

        console.log(f"GIF {self.index + 1}/{len(self.paths)}: {self.current_path.name}")

    def next(self) -> None:
        self.index = (self.index + 1) % len(self.paths)
        self.load_current()

    def previous(self) -> None:
        self.index = (self.index - 1) % len(self.paths)
        self.load_current()

    def frame(self) -> Image.Image:
        now = time.monotonic()
        while now - self.frame_started >= self.durations[self.frame_index]:
            self.frame_started += self.durations[self.frame_index]
            self.frame_index = (self.frame_index + 1) % len(self.frames)

        return self.frames[self.frame_index]

    def close(self) -> None:
        for frame in self.frames:
            frame.close()

    def _fit(self, frame: Image.Image) -> Image.Image:
        image = ImageOps.contain(frame, self.size)
        fitted = Image.new("RGB", self.size, (0, 0, 0))
        fitted.paste(
            image,
            (
                (self.size[0] - image.width) // 2,
                (self.size[1] - image.height) // 2,
            ),
        )
        return fitted.rotate(180)


class ProximityNextTrigger:
    def __init__(
        self,
        threshold: int,
        cooldown_seconds: float,
        baseline_samples: int,
        baseline_margin: int,
    ):
        ltr559_module = import_module("ltr559")

        self.sensor: Any = ltr559_module.LTR559()
        self.threshold = max(
            threshold,
            self._measure_baseline(baseline_samples) + baseline_margin,
        )
        self.cooldown_seconds = cooldown_seconds
        self.was_near = False
        self.last_triggered = 0.0
        console.log(f"proximity sensor ready, threshold: {self.threshold}")

    def next_requested(self) -> bool:
        proximity = int(self.sensor.get_proximity(passive=False))
        is_near = proximity >= self.threshold
        now = time.monotonic()
        should_trigger = (
            is_near
            and not self.was_near
            and now - self.last_triggered >= self.cooldown_seconds
        )

        self.was_near = is_near
        if should_trigger:
            self.last_triggered = now
            console.log(f"proximity next trigger: {proximity}")

        return should_trigger

    def _measure_baseline(self, samples: int) -> int:
        readings = [
            int(self.sensor.get_proximity(passive=False))
            for _sample in range(max(samples, 1))
        ]
        baseline = max(readings)
        console.log(f"proximity baseline: {baseline}")
        return baseline


def setup_proximity_trigger() -> ProximityNextTrigger | None:
    if not settings.proximity_enabled:
        return None

    try:
        return ProximityNextTrigger(
            settings.proximity_threshold,
            settings.proximity_cooldown_seconds,
            settings.proximity_baseline_samples,
            settings.proximity_baseline_margin,
        )
    except (ImportError, OSError, RuntimeError) as exc:
        console.log(f"proximity sensor disabled: {exc}")
        return None


def blink_change_led(screen: DisplayHatMiniScreen) -> None:
    screen.set_led(1.0, 0.0, 0.0)
    time.sleep(settings.gif_change_blink_seconds)
    screen.set_led(0, 0, 0)


def main() -> None:
    screen = DisplayHatMiniScreen(
        settings.width,
        settings.height,
        settings.initial_backlight,
    )
    player = GifPlayer(
        discover_gifs(),
        settings.width,
        settings.height,
        settings.frame_seconds,
    )
    buttons = ButtonPressReader(
        screen,
        debounce_seconds=settings.button_debounce_seconds,
    )
    proximity = setup_proximity_trigger()
    backlight = settings.initial_backlight
    running = True

    def stop(_signum: int, _frame: object) -> None:
        nonlocal running
        running = False

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)

    buttons.setup()

    try:
        while running:
            for name in buttons.pressed():
                if name == "X":
                    blink_change_led(screen)
                    player.previous()
                elif name == "Y":
                    blink_change_led(screen)
                    player.next()
                elif name == "A":
                    backlight = clamp(
                        backlight - settings.backlight_step,
                        settings.min_backlight,
                        settings.max_backlight,
                    )
                    screen.set_backlight(backlight)
                    console.log(f"backlight decreased to {backlight:.2f}")
                elif name == "B":
                    backlight = clamp(
                        backlight + settings.backlight_step,
                        settings.min_backlight,
                        settings.max_backlight,
                    )
                    screen.set_backlight(backlight)
                    console.log(f"backlight increased to {backlight:.2f}")

            if proximity is not None and proximity.next_requested():
                blink_change_led(screen)
                player.next()

            screen.set_led(0, 0, 0)
            screen.show(player.frame())
            time.sleep(settings.frame_seconds)
    finally:
        player.close()
        screen.close()


if __name__ == "__main__":
    main()
