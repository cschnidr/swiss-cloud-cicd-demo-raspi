# ChaosKitty

CICD dashboard is a Raspberry Pi-based project that interacts with AWS IoT Core to display changes in an AWS architecture based on a button press and visualizes the status with LED stripes.

---

## **Setup**

### **Raspi Hardware Setup**

1. **Requirements**:

    - Raspberry Pi (or similar)
    - [LED stripe with Neopixels library support](https://www.adafruit.com/product/1138)

2. **Connections**:

    - [LED Stripe connected to Port 18](https://learn.adafruit.com/neopixels-on-raspberry-pi/raspberry-pi-wiring)
    - [Button connected to Port 16](https://roboticsbackend.com/raspberry-pi-gpio-interrupts-tutorial/)

3. **Configuration**:

- If you're planning to use different ports, make sure to modify `src/utils/constants.py`:

```python
BUTTON_PORTS = { ... }
NEOPIXEL_PORT = board.D18
NEOPIXEL_NB_PIXELS = 100
```

- Configure LED positions in `/src/utils/constants.py`: 

``` python 
COMPONENT_PIXELS = { ... }
```

- Configure default actions per state in `/src/utils/constants.py`:  

``` python
DEFAULT_LED_ACTIONS = { ... }
```

### **Test on Non-Raspi***

- If you run the scripts on EC2, make sure to install the following packages:

``` bash
sudo yum install pip gcc python3-devel 
```

- Pass the argument `--mock` to the application: 

``` bash
python3 -m src.main --mock
```

This one is considered in `main.py`, `interfaces/neopxl.py`, `utils/constants.py` and `requirements.txt`. 

### **Raspi Software Setup**

#### **1. Environment and Dependencies**

- Copy the entire `raspi` folder of this repo to the Raspberry Pi
- Verify if `virtualenv` is installed:

```bash
python3 -m virtualenv --version
```

- If not installed:

```bash
python3 -m pip install virtualenv
```

- Create a virtual environment:

```bash
python3 -m virtualenv venv
```

- Activate the virtual environment:

```bash
source venv/bin/activate
```

- Install necessary dependencies:
    
```bash
pip install -r requirements.txt
```

### **MQTT messages**

Messages sent by backend:
- Topic: `/cicd/backend`
- Payload:

``` json 
{
  "deployment": "<green|red>",
  "component": "<repo|build|qa|transitionRegion1|region1|transitionRegion2|region2>",
  "status": "<processing|successful|failed|disabled|enabled>"
}
```

Messages sent by frontend:
- Topic: `/cicd/frontend`
- Payload defines the action
- Button pressed:

``` json
{
  "type": "buttonPressed",
  "button": "<deployGreen|deployRed|enableDisableTransitionRegion1|enableDisableTransitionRegion2>"
}
```

 - Initial / get all states:

``` json
{
  "type": "getAllStates"
}
```

#### **2. AWS IoT Core Setup**

To setup the IoT connection, follow the below steps. Create new "Thing" in AWS IoT:
- Navigate to https://eu-central-1.console.aws.amazon.com/iot/home?region=eu-central-1#/thinghub
- Choose "Create Things"
- Select "Create single thing"
- Choose a thing name
- Select "Auto-generate a new certificate"
- Attach new policy:

``` json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "iot:Connect",
      "Resource": "arn:aws:iot:<region>:<account-id>:client/<thing-name>"
    },
    {
      "Effect": "Allow",
      "Action": "iot:Publish",
      "Resource": "arn:aws:iot:<region>:<account-id>:topic/cicd/frontend"
    },
    {
      "Effect": "Allow",
      "Action": "iot:Receive",
      "Resource": "arn:aws:iot:<region>:<account-id>:topic/cicd/backend"
    },
    {
      "Effect": "Allow",
      "Action": "iot:Subscribe",
      "Resource": [
        "arn:aws:iot:<region>:<account-id>:topic/cicd/backend",
        "arn:aws:iot:<region>:<account-id>:topicfilter/cicd/backend"
      ]
    }
  ]
}
```

- Choose "Create Thing"
- Download all certificates and keys

Move on to the Raspberry Pi:
-   Place your Raspberry Pi's AWS certificates in `src/utils/certificates`.
-   Update the parameters in `src/utils/constants.py`.

### **Testing**

To test the setup:

1. Ensure the virtual environment is activated:

```bash
source venv/bin/activate
```

2. Run the main script:

```bash
python3 -m src.main # might require sudo / root on Raspi
```

3. Test the integration by sending messages via the AWS IoT Core Test Broker on the topic `cicd/backend`, and use a message according to the specification in *2. AWS IoT Core Setup*.

---

## **Understanding the Flow**

### 1. **User Action - Button Press**

The core interaction begins when a user presses a button connected to the Raspberry Pi. The buttons are linked to the Raspberry Pi on Ports defined in `/src/utils/constants.py`. We have multiple buttons connected, each of them triggering a backend action: 

- **Deploy Green**: Starts a deployment of the *GREEN* branch, to all active environments (triggers at least repo, build and QA)
- **Deploy Red**: Starts a deployment of the *RED* branch, to all active environments (triggers at least repo, build and QA)
- **Enable / Disable region 1**: Enables or disables transition to *Region 1*. If enabled, and the current state doesn't match, a deployment is automatically triggered.
- **Enable / Disable region 2**: Enables or disables transition to *Region 2*. If enabled, and the current state doesn't match, a deployment is automatically triggered.

When pressed, it triggers an event that leads to a message being published on a predefined MQTT topic. The topic and the message payload are determined by the following parameters in `/src/utils/constants.py`:

    ```python
    MQTT_CLIENT_PUBLISHING_TOPIC = "some/topic"
    MQTT_CLIENT_PUBLISHING_MESSAGE = "some-message"
    ```

### 2. **AWS Reaction to Published Message**

Upon receiving the message:

- The AWS infrastructure, particularly AWS IoT Core, detects the change and processes it. This results in a new build, or enabling / disabling a region.
- Once done, the backend publishes an update message on the topic `cicd/backend`, which is consumed by the Raspberry Pi in order to update the LED configuration.

### 3. **LED Stripe Visualization**

The LED stripe connected to the Raspberry Pi acts as a visual indicator of the state of the deployments:

- Each LED or a group of LEDs represents a specific component environment in your AWS architecture.
- As messages are received on the `cicd/backend` topics, the LEDs change colors based on the message's payload
- The default actions per state are configured in `/src/utils/constants.py`:

``` python
DEFAULT_LED_ACTIONS = { ... }
```

- They can also be set dynamically per `ArchitectureComponent` in `main.py`, if desired.
- The mapping to the corresponding AWS service/component is defined in `/src/utils/types.py`:

```python
class ComponentIds: { ... }
```

### 4. **Feedback Loop**

With the LEDs visualizing the status, users get immediate feedback on the deplyment's state post the button press. This can be useful for debugging, monitoring, or even gamifying the AWS setup.

---

## **Further Customization**

### 1. **Adapting MQTT Topics and Payloads**

If you wish to modify the MQTT topics your Raspberry Pi listens to or the expected payload messages:

- Head to `/src/utils/constants.py`:
- Modify `MQTT_CLIENT_SUBSCRIPTION_TOPIC` for changing the subscription topic
- Modify the below elements for changing the publishing topics and details:

``` python 
MQTT_CLIENT_PUBLISHING_TOPIC = ...
MQTT_CLIENT_PUBLISHING_MESSAGE_GETALLSTATES = ...
MQTT_CLIENT_PUBLISHING_MESSAGE_PRESSED = ...
```

### 2. **Customizing Hardware Components**

To tailor the local system to your specific AWS setup, modify the `LocalComponent` objects created in `src/main.py`. Each element can be configured with LED actions per state, omitting them uses the default states as defined in `src/utils/defaults.py`. On the other hand, AWS components are defined via `AwsComponentState` objects.

### 3. **LED actions**

LED actions are defined in the `src/utils/types.py` file

```python
class Action(Enum):
    OFF = 0
    RED = 1
    ORANGE = 2
    GREEN = 3
    WHITE = 4
    RUNNING_LIGHT = 5
```

If you add an action in the above enum, make sure to implement the function in `/src/interfaces/neopxl.py` and link the enum to the function name.

```python
class NeopixelInterface():
    def __init__(self, port: int, nb_pixels: int):
        ...

        self.action_methods = {
            ...
            types.Action.NEW_ACTION: self._new_function
        }

    def _new_function(self, pixels):
        for pixel in pixels:
            ...
```

### 4. **Configuring AWS Interactions**

Remember to keep the AWS IoT Core setup and Raspberry Pi in sync. If you modify the topics or payloads in the Raspberry Pi, ensure corresponding changes are made in AWS IoT Core's rules and actions.

### Auto Startup

sudo crontab -e
# TODO document content of `startup.sh`
@reboot bash /home/schnidrc/aws-chaos-kitty/startup.sh > /home/schnidrc/aws-chaos-kitty/logs/cronlog 2>&1
