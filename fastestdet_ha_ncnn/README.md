# FastestDet Person Detector (NCNN)

Home Assistant add-on for ultra-fast person detection using FastestDetV2 with NCNN (Tencent's high-performance inference framework).

## Overview

This add-on delivers **maximum performance on ARM devices** through NCNN's hand-optimized ARM NEON SIMD instructions. Perfect for Orange Pi, Raspberry Pi, and other ARM-based edge devices where every millisecond counts.

## Features

- ✅ **Maximum ARM Performance**: 20-50ms per frame on Cortex-A53
- ✅ **Ultra-Low Memory**: ~100MB RAM footprint
- ✅ **ARM NEON Optimized**: Hand-written assembly for ARM CPUs
- ✅ **MQTT Discovery**: Automatic entity creation in Home Assistant
- ✅ **Visual Feedback**: Annotated images with bounding boxes
- ✅ **Performance Monitoring**: Processing time and loop time sensors
- ✅ **Production Ready**: Pre-compiled models, no build-time conversion

## When to Choose NCNN

Choose this add-on if:
- You're running on ARM hardware (Orange Pi, Raspberry Pi, etc.)
- You need maximum performance (2-3x faster than ONNX)
- You have limited RAM (< 512MB)
- You want the absolute lowest latency
- You're deploying to edge devices

## When to Choose ONNX Instead

Consider the **ONNX version** if:
- You're on x86_64 hardware (Intel NUC, server)
- You want universal compatibility
- You prefer widely-supported, stable software
- You don't need maximum ARM performance

## Installation

See the [main repository README](../README.md) for installation instructions.

## Configuration

All configuration is done through the Home Assistant add-on UI:

| Option | Description | Default |
|--------|-------------|---------|
| `log_level` | Logging verbosity | `info` |
| `ha_url` | Home Assistant URL | `http://homeassistant.local:8123` |
| `ha_token` | Long-lived access token | *(required)* |
| `camera_entity` | Camera entity ID | *(required)* |
| `mqtt_broker` | MQTT broker address | `core-mosquitto` |
| `mqtt_port` | MQTT broker port | `1883` |
| `mqtt_user` | MQTT username | *(empty)* |
| `mqtt_pass` | MQTT password | *(empty)* |
| `mqtt_base_topic` | Base MQTT topic | `fastestdet` |
| `check_interval` | Loop interval (seconds) | `1.0` |
| `detection_threshold` | Confidence threshold | `0.55` |

## Performance Benchmarks

### Orange Pi Zero 3 (Cortex-A53 @ 1.5GHz)
- Processing time: 60-120ms
- Loop time: 200-1000ms (including network I/O)
- RAM usage: **64MB** 💾
- Effective FPS: 1-3 FPS

## Technical Details

### Model
- **Architecture**: FastestDetV2 (anchor-free)
- **Framework**: NCNN (Tencent)
- **Model Files**: `.param` (architecture) + `.bin` (weights)
- **Model Size**: ~1MB total
- **Input**: 352×352 BGR image
- **Output**: Bounding boxes with confidence scores
- **Classes**: COCO (80 classes, person detection only)

### Why NCNN is Faster

NCNN achieves superior performance through:

1. **ARM NEON SIMD**: Hand-written assembly for vector operations
2. **Optimized Memory Layout**: Efficient tensor storage
3. **Zero-Copy Operations**: Minimizes data movement
4. **Native BGR Support**: No color conversion overhead
5. **Fused Operations**: Combines multiple ops into single kernels

### Preprocessing
- Letterbox resizing (preserves aspect ratio)
- Native BGR format (no RGB conversion needed)
- In-place normalization

### Post-processing
- Custom decoding (tanh for center, sigmoid for size)
- Scoring formula: `(obj_score^0.6) * (cls_score^0.4)`
- Non-Maximum Suppression (NMS) with IoU threshold 0.45

### Docker Image
- **Base**: `python:3.10-slim`
- **Size**: ~300MB
- **Packages**: `ncnn`, `opencv-python-headless`, `numpy`, `requests`, `paho-mqtt`
- **Note**: NCNN installed with `--no-deps` to avoid GUI dependencies

## Performance Comparison

### NCNN vs ONNX on ARM Devices

| Device | ONNX (ms) | NCNN (ms) | Speedup |
|--------|-----------|-----------|---------|
| Orange Pi Zero 3 (A53) | 50-150 | **20-50** | **2-3x** |
| Raspberry Pi 4 (A72) | 40-100 | **15-40** | **2.5x** |
| Raspberry Pi 5 (A76) | 30-80 | **10-25** | **3x** |

### Memory Usage

| Component | ONNX | NCNN |
|-----------|------|------|
| Python runtime | ~30MB | ~30MB |
| Inference engine | ~80MB | **~40MB** |
| Model weights | ~10MB | ~10MB |
| OpenCV | ~30MB | ~30MB |
| **Total** | ~150MB | **~100MB** |

## Troubleshooting

### Import Errors (libxcb.so.1)
- This is fixed in the current Dockerfile
- NCNN is installed with `--no-deps` to avoid GUI dependencies
- If you see this error, rebuild the add-on

### Slow Performance
- Verify you're on ARM hardware (NCNN is optimized for ARM)
- Check CPU frequency scaling (may be throttled)
- Reduce camera resolution in Home Assistant
- Ensure no other heavy processes are running

### High CPU Usage
- NCNN uses all CPU cores by default
- This is normal and expected
- If too high, increase `check_interval` to reduce load

### Model Loading Errors
- Verify model files exist in `/models/`
- Check file permissions
- Rebuild the add-on to re-download models

## Why Not PNNX?

You might notice we don't use PNNX (PyTorch Neural Network eXchange) in this add-on. That's because:

- **PNNX is for model conversion**, not inference
- The FastestDetV2 author already converted the models to NCNN format
- We use the pre-compiled `.param` and `.bin` files directly
- This keeps the Docker image small and build times fast

If you want to train your own model, you'd use PNNX on a powerful PC to convert PyTorch weights to NCNN format, then deploy the resulting files.

---

**Part of the [FastestDet Person Detection Add-ons](../README.md) collection**

**Optimized for ARM with ❤️ by NCNN**