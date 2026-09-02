import time
from collections.abc import Iterable

from displayhatmini import DisplayHATMini
from PIL import Image

BUTTONS = {
    "A": DisplayHATMini.BUTTON_A,
    "B": DisplayHATMini.BUTTON_B,
    "X": DisplayHATMini.BUTTON_X,
    "Y": DisplayHATMini.BUTTON_Y,
}


class DisplayHatMiniScreen:
    def __init__(
        self,
        width: int,
        height: int,
        backlight: float,
        spi_speed_hz: int,
    ):
        self.buffer = Image.new("RGB", (width, height), (0, 0, 0))
        self.display = DisplayHATMini(self.buffer, backlight_pwm=True)
        self.display.st7789._spi.max_speed_hz = spi_speed_hz
        self.set_backlight(backlight)

    def show(self, image: Image.Image) -> None:
        self.buffer.paste(image, ((self.buffer.width - image.width) // 2, 0))
        self.display.display()

    def set_led(self, red: float, green: float, blue: float) -> None:
        self.display.set_led(red, green, blue)

    def set_backlight(self, value: float) -> None:
        self.display.set_backlight(value)

    def read_button(self, pin: int) -> bool:
        return self.display.read_button(pin)

    def close(self) -> None:
        self.set_led(0, 0, 0)
        self.show(Image.new("RGB", self.buffer.size, (0, 0, 0)))


class ButtonPressReader:
    def __init__(
        self,
        screen: DisplayHatMiniScreen,
        buttons: dict[str, int] | None = None,
        debounce_seconds: float = 0.2,
    ):
        self.screen = screen
        self.buttons = buttons or BUTTONS
        self.debounce_seconds = debounce_seconds
        self.previous: dict[str, bool] = {}
        self.last_pressed = {name: 0.0 for name in self.buttons}

    def setup(self) -> None:
        time.sleep(0.05)
        self.previous = {
            name: self.screen.read_button(pin) for name, pin in self.buttons.items()
        }

    def pressed(self) -> Iterable[str]:
        now = time.monotonic()
        pressed = []

        for name, pin in self.buttons.items():
            current = self.screen.read_button(pin)
            if (
                not self.previous[name]
                and current
                and now - self.last_pressed[name] >= self.debounce_seconds
            ):
                pressed.append(name)
                self.last_pressed[name] = now

            self.previous[name] = current

        return pressed
