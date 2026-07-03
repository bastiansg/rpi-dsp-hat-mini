from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    width: int = 320
    height: int = 240
    button_debounce_seconds: float = 0.08
    frame_seconds: float = 1 / 30
    backlight_step: float = 0.1
    min_backlight: float = 0.1
    max_backlight: float = 1.0
    initial_backlight: float = 0.5
    proximity_enabled: bool = True
    proximity_threshold: int = 30
    proximity_baseline_samples: int = 20
    proximity_baseline_margin: int = 15
    proximity_cooldown_seconds: float = 1.0
    gif_change_blink_seconds: float = 0.15


settings = Settings()
