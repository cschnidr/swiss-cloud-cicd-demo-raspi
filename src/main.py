#!/usr/bin/env python3
import signal
import sys
import time
import logging

# Check if we have to activate MOCK mode
if sys.argv and len(sys.argv) > 1 and sys.argv[1] == "--mock":
    import fake_rpi
    sys.modules['RPi'] = fake_rpi.RPi     # Fake RPi
    sys.modules['RPi.GPIO'] = fake_rpi.RPi.GPIO # Fake GPIO

import RPi.GPIO as GPIO

import src.interfaces.button as button_interface
import src.interfaces.mqtt as mqtt_interface
import src.interfaces.neopxl as neopixel_interface
import src.utils.constants as constants
import src.utils.types as types

logging.basicConfig(level=constants.LOG_LEVEL)

def create_signal_handler(
        mqtt_client: mqtt_interface.MqttClientInterface,
        neopixel_client: neopixel_interface.NeopixelInterface):
    """ Wrapper to provide signal_handler with references to objects needed to be shut down. """
    def signal_handler(sig, frame):
        """ Called when Ctl + C is pressed """
        mqtt_client.cleanup()
        neopixel_client.cleanup()
        GPIO.cleanup()
        sys.exit(0)
    return signal_handler

button_initialized = {
    str(types.Buttons.DEPLOY_GREEN): False,
    str(types.Buttons.DEPLOY_RED): False,
    str(types.Buttons.ENABLE_DISABLE_REGION1): False,
    str(types.Buttons.ENABLE_DISABLE_REGION2): False
}

def on_button_clicked_callback(button):
    global last_click_timestamp
    global button_initialized

    if not button_initialized.get(str(button)):
        logging.info(f'Initializing button {str(button)}...')
        button_initialized[str(button)] = True
        return
    else:
        logging.info(f'Button {str(button)} already initialized')

    current_time = time.time()

    # Check if the difference between the current time and the last click timestamp is more than 10 seconds
    if current_time - last_click_timestamp >= 2:
        logging.info("Pressed button: " + button)
        mqtt_client.publish_message(
            constants.MQTT_CLIENT_PUBLISHING_TOPIC,
            constants.MQTT_CLIENT_PUBLISHING_MESSAGE_PRESSED.replace("__button__", button))

        # Update the timestamp
        last_click_timestamp = current_time
    else:
        logging.info("Button pressed too quickly. Please wait for 2 seconds between presses.")

def on_button_clicked_callback_green(value):
    on_button_clicked_callback(types.Buttons.DEPLOY_GREEN)

def on_button_clicked_callback_red(value):
    on_button_clicked_callback(types.Buttons.DEPLOY_RED)

def on_button_clicked_callback_disableregion1(value):
    on_button_clicked_callback(types.Buttons.ENABLE_DISABLE_REGION1)

def on_button_clicked_callback_disableregion2(value):
    on_button_clicked_callback(types.Buttons.ENABLE_DISABLE_REGION2)

last_click_timestamp = 0  # initializing the timestamp at the start

neopixel_client: neopixel_interface.NeopixelInterface = neopixel_interface.NeopixelInterface(
    port=constants.NEOPIXEL_PORT,
    nb_pixels=constants.NEOPIXEL_NB_PIXELS)

repo_component : types.LocalComponent = types.LocalComponent(
    neopixel_client = neopixel_client,
    state_id = types.ComponentIds.repo,
    pixels = constants.COMPONENT_PIXELS.get(types.ComponentIds.repo),
)

build_component : types.LocalComponent = types.LocalComponent(
    neopixel_client = neopixel_client,
    state_id = types.ComponentIds.build,
    pixels = constants.COMPONENT_PIXELS.get(types.ComponentIds.build),
)

qa_component : types.LocalComponent = types.LocalComponent(
    neopixel_client = neopixel_client,
    state_id = types.ComponentIds.qa,
    pixels = constants.COMPONENT_PIXELS.get(types.ComponentIds.qa),
)

transitionRegion1_component : types.LocalComponent = types.LocalComponent(
    neopixel_client = neopixel_client,
    state_id = types.ComponentIds.transitionRegion1,
    pixels = constants.COMPONENT_PIXELS.get(types.ComponentIds.transitionRegion1),
)

region1_component : types.LocalComponent = types.LocalComponent(
    neopixel_client = neopixel_client,
    state_id = types.ComponentIds.region1,
    pixels = constants.COMPONENT_PIXELS.get(types.ComponentIds.region1),
)

transitionRegion2_component : types.LocalComponent = types.LocalComponent(
    neopixel_client = neopixel_client,
    state_id = types.ComponentIds.transitionRegion2,
    pixels = constants.COMPONENT_PIXELS.get(types.ComponentIds.transitionRegion2),
)

region2_component : types.LocalComponent = types.LocalComponent(
    neopixel_client = neopixel_client,
    state_id = types.ComponentIds.region2,
    pixels = constants.COMPONENT_PIXELS.get(types.ComponentIds.region2),
)

local_component_states = types.LocalComponentStates(
    repo = repo_component,
    build = build_component,
    qa = qa_component,
    transitionRegion1 = transitionRegion1_component,
    region1 = region1_component,
    transitionRegion2 = transitionRegion2_component,
    region2 = region2_component
)

aws_component_states = types.AwsComponentStates(
    repo = types.AwsComponentState(),
    build = types.AwsComponentState(),
    qa = types.AwsComponentState(),
    transitionRegion1 = types.AwsComponentState(),
    region1 = types.AwsComponentState(),
    transitionRegion2 = types.AwsComponentState(),
    region2 = types.AwsComponentState()
)

mqtt_client_options: types.MqttClientOption = types.MqttClientOption(
    endpoint=constants.MQTT_CLIENT_ENDPOINT,
    port=constants.MQTT_CLIENT_PORT,
    cert_filepath=constants.MQTT_CLIENT_CERT_FILEPATH,
    pri_key_filepath=constants.MQTT_CLIENT_PRI_KEY_FILEPATH,
    client_id=constants.MQTT_CLIENT_CLIENT_ID)

mqtt_client: mqtt_interface.MqttClientInterface = mqtt_interface.MqttClientInterface(
    aws_component_states,
    local_component_states,
    mqtt_client_options,
    constants.MQTT_CLIENT_SUBSCRIPTION_TOPIC)

# Link button actions
button_client_deployGreen: button_interface.ButtonInterface = button_interface.ButtonInterface(
    constants.BUTTON_PORTS.get(types.Buttons.DEPLOY_GREEN),
    on_button_clicked_callback_green)
button_client_deployRED: button_interface.ButtonInterface = button_interface.ButtonInterface(
    constants.BUTTON_PORTS.get(types.Buttons.DEPLOY_RED),
    on_button_clicked_callback_red)
button_client_enableDisableRegion1: button_interface.ButtonInterface = button_interface.ButtonInterface(
    constants.BUTTON_PORTS.get(types.Buttons.ENABLE_DISABLE_REGION1),
    on_button_clicked_callback_disableregion1)
button_client_enableDisableRegion2: button_interface.ButtonInterface = button_interface.ButtonInterface(
    constants.BUTTON_PORTS.get(types.Buttons.ENABLE_DISABLE_REGION2),
    on_button_clicked_callback_disableregion2)

signal.signal(signal.SIGINT, create_signal_handler(
    mqtt_client, neopixel_client))
signal.signal(signal.SIGTERM, create_signal_handler(
    mqtt_client, neopixel_client))

logging.info("Starting script execution")

# On startup, publish a message to MQTT asking for all states
logging.info("Publishing message to get all states")
mqtt_client.publish_message(
    constants.MQTT_CLIENT_PUBLISHING_TOPIC,
    constants.MQTT_CLIENT_PUBLISHING_MESSAGE_GETALLSTATES)

while True:
    # signal.pause()
    # Constantly update local components so that pixels can move
    for local_component in local_component_states.getAllComponentStates():
        local_component.updatePixels()
    neopixel_client.show_changes()