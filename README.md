# Raspberry Pi Display HAT Mini

Small Python project for a Raspberry Pi with a Pimoroni Display HAT Mini.

This project follows the same lightweight Python app structure as the nearby Raspberry Pi project, but targets only Display HAT Mini hardware:

- 320x240 SPI ST7789 display through Pimoroni's `displayhatmini` Python package.
- Four Display HAT Mini buttons.
- Onboard RGB LED.
- PWM backlight control.

Button behavior:

- `A`: decrease display backlight.
- `B`: increase display backlight.
- `X`: previous GIF.
- `Y`: next GIF.
- LTR-559 proximity sensor: next GIF when an object is detected close to the sensor.

## Hardware Setup

Enable SPI for the display and I2C for the Qw/ST sensor on the Raspberry Pi:

```bash
sudo raspi-config nonint do_spi 0
sudo raspi-config nonint do_i2c 0
sudo reboot
```

Display HAT Mini official references:

- Python library: https://github.com/pimoroni/displayhatmini-python
- Product documentation: https://shop.pimoroni.com/products/display-hat-mini
- Pinout: https://pinout.xyz/pinout/display_hat_mini

## Project Setup

```bash
make uv-setup
```

## Run

```bash
make app
```

The app shuffles all GIFs from `gif/`, plays them as animations, and lets the hardware buttons move through the playlist.

The Multi-Sensor Stick proximity trigger uses the onboard LTR-559 sensor. At startup, the app samples the sensor's ambient baseline and triggers when proximity rises above that baseline plus a margin, with a one second cooldown. These can be changed with environment variables:

```bash
PROXIMITY_THRESHOLD=50 PROXIMITY_BASELINE_MARGIN=20 PROXIMITY_COOLDOWN_SECONDS=0.75 make app
```

Whenever the GIF changes from a button press or proximity trigger, the onboard LED blinks red. The blink duration can be changed with `GIF_CHANGE_BLINK_SECONDS`.

## Checks

```bash
make format
make check
```
