import logging

from sys import stdout
from ProjectUtils.MessagingService.queue_definitions import channel, EXCHANGE_NAME, WRAPPER_TO_APP_ROUTING_KEY, \
    WRAPPER_TO_CALENDAR_ROUTING_KEY
from ProjectUtils.MessagingService.schemas import (
    MessageFactory,
    MessageType,
    to_json, from_json
)
from Wrappers.base_wrapper.wrapper import BaseWrapper

logging.basicConfig(level=logging.INFO, stream=stdout)
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)


def handle_recv(channel, method, properties, body, wrapper:BaseWrapper):
    delivery_tag = method.delivery_tag
    try:
        LOGGER.info("%s - received message", wrapper.service_schema.name)
        message = from_json(body)
        body = message.body
        match message.message_type:
            case MessageType.RESERVATION_IMPORT_OVERLAP:
                LOGGER.info("%s - MessageType: RESERVATION_IMPORT_OVERLAP. Body: %s", wrapper.service_schema.name, body)
                wrapper.cancel_overlapping_reservation(body["old_reservation_internal_id"])
            case MessageType.RESERVATION_CANCEL_MESSAGE:
                LOGGER.info("%s - MessageType: RESERVATION_CANCEL_MESSAGE. Body: %s", wrapper.service_schema.name, body)
                wrapper.cancel_reservation(body["old_reservation_internal_id"], body["property_internal_id"])
            case MessageType.RESERVATION_IMPORT_REQUEST:
                LOGGER.info("%s - MessageType: RESERVATION_IMPORT_REQUEST.", wrapper.service_schema.name)
                for user_email, user_service in body["users_with_services"].items():
                    if wrapper.service_schema.value in user_service:
                        reservations = wrapper.import_new_or_newly_canceled_reservations({"email": user_email})
                        LOGGER.info("%s - Sending RESERVATION_IMPORT response. Reservations: %s", wrapper.service_schema.name, reservations)
                        channel.basic_publish(exchange=EXCHANGE_NAME, routing_key=WRAPPER_TO_CALENDAR_ROUTING_KEY,
                                              body=to_json(
                                                  MessageFactory.create_import_reservations_response_message(
                                                      wrapper.service_schema, reservations)
                                              ))
            case MessageType.RESERVATION_IMPORT_CONFIRM:
                LOGGER.info("%s - MessageType: RESERVATION_IMPORT_CONFIRM. Body: %s", wrapper.service_schema.name, body)
                wrapper.confirm_reservation(
                    body["reservation_internal_id"],
                    body["property_internal_id"],
                    body["begin_datetime"],
                    body["end_datetime"],
                )
            case MessageType.SCHEDULED_PROPERTY_IMPORT:
                LOGGER.info("%s - MessageType: SCHEDULED_PROPERTY_IMPORT.", wrapper.service_schema.name)
                for user_email, user_service in body["users_with_services"].items():
                    if wrapper.service_schema.value in user_service:
                        properties = wrapper.import_new_properties({"email": user_email})
                        if len(properties) > 0:
                            LOGGER.info("%s - Detected new properties. Addresses: %s", wrapper.service_schema.name, [p.get("address") for p in properties])
                            channel.basic_publish(exchange=EXCHANGE_NAME, routing_key=WRAPPER_TO_APP_ROUTING_KEY,
                                                  body=to_json(
                                                      MessageFactory.create_import_properties_response_message(
                                                          wrapper.service_schema, properties)
                                                  ))
    except Exception as e:
        LOGGER.error(f"Error in handle_recv: {e}")
    finally:
        channel.basic_ack(delivery_tag)


def run_scheduled_events_handler(wrapper: BaseWrapper):
    channel.basic_consume(
        queue=wrapper.queue,
        on_message_callback=lambda ch, method, properties, body: handle_recv(ch, method, properties, body, wrapper)
    )
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
