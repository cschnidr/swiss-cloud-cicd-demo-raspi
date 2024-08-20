import os
import sys
import logging

if sys.argv and len(sys.argv) > 1 and sys.argv[1] == "--mock":
    from src.mock.board import board as board  # use for non-Raspi testing
else:
    import board as board # use on Raspi

import src.utils.types as types
import json

LOG_LEVEL = logging.INFO
DIR_PATH = os.path.dirname(os.path.abspath(__file__))
CERTIFICATES_PATH = os.path.join(DIR_PATH, "certificates")

# Pixel settings
COMPONENT_PIXELS = {
    'repo': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
    'build': [12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23],
    'qa': [24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35],
    'transitionRegion1': [36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47],
    'region1': [36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47],
    'transitionRegion2': [48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59],
    'region2': [48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59]
}

# Ports for the buttons
BUTTON_PORTS = {
    str(types.Buttons.DEPLOY_GREEN): 23,
    str(types.Buttons.DEPLOY_RED): 16,
    str(types.Buttons.ENABLE_DISABLE_REGION1): 24,
    str(types.Buttons.ENABLE_DISABLE_REGION2): 25
}

# Port for Neopixel LED stripe
NEOPIXEL_PORT = board.D18
# Number of LED pixels used for Neopixel stripe
NEOPIXEL_NB_PIXELS = 60

# Default LED actions
DEFAULT_LED_ACTIONS = {
    str(types.State.PROCESSING + types.Deployment.RED): types.Action.RUNNING_LIGHT,
    str(types.State.PROCESSING + types.Deployment.GREEN): types.Action.RUNNING_LIGHT,
    str(types.State.SUCCESSFUL + types.Deployment.RED): types.Action.GREEN,
    str(types.State.SUCCESSFUL + types.Deployment.GREEN): types.Action.GREEN,
    str(types.State.FAILED + types.Deployment.RED): types.Action.RED,
    str(types.State.FAILED + types.Deployment.GREEN): types.Action.RED,
    str(types.State.DISABLED + types.Deployment.RED): types.Action.OFF,
    str(types.State.DISABLED + types.Deployment.GREEN): types.Action.OFF,
    str(types.State.ENABLED + types.Deployment.RED): types.Action.WHITE,
    str(types.State.ENABLED + types.Deployment.GREEN): types.Action.WHITE
}

# Mqtt client config
MQTT_CLIENT_ENDPOINT = "a1qm0b6u07r8e4-ats.iot.eu-central-1.amazonaws.com"
MQTT_CLIENT_PORT = 8883
MQTT_CLIENT_CERT_FILEPATH = os.path.join(CERTIFICATES_PATH, "certificate.pem.crt")
MQTT_CLIENT_PRI_KEY_FILEPATH = os.path.join(CERTIFICATES_PATH, "private.pem.key")
MQTT_CLIENT_CLIENT_ID = "RaspberryPi"

# MQTT publish topic
MQTT_CLIENT_PUBLISHING_TOPIC = "cicd/frontend"
MQTT_CLIENT_PUBLISHING_MESSAGE_GETALLSTATES = json.dumps({"type": "get_all_states"})
MQTT_CLIENT_PUBLISHING_MESSAGE_PRESSED = json.dumps({"type": "buttonPressed", "button": "__button__"})

# MQTT listening topic
MQTT_CLIENT_SUBSCRIPTION_TOPIC = "cicd/backend"
