from ProjectUtils.MessagingService.queue_definitions import channel, QUEUE_NAME
from ProjectUtils.MessagingService.schemas import PropertyType
from .zooking_wrapper import ZookingAPIWrapper
import json


def handle_recv(channel, method, properties, body):
    delivery_tag = method.delivery_tag

    message = json.loads(body)
    msg_type = message.get("type")
    if msg_type == PropertyType.CREATE_PROPERTY:
        wrapper.create_property(message.get("body"))
    elif msg_type == PropertyType.UPDATE_PROPERTY:
        wrapper.update_property(message.get("body"))
    elif msg_type == PropertyType.DELETE_PROPERTY:
        wrapper.delete_property(message.get("body"))

    channel.basic_ack(delivery_tag)


def run():
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=handle_recv)
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()


if __name__ == "__main__":
    wrapper = ZookingAPIWrapper()
    run()
