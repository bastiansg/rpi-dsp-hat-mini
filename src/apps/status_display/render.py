import math

from PIL import Image, ImageDraw, ImageFont

COLOR_MODES = (
    ("RED", (0.85, 0.05, 0.02), (245, 74, 65)),
    ("GREEN", (0.0, 0.65, 0.12), (95, 225, 125)),
    ("BLUE", (0.0, 0.15, 0.9), (105, 160, 255)),
    ("WHITE", (0.75, 0.75, 0.75), (235, 235, 225)),
)


class StatusRenderer:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.font = ImageFont.load_default()

    def frame(
        self,
        mode_name: str,
        accent: tuple[int, int, int],
        backlight: float,
        last_button: str,
        tick: int,
    ) -> Image.Image:
        image = Image.new("RGB", (self.width, self.height), (9, 11, 14))
        draw = ImageDraw.Draw(image)

        self._draw_background(draw, accent, tick)
        draw.rounded_rectangle((14, 14, 306, 226), radius=8, fill=(13, 16, 21))
        draw.text((28, 30), "DISPLAY HAT MINI", fill=(220, 226, 235), font=self.font)
        draw.text((28, 56), "320 x 240 SPI LCD", fill=(160, 174, 190), font=self.font)
        self._draw_meter(draw, "LIGHT", backlight, 28, 100, accent)
        self._draw_value(draw, "LED", mode_name, 28, 148, accent)
        self._draw_value(draw, "BUTTON", last_button, 28, 184, (220, 226, 235))

        return image

    def _draw_background(
        self, draw: ImageDraw.ImageDraw, accent: tuple[int, int, int], tick: int
    ) -> None:
        for x in range(0, self.width, 8):
            phase = (x / self.width * math.tau) + tick * 0.08
            color = (
                int(18 + accent[0] * 0.28 + 18 * math.sin(phase)),
                int(18 + accent[1] * 0.28 + 18 * math.sin(phase + 2.0)),
                int(18 + accent[2] * 0.28 + 18 * math.sin(phase + 4.0)),
            )
            draw.rectangle((x, 0, x + 7, self.height), fill=color)

    def _draw_meter(
        self,
        draw: ImageDraw.ImageDraw,
        label: str,
        value: float,
        x: int,
        y: int,
        color: tuple[int, int, int],
    ) -> None:
        draw.text((x, y), label, fill=(220, 226, 235), font=self.font)
        bar_x = x + 54
        bar_y = y - 2
        bar_width = 204
        draw.rectangle(
            (bar_x, bar_y, bar_x + bar_width, bar_y + 14),
            outline=(64, 74, 86),
        )
        width = int(bar_width * min(max(value, 0.0), 1.0))
        draw.rectangle(
            (bar_x + 2, bar_y + 2, bar_x + width, bar_y + 12),
            fill=color,
        )
        draw.text(
            (bar_x + bar_width - 34, y),
            f"{value * 100:3.0f}%",
            fill=(220, 226, 235),
            font=self.font,
        )

    def _draw_value(
        self,
        draw: ImageDraw.ImageDraw,
        label: str,
        value: str,
        x: int,
        y: int,
        color: tuple[int, int, int],
    ) -> None:
        draw.text((x, y), label, fill=(220, 226, 235), font=self.font)
        draw.text((x + 54, y), value, fill=color, font=self.font)
