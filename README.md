# FastestDet Person Detection Add-ons for Home Assistant

Ultra-fast, lightweight person detection add-ons for Home Assistant using the [FastestDetV2](https://github.com/Pairman/FastestDetV2) model. Perfect for edge devices like Orange Pi, Raspberry Pi, and other ARM-based systems.

## Overview

This repository provides two Home Assistant add-ons for real-time person detection via MQTT:

| Add-on | Runtime | Best For | Performance |
|--------|---------|----------|-------------|
| **FastestDet ONNX** | ONNX Runtime | Universal compatibility, easy setup | Good (50-150ms per frame) |
| **FastestDet NCNN** | NCNN (Tencent) | ARM devices, maximum performance | Excellent (20-50ms per frame) |

Both add-ons:
- ✅ Detect persons from any Home Assistant camera
- ✅ Create motion sensors via MQTT Discovery
- ✅ Provide annotated images (first/last detection frames)
- ✅ Monitor processing time and loop performance
- ✅ Work on ARM64 (aarch64) and x86_64 architectures
- ✅ Ultra-lightweight (~300MB Docker image)
- ✅ No GPU required - optimized for CPU inference

<details>
  <summary>Screenshots</summary>
  
  ![MQTT Device](/screenshots/screenshot_1.png)
  ![Settings](/screenshots/screenshot_2.png)
</details>

## Features

### Motion Detection
- Binary sensor with `motion` device class
- Debounced detection (configurable consecutive frames)
- Automatic MQTT Discovery - no YAML configuration needed

### Visual Feedback
- **Annotated First Detection**: Shows the first frame when motion is detected
- **Annotated Last Detection**: Shows the last frame before motion ends
- Bounding boxes with confidence scores

### Performance Monitoring
- **Processing Time**: AI inference + post-processing (ms)
- **Loop Time**: Total cycle time including network I/O (ms)
- Diagnostic entities hidden from main UI

### Smart Configuration
- Fixed-rate loop (consistent FPS)
- Configurable detection threshold
- Adjustable check interval
- Letterbox preprocessing (preserves aspect ratio)

## Installation

### Step 1: Add Repository

[![Install to Home Assistant](https://my.home-assistant.io/badges/supervisor_addon.svg)](https://my.home-assistant.io/redirect/supervisor_addon/?repository_url=https%3A%2F%2Fgithub.com%2FSplinterjke%2FFastestDet-HASS-Addon&addon=23bd8096_fastestdet_ncnn)

1. In Home Assistant, go to **Settings → Add-ons → Add-on Store**
2. Click the three dots (⋮) in the top right → **Repositories**
3. Add the repository URL: https://github.com/Splinterjke/FastestDet-HASS-Addon
4. Click **Add** → **Close**
5. Refresh the page (F5)

### Step 2: Install Add-on

You'll now see two new add-ons in the store:

- **FastestDet Person Detector (ONNX)** - Universal compatibility
- **FastestDet Person Detector (NCNN)** - ARM optimized

Choose based on your hardware:

| Device | Recommended Add-on |
|--------|-------------------|
| Orange Pi Zero 3, Raspberry Pi 4/5 | **NCNN** (2-3x faster) |
| x86_64 server, Intel NUC | **ONNX** (easier setup) |
| Any ARM device with limited RAM | **NCNN** (lower memory) |

### Step 3: Configure

1. Click on the add-on → **Configuration** tab
2. Fill in required fields:
   - **Home Assistant URL**: `http://homeassistant.local:8123` (or your HA IP)
   - **Long-Lived Access Token**: Generate in HA Profile → Security → Create Token
   - **Camera Entity**: Your camera entity ID (e.g., `camera.front_door`)
   - **MQTT Broker**: Your MQTT broker address (e.g., `core-mosquitto` or `homeassistant.local`)
   - **MQTT Port**: Usually `1883`
   - **MQTT Credentials**: Leave empty if not required
3. Click **Save**

### Step 4: Start Add-on

1. Go to **Info** tab
2. Click **Start**
3. Check logs for any errors

### Step 5: Verify in Home Assistant

After a few seconds, you'll see new entities:

- `binary_sensor.fastestdet_person_motion` - Motion sensor
- `sensor.fastestdet_person_processing_time` - AI inference time
- `sensor.fastestdet_person_loop_time` - Total loop time
- `camera.fastestdet_person_annotated_first` - First detection image
- `camera.fastestdet_person_annotated_last` - Last detection image

> [!NOTE]
> **Loop time is highly dependent on the latency of the camera API call.**
> 
> The endpoint `{HA_URL}/api/camera_proxy/{CAMERA_ENTITY}?width={width}&height={height}` can vary significantly based on:
> - Camera hardware and encoding
> - Network latency between HA and the camera
> - Snapshot resolution (larger = slower)
> 
> **Tips:**
> - Configure snapshot dimensions via `snapshot_width` and `snapshot_height` to reduce bandwidth
> - Decrease `check_interval` for more responsive detection (but higher CPU/network usage)
> - Frequent API calls (e.g., 0.5s interval) may actually have **lower per-call latency** than infrequent calls due to connection keep-alive and caching effects. Feel free to go below 1.0s interval to get higher FPS, but set higher `consecutive_detections_required` and `consecutive_non_detections_required` correspondigly. I personally use 0.5s interval and 2 frames for ON and 6 frames for OFF.

## Configuration Options

| Option | Description | Default | Example |
|--------|-------------|---------|---------|
| `log_level` | Logging verbosity | `info` | `debug`, `warning` |
| `ha_url` | Home Assistant URL | `http://homeassistant.local:8123` | `http://192.168.1.100:8123` |
| `ha_token` | Long-lived access token | *(required)* | `eyJ0eXAi...` |
| `camera_entity` | Camera to monitor | *(required)* | `camera.front_door` |
| `mqtt_broker` | MQTT broker address | `core-mosquitto` | `homeassistant.local` |
| `mqtt_port` | MQTT broker port | `1883` | `1883` |
| `mqtt_user` | MQTT username | *(empty)* | `mqtt_user` |
| `mqtt_pass` | MQTT password | *(empty)* | `mqtt_password` |
| `mqtt_base_topic` | Base MQTT topic | `fastestdet` | `person_detection` |
| `check_interval` | Loop interval (seconds) | `1.0` | `0.5` (2 FPS), `2.0` (0.5 FPS) |
| `detection_threshold` | Confidence threshold | `0.55` | `0.65` (stricter), `0.45` (more sensitive) |
| `consecutive_detections_required` | Frames needed to trigger ON | `2` | `3` (less sensitive), `1` (instant) |
| `consecutive_non_detections_required` | Frames needed to trigger OFF | `3` | `5` (longer presence), `1` (instant) |
| `snapshot_width` | Camera snapshot width (px) | `1280` | `1920` (higher quality), `352` (lower bandwidth) |
| `snapshot_height` | Camera snapshot height (px) | `720` | `1080` (higher quality), `197` (lower bandwidth) |

### Debouncing Parameters

The debouncing parameters help prevent false positives and flickering:

- **`consecutive_detections_required`**: The model must detect a person in this many consecutive frames before triggering the motion sensor ON. Increase this value for noisy cameras or environments with brief false detections.

- **`consecutive_non_detections_required`**: The model must NOT detect a person in this many consecutive frames before triggering the motion sensor OFF. Increase this value to keep the sensor ON longer when a person is present (to get delayed OFF state to catch more ending frames), even if they temporarily move out of frame.

## Configuration Changes

After changing the add-on configuration, you must **restart the add-on** for changes to take effect:

1. Go to **Settings → Add-ons → [Your Add-on]**
2. Click the **Info** tab
3. Click **Restart**

The add-on will reload all configuration values and restart the detection process.

## Performance Expectations

### Orange Pi Zero 3 (Allwinner H618, Cortex-A53)
- **NCNN**: 60-120ms processing time, ~64MB RAM
- **ONNX**: 90-180ms processing time, ~64MB RAM

*Note: Actual performance depends on camera resolution, network speed, and system load.*

## Troubleshooting

### Add-on won't start
- Check logs in the **Log** tab
- Verify MQTT broker is accessible
- Ensure camera entity exists in Home Assistant

### No motion detected
- Lower `detection_threshold` to `0.45`
- Check camera is actually streaming (view in HA)
- Verify `camera_entity` is correct (e.g., `camera.front_door` not `camera.front door`)

### High processing time
- Try NCNN add-on instead of ONNX
- Reduce camera resolution in HA camera settings
- Increase `check_interval` to reduce load

### MQTT Discovery not working
- Ensure MQTT integration is set up in Home Assistant
- Check MQTT broker logs for connection issues
- Verify `mqtt_base_topic` doesn't conflict with other devices

## Architecture
```
┌─────────────────┐
│  Home Assistant │
│   Camera Entity │
└────────┬────────┘
         │ HTTP API (snapshot)
         ↓
┌─────────────────┐
│  FastestDet     │
│  Add-on         │
│  - Fetch image  │
│  - Preprocess   │
│  - AI inference │
│  - Postprocess  │
└────────┬────────┘
         │ MQTT
         ↓
┌─────────────────┐
│  MQTT Broker    │
│  (Mosquitto)    │
└────────┬────────┘
         │ MQTT Discovery
         ↓
┌─────────────────┐
│  Home Assistant │
│  - Motion sensor│
│  - Cameras      │
│  - Diagnostics  │
└─────────────────┘
```

## Model Information

Both add-ons use **FastestDetV2** by [Pairman](https://github.com/Pairman/FastestDetV2):
- Ultra-lightweight: ~1MB model size
- Anchor-free detection
- Trained on COCO dataset (80 classes, but only "person" class is used)
- Input: 352×352 RGB image
- Output: Bounding boxes with confidence scores

## Credits

- **FastestDetV2**: [Pairman](https://github.com/Pairman/FastestDetV2) - Optimized fork
- **FastestDet Original**: [dog-qiuqiu](https://github.com/dog-qiuqiu/FastestDet) - Original architecture
- **NCNN**: [Tencent](https://github.com/Tencent/ncnn) - High-performance inference framework
- **ONNX Runtime**: [Microsoft](https://github.com/microsoft/onnxruntime) - Universal inference engine

## License

This project is provided as-is for personal and commercial use. The FastestDetV2 model is subject to its own license terms.

---

**Made with ❤️ for the Home Assistant community**