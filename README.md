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
- `X`: previous animation.
- `Y`: next animation.
- LTR-559 proximity sensor: next animation when an object is detected close to the sensor.

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

The app shuffles the PNG frame directories from `frames/` and lets the hardware buttons move through the playlist. A background thread keeps a bounded queue of decoded frames ready so image loading does not interrupt rendering. The queue holds 20 frames by default and can be changed with `FRAME_BUFFER_SIZE`.

The Multi-Sensor Stick proximity trigger uses the onboard LTR-559 sensor. At startup, the app samples the sensor's ambient baseline and triggers after two consecutive readings rise above that baseline plus a margin, with a one second cooldown. The threshold, baseline, timing, confirmation count, and LED measurement parameters can all be changed with environment variables:

```bash
PROXIMITY_THRESHOLD=50 PROXIMITY_BASELINE_MARGIN=20 PROXIMITY_COOLDOWN_SECONDS=0.75 make app
```

The additional proximity settings are `PROXIMITY_ENABLED`, `PROXIMITY_BASELINE_SAMPLES`, `PROXIMITY_MEASUREMENT_MILLISECONDS`, `PROXIMITY_CONFIRMATION_SAMPLES`, `PROXIMITY_LED_CURRENT_MILLIAMPS`, `PROXIMITY_LED_DUTY_CYCLE`, `PROXIMITY_LED_PULSE_FREQUENCY_KILOHERTZ`, and `PROXIMITY_LED_PULSES`.

Whenever the animation changes from a button press or proximity trigger, the onboard LED blinks red. The blink duration can be changed with `GIF_CHANGE_BLINK_SECONDS`.

## PM2 Setup

Install PM2 globally:

```bash
npm install pm2 -g
```

Add the PM2 startup script so the application starts on boot:

```bash
pm2 startup
```

The app is configured in `ecosystem.config.js`. Start and persist it with:

```bash
make start
```

## Checks

```bash
make format
make check
```
