from ProjectUtils.MessagingService.queue_definitions import channel, EXCHANGE_NAME, WRAPPER_TO_APP_ROUTING_KEY
from ProjectUtils.MessagingService.schemas import (
    MessageFactory,
    MessageType,
    to_json,
)
from .zooking_wrapper import ZookingAPIWrapper
import json


def handle_recv(channel, method, properties, body):
    delivery_tag = method.delivery_tag

    message = json.loads(body)
    msg_type = message.get("type")
    if msg_type == MessageType.PROPERTY_CREATE:
        wrapper.create_property(message.get("body"))
    elif msg_type == MessageType.PROPERTY_UPDATE:
        wrapper.update_property(message.get("body"))
    elif msg_type == MessageType.PROPERTY_DELETE:
        wrapper.delete_property(message.get("body"))
    elif msg_type == MessageType.PROPERTY_IMPORT:
        properties = wrapper.import_properties(message.get("body"))
        body = MessageFactory.create_import_properties_response_message(properties)
        channel.basic_publish(exchange=EXCHANGE_NAME, routing_key=WRAPPER_TO_APP_ROUTING_KEY, body=to_json(body))

    channel.basic_ack(delivery_tag)


def run():
    channel.basic_consume(queue=wrapper.queue, on_message_callback=handle_recv)
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()


if __name__ == "__main__":
    wrapper = ZookingAPIWrapper()
    run()
