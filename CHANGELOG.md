# Changelog

## [1.0.1] - 2026-07-09

### Added
- **Configurable debouncing parameters** via add-on settings:
  - `consecutive_detections_required` — Number of consecutive frames with a person detected before triggering motion ON (default: 2)
  - `consecutive_non_detections_required` — Number of consecutive frames without a person before triggering motion OFF (default: 3)
- Allows fine-tuning motion sensor sensitivity without modifying the source code
- Useful for noisy cameras (increase values) or fast-response needs (decrease values)

### Changed
- Bumped add-on version to 1.0.1 in both `fastestdet_ncnn` and `fastestdet_onnx`
- Updated translations for the new configuration options

### Technical Details
- Debouncing values are now read from environment variables set by `run.sh`
- Backward compatible: existing installations keep the previous default behavior (2 ON / 3 OFF)

## [1.0.0] - 2026-07-09

### Added
- **Initial release** with two separate add-ons:
  - `fastestdet_onnx` - Universal compatibility using ONNX Runtime
  - `fastestdet_ncnn` - ARM-optimized using NCNN (Tencent)
- **Person motion detection** via Home Assistant camera snapshots
- **MQTT Discovery** for automatic entity creation (no YAML needed)
- **Debounced motion sensor** with configurable consecutive frame requirements
- **Annotated camera entities**:
  - First detection frame (when motion starts)
  - Last detection frame (when motion ends)
- **Diagnostic sensors**:
  - Processing time (AI inference + post-processing)
  - Loop time (total cycle including network I/O)
- **Letterbox preprocessing** to preserve 16:9 aspect ratio
- **Fixed-rate loop** for consistent update frequency
- **Configurable parameters**:
  - Detection threshold (0.0 - 1.0)
  - Check interval (seconds, supports decimals for sub-second polling)
  - Consecutive detections required (ON trigger)
  - Consecutive non-detections required (OFF trigger)
  - MQTT broker settings and base topic
  - Log level (trace, debug, info, notice, warning, error, fatal)
- **Multi-architecture support**: aarch64, armv7, armhf, amd64
- **Pre-compiled model files** bundled in the add-on (no runtime downloads)
- **Compatibility with Home Assistant Supervisor 2026.04.0+**

### Technical Details
- Uses [FastestDetV2](https://github.com/Pairman/FastestDetV2) model (~1MB)
- Anchor-free detection with custom scoring: `(obj^0.6) * (cls^0.4)`
- NMS with IoU threshold 0.45
- Input resolution: 352×352 (optimized for edge devices)
- COCO-trained, detects "person" class (class 0) only
- Docker base: `python:3.10-slim` (glibc for wheel compatibility)

## Version History Summary

| Version | Date       | Highlights                                                     |
|---------|------------|----------------------------------------------------------------|
| 1.0.1   | 2026-07-09 | Configurable debouncing parameters (consecutive detections)    |
| 1.0.0   | 2026-07-09 | Initial release with ONNX and NCNN variants                    |