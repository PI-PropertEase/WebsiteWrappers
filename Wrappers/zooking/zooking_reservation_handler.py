from ProjectUtils.MessagingService.queue_definitions import channel, EXCHANGE_NAME, WRAPPER_TO_APP_ROUTING_KEY, \
    WRAPPER_TO_CALENDAR_ROUTING_KEY
from ProjectUtils.MessagingService.schemas import (
    MessageFactory,
    MessageType,
    to_json, from_json, Service,
)
from .zooking_wrapper import ZookingAPIWrapper


def handle_recv(channel, method, properties, body):
    delivery_tag = method.delivery_tag

    message = from_json(body)
    print(message.__dict__)
    body = message.body
    match message.message_type:
        case MessageType.RESERVATION_IMPORT_OVERLAP:
            print("RESERVATION_IMPORT_OVERLAP: ", body)
            wrapper.delete_reservation(body["old_internal_id"])
        case MessageType.RESERVATION_IMPORT_REQUEST:
            print("RESERVATION_IMPORT_REQUEST: ", body)
            for user_email, user_service in body["users_with_services"].items():
                print(user_email, user_service)
                if "zooking" in user_service:
                    reservations = wrapper.import_new_pending_or_canceled_reservations({"email": user_email})
                    channel.basic_publish(exchange=EXCHANGE_NAME, routing_key=WRAPPER_TO_CALENDAR_ROUTING_KEY, body=to_json(
                        MessageFactory.create_import_reservations_response_message(Service.ZOOKING, reservations)
                    ))
        case MessageType.RESERVATION_IMPORT_CONFIRM:
            print("RESERVATION_IMPORT_CONFIRM: ", body)
            wrapper.confirm_reservation(body["internal_id"])


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
