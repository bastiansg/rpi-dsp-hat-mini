import signal
import time
from importlib import import_module
from pathlib import Path
from typing import Any

from rich.console import Console

from src.apps.status_display.animation import FrameAnimationDeck, frame_directories
from src.apps.status_display.hardware import ButtonPressReader, DisplayHatMiniScreen
from src.apps.status_display.settings import settings

console = Console()
ROOT_DIR = Path(__file__).resolve().parents[3]


def clamp(value: float, minimum: float, maximum: float) -> float:
    return min(max(value, minimum), maximum)


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
    animation_deck = FrameAnimationDeck(
        frame_directories(ROOT_DIR / settings.frames_directory),
        frame_duration=settings.frame_seconds,
        max_cached_animations=settings.max_cached_animations,
    )
    current_animation = animation_deck.next_animation()
    console.log(f"showing animation: {current_animation.path}")
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
                    current_animation = animation_deck.previous_animation()
                    console.log(f"showing animation: {current_animation.path}")
                if name == "Y":
                    blink_change_led(screen)
                    current_animation = animation_deck.next_animation()
                    console.log(f"showing animation: {current_animation.path}")
                if name == "A":
                    backlight = clamp(
                        backlight - settings.backlight_step,
                        settings.min_backlight,
                        settings.max_backlight,
                    )
                    screen.set_backlight(backlight)
                    console.log(f"backlight decreased to {backlight:.2f}")
                if name == "B":
                    backlight = clamp(
                        backlight + settings.backlight_step,
                        settings.min_backlight,
                        settings.max_backlight,
                    )
                    screen.set_backlight(backlight)
                    console.log(f"backlight increased to {backlight:.2f}")

            if proximity is not None and proximity.next_requested():
                blink_change_led(screen)
                current_animation = animation_deck.next_animation()
                console.log(f"showing animation: {current_animation.path}")

            screen.set_led(0, 0, 0)
            frame_started = time.monotonic()
            screen.show(current_animation.next_frame())
            elapsed = time.monotonic() - frame_started
            time.sleep(max(current_animation.frame_duration - elapsed, 0.0))
    finally:
        animation_deck.close()
        screen.close()


if __name__ == "__main__":
    main()
