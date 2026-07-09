# FastestDet Person Detector (ONNX)

Home Assistant add-on for person detection using FastestDetV2 with ONNX Runtime.

## Overview

This add-on provides universal compatibility across all architectures (ARM, x86, x64) with easy setup and good performance. Ideal for users who want a straightforward installation without worrying about hardware-specific optimizations.

## Features

- ✅ **Universal Compatibility**: Works on ARM64, ARMv7, x86_64
- ✅ **Easy Setup**: Single package installation, no compilation needed
- ✅ **Good Performance**: 50-150ms per frame on ARM devices
- ✅ **Low Resource Usage**: ~150MB RAM footprint
- ✅ **MQTT Discovery**: Automatic entity creation in Home Assistant
- ✅ **Visual Feedback**: Annotated images with bounding boxes
- ✅ **Performance Monitoring**: Processing time and loop time sensors

## When to Choose ONNX

Choose this add-on if:
- You're running on x86_64 hardware (Intel NUC, server, etc.)
- You want the simplest possible setup
- You don't need maximum performance on ARM devices
- You prefer widely-supported, stable software

## When to Choose NCNN Instead

Consider the **NCNN version** if:
- You're on ARM hardware (Orange Pi, Raspberry Pi)
- You need maximum performance (2-3x faster)
- You have limited RAM (< 512MB)
- You want the absolute lowest latency

## Installation and configuration

See the [main repository README](https://github.com/Splinterjke/FastestDet-HASS-Addon/blob/master/README.md) for installation and configuration instructions.

## Performance Benchmarks

### Orange Pi Zero 3 (Cortex-A53 @ 1.5GHz)
- Processing time: 90-180ms
- Loop time: 400-1000ms (including network I/O)
- RAM usage: **64MB** 💾
- Effective FPS: 1-2 FPS

## Technical Details

### Model
- **Architecture**: FastestDetV2 (anchor-free)
- **Framework**: ONNX Runtime
- **Model Size**: ~1MB
- **Input**: 352×352 RGB image
- **Output**: Bounding boxes with confidence scores
- **Classes**: COCO (80 classes, person detection only)

### Preprocessing
- Letterbox resizing (preserves aspect ratio)
- Normalization to [0, 1]
- CHW format (Channel, Height, Width)

### Post-processing
- Custom decoding (tanh for center, sigmoid for size)
- Scoring formula: `(obj_score^0.6) * (cls_score^0.4)`
- Non-Maximum Suppression (NMS) with IoU threshold 0.45

### Docker Image
- **Base**: `python:3.10-slim`
- **Size**: ~300MB
- **Packages**: `onnxruntime`, `opencv-python-headless`, `numpy`, `requests`, `paho-mqtt`

## Troubleshooting

### Slow Performance
- ONNX Runtime may not be fully optimized for your ARM CPU
- Try the NCNN version for 2-3x speedup on ARM devices
- Reduce camera resolution in Home Assistant

### Import Errors
- Ensure you're using the correct architecture tag
- Rebuild the add-on: **Settings → Add-ons → [Add-on] → Rebuild**

### High Memory Usage
- Check if multiple instances are running
- Verify camera resolution isn't excessive
- Consider NCNN version for lower memory footprint

## Comparison with NCNN Version

| Feature | ONNX | NCNN |
|---------|------|------|
| ARM Performance | Good | Excellent (2-3x faster) |
| x86 Performance | Excellent | Good |
| Setup Complexity | Easy | Easy |
| Memory Usage | ~150MB | ~100MB |
| Compatibility | Universal | ARM optimized |
| Maintenance | Low | Low |

---

**Part of the [FastestDet Person Detection Add-ons](../README.md) collection**