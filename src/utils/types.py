from enum import Enum
from dataclasses import dataclass
from typing import List
import logging

@dataclass
class State:
    PROCESSING = 'processing'
    SUCCESSFUL = 'successful'
    FAILED = 'failed'
    DISABLED = 'disabled'
    ENABLED = 'enabled'

@dataclass
class Deployment:
    GREEN = 'green'
    RED = 'red'

@dataclass
class Buttons:
    DEPLOY_GREEN:str = 'deployGreen'
    DEPLOY_RED:str = 'deployRed'
    ENABLE_DISABLE_REGION1:str = 'enableDisableRegion1'
    ENABLE_DISABLE_REGION2:str = 'enableDisableRegion2'

# LED actions
class Action(Enum):
    OFF = 0
    RED = 1
    ORANGE = 2
    GREEN = 3
    WHITE = 4
    RUNNING_LIGHT = 5

class ComponentIds(str, Enum):
    repo = 'repo'
    build = 'build'
    qa = 'qa'
    transitionRegion1 = 'transitionRegion1'
    region1 = 'region1'
    transitionRegion2 = 'transitionRegion2'
    region2 = 'region2'

@dataclass
class AwsComponentState:
    deployment: Deployment = ''
    state: State = ''

@dataclass
class AwsComponentStates:
    """ Defines component states globally - Singleton """
    repo: AwsComponentState
    build: AwsComponentState
    qa: AwsComponentState
    transitionRegion1: AwsComponentState
    region1: AwsComponentState
    transitionRegion2: AwsComponentState
    region2: AwsComponentState

    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if not isinstance(cls._instance, cls):
            cls._instance = super(AwsComponentStates, cls).__new__(cls)
        return cls._instance

    def updateComponentState(self, component_id: str, aws_component_state: AwsComponentState):
        if component_id == ComponentIds.repo:
            self.repo = aws_component_state
        elif component_id == ComponentIds.build:
            self.build = aws_component_state
        elif component_id == ComponentIds.qa:
            self.qa = aws_component_state
        elif component_id == ComponentIds.transitionRegion1:
            self.transitionRegion1 = aws_component_state
        elif component_id == ComponentIds.region1:
            self.region1 = aws_component_state
        elif component_id == ComponentIds.transitionRegion2:
            self.transitionRegion2 = aws_component_state
        elif component_id == ComponentIds.region2:
            self.region2 = aws_component_state

    def getComponentState(self, component_id: str) -> AwsComponentState:
        if component_id == ComponentIds.repo:
            return self.repo
        elif component_id == ComponentIds.build:
            return self.build
        elif component_id == ComponentIds.qa:
            return self.qa
        elif component_id == ComponentIds.transitionRegion1:
            return self.transitionRegion1
        elif component_id == ComponentIds.region1:
            return self.region1
        elif component_id == ComponentIds.transitionRegion2:
            return self.transitionRegion2
        elif component_id == ComponentIds.region2:
            return self.region2

class LocalComponent():
    deployment: Deployment = ''
    state: State = ''

    from src.utils.constants import DEFAULT_LED_ACTIONS
    from src.interfaces.neopxl import NeopixelInterface
    def __init__(self,
                 neopixel_client: NeopixelInterface,
                 state_id: ComponentIds,
                 pixels: List[int],
                 processing_action_red:Action = DEFAULT_LED_ACTIONS.get(State.PROCESSING + Deployment.RED),
                 processing_action_green:Action = DEFAULT_LED_ACTIONS.get(State.PROCESSING + Deployment.GREEN),
                 successful_action_red:Action = DEFAULT_LED_ACTIONS.get(State.SUCCESSFUL + Deployment.RED),
                 successful_action_green: Action = DEFAULT_LED_ACTIONS.get(State.SUCCESSFUL + Deployment.GREEN),
                 failed_action_red:Action = DEFAULT_LED_ACTIONS.get(State.FAILED + Deployment.RED),
                 failed_action_green: Action = DEFAULT_LED_ACTIONS.get(State.FAILED + Deployment.GREEN),
                 disabled_action_red:Action = DEFAULT_LED_ACTIONS.get(State.DISABLED + Deployment.RED),
                 disabled_action_green: Action = DEFAULT_LED_ACTIONS.get(State.DISABLED + Deployment.RED),
                 enabled_action_red:Action = DEFAULT_LED_ACTIONS.get(State.ENABLED + Deployment.RED),
                 enabled_action_green:Action = DEFAULT_LED_ACTIONS.get(State.ENABLED + Deployment.GREEN)):
        self.neopixel_client = neopixel_client
        self.state_id = state_id
        self.pixels = pixels
        self.processing_action_red = processing_action_red
        self.processing_action_green = processing_action_green
        self.successful_action_red = successful_action_red
        self.successful_action_green = successful_action_green
        self.failed_action_red = failed_action_red
        self.failed_action_green = failed_action_green
        self.disabled_action_red = disabled_action_red
        self.disabled_action_green = disabled_action_green
        self.enabled_action_red = enabled_action_red
        self.enabled_action_green = enabled_action_green
        self.deployment = ''
        self.state = ''

    def _forward_action_to_driver(self):

        if self.deployment and self.state:
            logging.debug(f"Updating pixel configuration of component {self.state_id} with state {self.state} and "
                      f"deployment "
                  f"{self.deployment}")

            # Using ugly if/elif to ensure the script runs on Python < 3.10
            if self.deployment == Deployment.RED:
                if self.state == State.PROCESSING:
                    self.neopixel_client.update_pixels(self.pixels, self.processing_action_red)
                elif self.state == State.SUCCESSFUL:
                    self.neopixel_client.update_pixels(self.pixels, self.successful_action_red)
                elif self.state == State.FAILED:
                    self.neopixel_client.update_pixels(self.pixels, self.failed_action_red)
                elif self.state == State.DISABLED:
                    self.neopixel_client.update_pixels(self.pixels, self.disabled_action_red)
                elif self.state == State.ENABLED:
                    self.neopixel_client.update_pixels(self.pixels, self.enabled_action_red)
            elif self.deployment == Deployment.GREEN:
                if self.state == State.PROCESSING:
                    self.neopixel_client.update_pixels(self.pixels, self.processing_action_green)
                elif self.state == State.SUCCESSFUL:
                    self.neopixel_client.update_pixels(self.pixels, self.successful_action_green)
                elif self.state == State.FAILED:
                    self.neopixel_client.update_pixels(self.pixels, self.failed_action_green)
                elif self.state == State.DISABLED:
                    self.neopixel_client.update_pixels(self.pixels, self.disabled_action_green)
                elif self.state == State.ENABLED:
                    self.neopixel_client.update_pixels(self.pixels, self.enabled_action_green)

    def update(self, aws_component_state:AwsComponentState):
        logging.info(f"Updating component {self.state_id} with deployment {aws_component_state.deployment} and state "
              f"{aws_component_state.state}")
        self.deployment = aws_component_state.deployment
        self.state = aws_component_state.state

    def updatePixels(self):
        self._forward_action_to_driver()
        # self.neopixel_client.show_changes() # commented because called from main

@dataclass
class LocalComponentStates:
    """ Defines component states globally - Singleton """
    repo: LocalComponent
    build: LocalComponent
    qa: LocalComponent
    transitionRegion1: LocalComponent
    region1: LocalComponent
    transitionRegion2: LocalComponent
    region2: LocalComponent

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not isinstance(cls._instance, cls):
            cls._instance = super(LocalComponentStates, cls).__new__(cls)
        return cls._instance

    def getComponentState(self, component_id: str) -> LocalComponent:
        if component_id == ComponentIds.repo:
            return self.repo
        elif component_id == ComponentIds.build:
            return self.build
        elif component_id == ComponentIds.qa:
            return self.qa
        elif component_id == ComponentIds.transitionRegion1:
            return self.transitionRegion1
        elif component_id == ComponentIds.region1:
            return self.region1
        elif component_id == ComponentIds.transitionRegion2:
            return self.transitionRegion2
        elif component_id == ComponentIds.region2:
            return self.region2

    def getAllComponentStates(self):
        return [self.repo, self.build, self.qa, self.transitionRegion1, self.region1, self.transitionRegion2, self.region2]

@dataclass
class MqttClientOption:
    """Configuration for the creation of MQTT5 client
    Account - Frankfurt - IoT Core - Mqtt test client - Raspi4 - Certificates (policy haengt am certificate) - iot receive anpassen bei anderem topic & publish -
    test client - subscribe auf broker - topic # - testen ob publish klappt -  
    Args:
        endpoint (str): Host name of AWS IoT server.
        port (int): Connection port for direct connection. "AWS IoT supports 443 and 8883.
        cert_filepath (str): Path to certificate file.
        pri_key_filepath (str): Path to private key file.
        client_id (str): Globally unique client id.
    """
    endpoint: str
    port: int
    cert_filepath: str
    pri_key_filepath: str
    client_id: str