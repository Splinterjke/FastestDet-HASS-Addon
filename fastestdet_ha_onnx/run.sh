#!/usr/bin/env bash
set -e

CONFIG_PATH=/data/options.json

HA_URL=$(jq --raw-output ".ha_url" $CONFIG_PATH)
HA_TOKEN=$(jq --raw-output ".ha_token" $CONFIG_PATH)
CAMERA_ENTITY=$(jq --raw-output ".camera_entity" $CONFIG_PATH)
MQTT_BROKER=$(jq --raw-output ".mqtt_broker" $CONFIG_PATH)
MQTT_PORT=$(jq --raw-output ".mqtt_port" $CONFIG_PATH)
MQTT_USER=$(jq --raw-output ".mqtt_user" $CONFIG_PATH)
MQTT_PASS=$(jq --raw-output ".mqtt_pass" $CONFIG_PATH)
MQTT_BASE_TOPIC=$(jq --raw-output ".mqtt_base_topic" $CONFIG_PATH)
CHECK_INTERVAL=$(jq --raw-output ".check_interval" $CONFIG_PATH)
DETECTION_THRESHOLD=$(jq --raw-output ".detection_threshold" $CONFIG_PATH)
CONSECUTIVE_DETECTIONS_REQUIRED=$(jq --raw-output ".consecutive_detections_required" $CONFIG_PATH)
CONSECUTIVE_NON_DETECTIONS_REQUIRED=$(jq --raw-output ".consecutive_non_detections_required" $CONFIG_PATH)
LOG_LEVEL=$(jq --raw-output ".log_level" $CONFIG_PATH)

export HA_URL HA_TOKEN CAMERA_ENTITY
export MQTT_BROKER MQTT_PORT MQTT_USER MQTT_PASS MQTT_BASE_TOPIC
export CHECK_INTERVAL DETECTION_THRESHOLD CONSECUTIVE_DETECTIONS_REQUIRED CONSECUTIVE_NON_DETECTIONS_REQUIRED
export LOG_LEVEL

python3 /app/ha_person_detector.py