# fastestdet_ha/ha_person_detector.py
import os
import cv2
import numpy as np
import onnxruntime as ort
import requests
import paho.mqtt.client as mqtt
import time
import logging
import json
import base64

log_level = os.getenv("LOG_LEVEL", "info").upper()
logging.basicConfig(level=getattr(logging, log_level, logging.INFO))

# --- Configuration from Environment Variables ---
HA_URL = os.getenv("HA_URL", "http://homeassistant.local:8123")
HA_TOKEN = os.getenv("HA_TOKEN", "YOUR_LONG_LIVED_ACCESS_TOKEN")
CAMERA_ENTITY = os.getenv("CAMERA_ENTITY", "camera.your_camera_entity_id")

MQTT_BROKER = os.getenv("MQTT_BROKER", "core-mosquitto")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_USER = os.getenv("MQTT_USER", "")
MQTT_PASS = os.getenv("MQTT_PASS", "")
# Base topic for all entities
MQTT_BASE_TOPIC = os.getenv("MQTT_BASE_TOPIC", "fastestdet")

MODEL_PATH = os.getenv("MODEL_PATH", "/models/FastestDetV2.onnx")
CHECK_INTERVAL = float(os.getenv("CHECK_INTERVAL", 1.0)) # Seconds between checks
DETECTION_THRESHOLD = float(os.getenv("DETECTION_THRESHOLD", 0.55))
CONSECUTIVE_DETECTIONS_REQUIRED = int(os.getenv("CONSECUTIVE_DETECTIONS_REQUIRED", 2))
CONSECUTIVE_NON_DETECTIONS_REQUIRED = int(os.getenv("CONSECUTIVE_NON_DETECTIONS_REQUIRED", 3))

# Snapshot dimensions
SNAPSHOT_WIDTH = int(os.getenv("SNAPSHOT_WIDTH", 1280))
SNAPSHOT_HEIGHT = int(os.getenv("SNAPSHOT_HEIGHT", 720))

# Specific topics for the entities
TOPIC_MOTION = f"{MQTT_BASE_TOPIC}/binary_sensor/motion/person"
TOPIC_PROCESSING_TIME = f"{MQTT_BASE_TOPIC}/sensor/processing_time"
TOPIC_LOOP_TIME = f"{MQTT_BASE_TOPIC}/sensor/loop_time"
TOPIC_IMAGE_FIRST = f"{MQTT_BASE_TOPIC}/camera/annotated_first"   # First frame of detection
TOPIC_IMAGE_LAST = f"{MQTT_BASE_TOPIC}/camera/annotated_last"     # Last frame of detection

# --- FastestDet Post-Processing Functions ---
def sigmoid(x): return 1. / (1. + np.exp(-x))
def tanh(x): return 2. / (1. + np.exp(-2. * x)) - 1.

def letterbox_image(img, target_shape=(352, 352)):
    h, w = img.shape[:2]
    target_w, target_h = target_shape
    r = min(target_w / w, target_h / h)
    new_unpad = int(round(w * r)), int(round(h * r))
    img_resized = cv2.resize(img, new_unpad, interpolation=cv2.INTER_LINEAR)
    dw, dh = target_w - new_unpad[0], target_h - new_unpad[1]
    left, right = dw // 2, dw - (dw // 2)
    top, bottom = dh // 2, dh - (dh // 2)
    img_padded = cv2.copyMakeBorder(img_resized, top, bottom, left, right, 
                                    cv2.BORDER_CONSTANT, value=(114, 114, 114))
    return img_padded, r, left, top

def preprocess(src_img, size):
    target_w, target_h = size[0], size[1]
    img_padded, r, left_pad, top_pad = letterbox_image(src_img, (target_w, target_h))
    output = img_padded.transpose(2, 0, 1)
    output = output.reshape((1, 3, target_h, target_w)) / 255.0
    return output.astype('float32'), r, left_pad, top_pad
def nms(dets, thresh=0.45):
    if len(dets) == 0: return []
    x1, y1, x2, y2, scores = dets[:, 0], dets[:, 1], dets[:, 2], dets[:, 3], dets[:, 4]
    areas = (x2 - x1 + 1) * (y2 - y1 + 1)
    order = scores.argsort()[::-1]
    keep = []
    while order.size > 0:
        i = order[0]
        keep.append(i)
        xx1 = np.maximum(x1[i], x1[order[1:]])
        yy1 = np.maximum(y1[i], y1[order[1:]])
        xx2 = np.minimum(x2[i], x2[order[1:]])
        yy2 = np.minimum(y2[i], y2[order[1:]])
        w = np.maximum(0.0, xx2 - xx1 + 1)
        h = np.maximum(0.0, yy2 - yy1 + 1)
        inter = w * h
        ovr = inter / (areas[i] + areas[order[1:]] - inter)
        inds = np.where(ovr <= thresh)[0]
        order = order[inds + 1]
    return dets[keep]

def detection(session, img, input_width, input_height, thresh):
    # Start timing the entire detection process
    start_time = time.perf_counter()
    
    pred = []
    H, W, _ = img.shape
    data, r, left_pad, top_pad = preprocess(img, [input_width, input_height])
    input_name = session.get_inputs()[0].name
    
    feature_map = session.run([], {input_name: data})[0][0]
    feature_map = feature_map.transpose(1, 2, 0)
    feature_map_height, feature_map_width = feature_map.shape[0], feature_map.shape[1]

    for h_idx in range(feature_map_height):
        for w_idx in range(feature_map_width):
            data = feature_map[h_idx][w_idx]
            obj_score, cls_score = data[0], data[5:].max()
            score = (obj_score ** 0.6) * (cls_score ** 0.4)
            
            if score > thresh:
                cls_index = np.argmax(data[5:])
                x_offset, y_offset = tanh(data[1]), tanh(data[2])
                box_width, box_height = sigmoid(data[3]), sigmoid(data[4])
                
                box_cx = (w_idx + x_offset) / feature_map_width * input_width
                box_cy = (h_idx + y_offset) / feature_map_height * input_height
                bw = box_width * input_width
                bh = box_height * input_height
                
                x1 = box_cx - 0.5 * bw
                y1 = box_cy - 0.5 * bh
                x2 = box_cx + 0.5 * bw
                y2 = box_cy + 0.5 * bh
                
                # Map back to original image coordinates
                x1 -= left_pad
                y1 -= top_pad
                x2 -= left_pad
                y2 -= top_pad
                
                x1 /= r
                y1 /= r
                x2 /= r
                y2 /= r
                
                x1 = max(0, min(x1, W))
                y1 = max(0, min(y1, H))
                x2 = max(0, min(x2, W))
                y2 = max(0, min(y2, H))
                
                pred.append([int(x1), int(y1), int(x2), int(y2), score, cls_index])
    
    # Calculate total processing time in milliseconds
    processing_time_ms = (time.perf_counter() - start_time) * 1000
    
    if not pred: return [], processing_time_ms
    return nms(np.array(pred)), processing_time_ms

# --- Main Logic ---
def get_ha_snapshot():
    url = f"{HA_URL}/api/camera_proxy/{CAMERA_ENTITY}?width={SNAPSHOT_WIDTH}&height={SNAPSHOT_HEIGHT}" # query params are optional
    headers = {"Authorization": f"Bearer {HA_TOKEN}"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200: return response.content
        logging.error(f"HA Snapshot failed: {response.status_code}")
        return None
    except Exception as e:
        logging.error(f"Error fetching snapshot: {e}")
        return None

def annotate_image(img, detections):
    """Helper function to annotate image with bounding boxes"""
    img_annotated = img.copy()
    for det in detections:
        if det[5] == 0:  # Only draw boxes for 'person' class
            x1, y1, x2, y2, score = int(det[0]), int(det[1]), int(det[2]), int(det[3]), det[4]
            cv2.rectangle(img_annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(img_annotated, f"Person {score:.2f}", (x1, y1 - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    return img_annotated

def publish_image(mqtt_client, topic, img):
    """Helper function to encode and publish image to MQTT"""
    _, buffer = cv2.imencode('.jpg', img)
    img_b64 = base64.b64encode(buffer).decode('utf-8')
    mqtt_client.publish(topic, img_b64)

def setup_mqtt_discovery(client):
    # Use the modern HA device discovery format with 'cmps' (components)
    discovery_topic = "homeassistant/device/fastestdet_person/config"
    config_payload = {
        "device": {
            "name": "FastestDet Person Detector",
            "identifiers": ["fastestdet_person_detector_001"],
            "manufacturer": "dog-qiuqiu",
            "model": "FastestDet ONNX",
            "sw_version": "1.0.0"
        },
        "origin": {
            "name": "fastestdet_ha service",
            "support_url": "https://github.com/dog-qiuqiu/FastestDet"
        },
        "cmps": {
            "motion_person": {
                "p": "binary_sensor",
                "name": "Person Motion",
                "unique_id": "fastestdet_person_motion_001",
                "stat_t": TOPIC_MOTION,
                "payload_on": "ON",
                "payload_off": "OFF",
                "device_class": "motion",
                "icon": "mdi:motion-sensor"
            },
            "processing_time": {
                "p": "sensor",
                "name": "Processing Time",
                "unique_id": "fastestdet_person_processingtime_001",
                "stat_t": TOPIC_PROCESSING_TIME,
                "unit_of_measurement": "ms",
                "icon": "mdi:timer-outline",
                "entity_category": "diagnostic"
            },
            "loop_time": {
                "p": "sensor",
                "name": "Loop Time",
                "unique_id": "fastestdet_person_looptime_001",
                "stat_t": TOPIC_LOOP_TIME,
                "unit_of_measurement": "ms",
                "icon": "mdi:timer-sync-outline",
                "entity_category": "diagnostic"
            },
            "annotated_image_first": {
                "p": "camera",
                "name": "Annotated First Detection",
                "unique_id": "fastestdet_person_annotatedfirst_001",
                "t": TOPIC_IMAGE_FIRST,
                "image_encoding": "b64"
            },
            "annotated_image_last": {
                "p": "camera",
                "name": "Annotated Last Detection",
                "unique_id": "fastestdet_person_annotatedlast_001",
                "t": TOPIC_IMAGE_LAST,
                "image_encoding": "b64"
            }
        }
    }
    client.publish(discovery_topic, json.dumps(config_payload), retain=True)

def main():
    logging.info("Loading FastestDet ONNX model...")
    session = ort.InferenceSession(MODEL_PATH)
    
    logging.info("Connecting to MQTT broker...")
    mqtt_client = mqtt.Client()
    if MQTT_USER: mqtt_client.username_pw_set(MQTT_USER, MQTT_PASS)
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    setup_mqtt_discovery(mqtt_client)
    
    last_state = None
    consecutive_detections = 0
    consecutive_non_detections = 0
    last_annotated_image = None  # Store the most recent annotated image
    
    logging.info(f"Starting detection loop (interval={CHECK_INTERVAL}s, threshold={DETECTION_THRESHOLD})...")
    logging.info(f"Debouncing: {CONSECUTIVE_DETECTIONS_REQUIRED} detections ON, {CONSECUTIVE_NON_DETECTIONS_REQUIRED} detections OFF")
    
    while True:
        loop_start_time = time.perf_counter()
        
        img_bytes = get_ha_snapshot()
        if img_bytes:
            nparr = np.frombuffer(img_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is not None:
                detections, processing_time_ms = detection(session, img, 352, 352, DETECTION_THRESHOLD)
                mqtt_client.publish(TOPIC_PROCESSING_TIME, f"{processing_time_ms:.1f}")
                
                person_detected = any(det[5] == 0 for det in detections)
                
                # If person is detected, annotate and store the image
                if person_detected:
                    img_annotated = annotate_image(img, detections)
                    last_annotated_image = img_annotated  # Keep updating with latest detection
                
                if person_detected:
                    consecutive_detections += 1
                    consecutive_non_detections = 0
                    
                    if consecutive_detections >= CONSECUTIVE_DETECTIONS_REQUIRED and last_state != "ON":
                        logging.info(f"Person confirmed detected ({consecutive_detections} consecutive) -> Publishing ON")
                        mqtt_client.publish(TOPIC_MOTION, "ON", retain=True)
                        last_state = "ON"
                        
                        # Publish first detection image
                        if last_annotated_image is not None:
                            publish_image(mqtt_client, TOPIC_IMAGE_FIRST, last_annotated_image)
                            logging.info("Published first detection image")
                else:
                    consecutive_non_detections += 1
                    consecutive_detections = 0
                    
                    if consecutive_non_detections >= CONSECUTIVE_NON_DETECTIONS_REQUIRED and last_state != "OFF":
                        logging.info(f"Person confirmed absent ({consecutive_non_detections} consecutive) -> Publishing OFF")
                        mqtt_client.publish(TOPIC_MOTION, "OFF", retain=True)
                        last_state = "OFF"
                        
                        # Publish last detection image (the last frame where person was seen)
                        if last_annotated_image is not None:
                            publish_image(mqtt_client, TOPIC_IMAGE_LAST, last_annotated_image)
                            logging.info("Published last detection image")
                        
                        # Clear the stored image
                        last_annotated_image = None
                        
        loop_time_ms = (time.perf_counter() - loop_start_time) * 1000
        mqtt_client.publish(TOPIC_LOOP_TIME, f"{loop_time_ms:.1f}")
        
        time.sleep(max(0, CHECK_INTERVAL - loop_time_ms / 1000))

if __name__ == "__main__":
    main()