from ProjectUtils.MessagingService.queue_definitions import channel, EXCHANGE_NAME, WRAPPER_TO_APP_ROUTING_KEY, \
    WRAPPER_TO_CALENDAR_ROUTING_KEY
from ProjectUtils.MessagingService.schemas import (
    MessageFactory,
    MessageType,
    to_json, from_json, Service,
)
from Wrappers.models import set_property_mapped_id
from .zooking_wrapper import ZookingAPIWrapper


def handle_recv(channel, method, properties, body):
    delivery_tag = method.delivery_tag

    message = from_json(body)
    print(message.__dict__)
    match message.message_type:
        case MessageType.PROPERTY_CREATE:
            wrapper.create_property(message.body)
        case MessageType.PROPERTY_UPDATE:
            body = message.body
            wrapper.update_property(body["internal_id"], body["update_parameters"])
        case MessageType.PROPERTY_DELETE:
            wrapper.delete_property(message.body)
        case MessageType.PROPERTY_CREATE:
            wrapper.create_property(message.body)
        case MessageType.PROPERTY_IMPORT:
            body = message.body
            properties = wrapper.import_properties(body)
            channel.basic_publish(exchange=EXCHANGE_NAME, routing_key=WRAPPER_TO_APP_ROUTING_KEY, body=to_json(
                MessageFactory.create_import_properties_response_message(Service.ZOOKING, properties)
            ))
            reservations = wrapper.import_reservations(body)
            channel.basic_publish(exchange=EXCHANGE_NAME, routing_key=WRAPPER_TO_CALENDAR_ROUTING_KEY, body=to_json(
                MessageFactory.create_import_reservations_response_message(Service.ZOOKING, reservations)
            ))
        case MessageType.PROPERTY_IMPORT_DUPLICATE:
            body = message.body
            set_property_mapped_id(Service.ZOOKING, body["old_internal_id"], body["new_internal_id"])

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
