from pydantic import (
    Field,
    NonNegativeFloat,
    NonNegativeInt,
    PositiveFloat,
    PositiveInt,
    StrictBool,
    StrictStr,
)
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    width: PositiveInt = Field(
        default=320,
        le=320,
        description="Display width in pixels",
    )

    height: PositiveInt = Field(
        default=240,
        le=240,
        description="Display height in pixels",
    )
    spi_speed_hz: PositiveInt = Field(
        default=80 * 1000 * 1000,
        description="Display SPI clock speed in hertz",
    )

    button_debounce_seconds: NonNegativeFloat = Field(
        default=0.08,
        description="Minimum interval between button presses in seconds",
    )

    frame_seconds: PositiveFloat = Field(
        default=1 / 30,
        description="Target duration of each animation frame in seconds",
    )

    frames_directory: StrictStr = Field(
        default="frames",
        min_length=1,
        description="Directory containing animation frame directories",
    )

    max_cached_animations: PositiveInt = Field(
        default=1,
        description="Maximum number of animations retained in memory",
    )

    backlight_step: PositiveFloat = Field(
        default=0.1,
        le=1.0,
        description="Backlight adjustment applied per button press",
    )

    min_backlight: NonNegativeFloat = Field(
        default=0.1,
        le=1.0,
        description="Minimum backlight intensity",
    )

    max_backlight: PositiveFloat = Field(
        default=1.0,
        le=1.0,
        description="Maximum backlight intensity",
    )

    initial_backlight: NonNegativeFloat = Field(
        default=1.0,
        le=1.0,
        description="Backlight intensity applied at startup",
    )

    proximity_enabled: StrictBool = Field(
        default=True,
        description="Whether proximity-triggered animation changes are enabled",
    )

    proximity_threshold: NonNegativeInt = Field(
        default=30,
        le=2047,
        description="Minimum absolute proximity reading required to trigger",
    )

    proximity_baseline_samples: PositiveInt = Field(
        default=20,
        description="Number of startup samples used to establish the baseline",
    )

    proximity_baseline_margin: NonNegativeInt = Field(
        default=15,
        le=2047,
        description="Required proximity increase above the measured baseline",
    )

    proximity_cooldown_seconds: NonNegativeFloat = Field(
        default=1.0,
        description="Minimum interval between proximity triggers in seconds",
    )

    gif_change_blink_seconds: NonNegativeFloat = Field(
        default=0.15,
        description="Duration of the animation-change LED blink in seconds",
    )

settings = Settings()
