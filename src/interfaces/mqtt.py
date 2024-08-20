import json
from concurrent.futures import Future
from awsiot import mqtt5_client_builder
from awscrt import mqtt5
import logging

class MqttClientInterface():
    from src.utils.types import AwsComponentStates, LocalComponentStates, MqttClientOption
    def __init__(self,
                 aws_component_states: AwsComponentStates,
                 local_component_states: LocalComponentStates,
                 client_options: (
        MqttClientOption), subscription_topic: str):
        """
        aws_component_states (ComponentStates): Global component states of the architecture
        client_options (MqttClientOption): Configuration for the creation of MQTT5 client
        message_topic (str): Filter mask for topics to subscribe to, e.g. "test/topic"
        """
        self.aws_component_states = aws_component_states
        self.local_component_states = local_component_states
        self.subscription_topic = subscription_topic
        self.timeout = 100
        self.future_stopped = Future()
        self.future_connection_success = Future()

        # Create MQTT5 client
        self.client: mqtt5.Client = mqtt5_client_builder.mtls_from_path(
            endpoint=client_options.endpoint,
            port=client_options.port,
            cert_filepath=str(client_options.cert_filepath),
            pri_key_filepath=str(client_options.pri_key_filepath),
            client_id=client_options.client_id,
            on_publish_received=self._on_publish_received,
            on_lifecycle_stopped=self._on_lifecycle_stopped,
            on_lifecycle_connection_success=self._on_lifecycle_connection_success,
            on_lifecycle_connection_failure=self._on_lifecycle_connection_failure
        )
        logging.info("MQTT5 Client Created")

        logging.info(f"Connecting to {client_options.endpoint} with client ID '{client_options.client_id}'...")
        self.client.start()

        # Wait for connection to be successful
        lifecycle_connect_success_data = self.future_connection_success.result(self.timeout)
        connack_packet = lifecycle_connect_success_data.connack_packet
        logging.info(f"Connected to endpoint: {client_options.endpoint} with client ID '{client_options.client_id}' with reason_code:{repr(connack_packet.reason_code)}")

        # Subscribe to the topic
        logging.info(f"Subscribing to topic '{self.subscription_topic}'...")
        subscribe_future = self.client.subscribe(subscribe_packet=mqtt5.SubscribePacket(
            subscriptions=[mqtt5.Subscription(
                topic_filter=self.subscription_topic,
                qos=mqtt5.QoS.AT_LEAST_ONCE)]
        ))
        suback = subscribe_future.result(self.timeout)
        logging.info("Subscribed with {}".format(suback.reason_codes))
        
    # Callback for the lifecycle event Connection Success
    def _on_lifecycle_connection_success(self, lifecycle_connect_success_data: mqtt5.LifecycleConnectSuccessData):
        logging.info("Lifecycle Connection Success")
        if not self.future_connection_success.done():
            self.future_connection_success.set_result(lifecycle_connect_success_data)

    # Callback for the lifecycle event Connection Failure
    def _on_lifecycle_connection_failure(self, lifecycle_connection_failure: mqtt5.LifecycleConnectFailureData):
        logging.info("Lifecycle Connection Failure")
        logging.info(f"Connection failed with exception: {lifecycle_connection_failure.exception}")
    
    # Callback when any publish is received
    def _on_publish_received(self, publish_packet_data):
        publish_packet = publish_packet_data.publish_packet
        assert isinstance(publish_packet, mqtt5.PublishPacket)
        logging.info(f"Received message from topic {publish_packet.topic}: {publish_packet.payload}")
        
        # We expect messages in the following format:
        # {
        #     "deployment": "<green|red>",
        #     "component": "<repo|build|qa|transitionRegion1|region1|transitionRegion2|region2>",
        #     "status": "<processing|successful|failed|disabled|enabled>"
        # }
        if publish_packet and publish_packet.payload:
            logging.info("Payload: " + publish_packet.payload.decode("utf-8"))
        else:
            logging.info("No payload attached. Stop processing received message")
            return

        payload = json.loads(publish_packet.payload)
        component = payload.get("component")
        deployment = payload.get("deployment")
        status = payload.get("status")

        if component and deployment and status:
            logging.info(f"Received required information for update: {component}, {deployment}, {status}")
            aws_component_state = self.aws_component_states.getComponentState(component)
            if aws_component_state:
                aws_component_state.deployment = deployment
                aws_component_state.state = status
                self.aws_component_states.updateComponentState(component_id=component, aws_component_state=aws_component_state)

                #trigger update on local component
                local_component = self.local_component_states.getComponentState(component)
                local_component.update(aws_component_state)

    # Callback for the lifecycle event Stopped
    def _on_lifecycle_stopped(self, lifecycle_stopped_data: mqtt5.LifecycleStoppedData):
        logging.info("Lifecycle Stopped")
        self.future_stopped.set_result(lifecycle_stopped_data)

    def cleanup(self):
        """ Remove subscription and stop the client """
        logging.info(f"Unsubscribing from topic {self.subscription_topic}")
        unsubscribe_future = self.client.unsubscribe(unsubscribe_packet=mqtt5.UnsubscribePacket(
            topic_filters=[self.subscription_topic]))
        unsuback = unsubscribe_future.result(self.timeout)
        logging.info(f"Unsubscribed from topic {self.subscription_topic} with {unsuback.reason_codes}")
        logging.info("Stopping Client")
        self.client.stop()
        self.future_stopped.result(self.timeout)
        logging.info("Client Stopped!")

    def publish_message(self, topic: str, message: str):
        logging.info(f"Publishing message to topic '{topic}': {message}")
        publish_future = self.client.publish(mqtt5.PublishPacket(
            topic=topic,
            payload=json.dumps(message),
            qos=mqtt5.QoS.AT_LEAST_ONCE
        ))
        publish_completion_data = publish_future.result(self.timeout)
        logging.info(f"PubAck received with {repr(publish_completion_data.puback.reason_code)}")