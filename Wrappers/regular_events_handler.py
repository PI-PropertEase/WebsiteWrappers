from ProjectUtils.MessagingService.queue_definitions import channel, EXCHANGE_NAME, WRAPPER_TO_APP_ROUTING_KEY, \
    WRAPPER_TO_CALENDAR_ROUTING_KEY
from ProjectUtils.MessagingService.schemas import (
    MessageFactory,
    MessageType,
    to_json, from_json
)
from Wrappers.base_wrapper.wrapper import BaseWrapper
from Wrappers.models import set_property_mapped_id, get_management_event, create_management_event


def handle_recv(channel, method, properties, body, wrapper):
    delivery_tag = method.delivery_tag

    message = from_json(body)
    print(message.__dict__)
    body = message.body
    match message.message_type:
        case MessageType.PROPERTY_CREATE:
            wrapper.create_property(body)
        case MessageType.PROPERTY_UPDATE:
            wrapper.update_property(body["internal_id"], body["update_parameters"])
        case MessageType.PROPERTY_DELETE:
            wrapper.delete_property(body)
        case MessageType.PROPERTY_CREATE:
            wrapper.create_property(body)
        case MessageType.PROPERTY_IMPORT:
            properties = wrapper.import_properties(body)
            channel.basic_publish(exchange=EXCHANGE_NAME, routing_key=WRAPPER_TO_APP_ROUTING_KEY, body=to_json(
                MessageFactory.create_import_properties_response_message(wrapper.service_schema, properties)
            ))
        case MessageType.RESERVATION_IMPORT_INITIAL_REQUEST:
            # 1. Update the internal ids of the properties (because of duplicated properties in PropertyService)
            # 2. Import the reservations with the newly updated internal ids to map those into
            old_new_id_map = body["old_new_id_map"]
            for old_internal_id, new_internal_id in old_new_id_map.items():
                set_property_mapped_id(wrapper.service_schema, old_internal_id, new_internal_id)
            reservations = wrapper.import_reservations(body)
            channel.basic_publish(exchange=EXCHANGE_NAME, routing_key=WRAPPER_TO_CALENDAR_ROUTING_KEY, body=to_json(
                MessageFactory.create_import_reservations_response_message(wrapper.service_schema, reservations)
            ))
        case MessageType.MANAGEMENT_EVENT_PROPAGATION:
            update_parameters = {"closed_time_frames": [{
                "begin_datetime": body["begin_datetime"],
                "end_datetime": body["end_datetime"]
            }]}
            event_internal_id = body["event_internal_id"]
            if (management_event := get_management_event(wrapper.service_schema, event_internal_id)
            ) is not None:
                update_parameters["id"] = management_event.external_id
            external_id = wrapper.update_property(body["property_internal_id"], update_parameters)
            print(external_id)
            if external_id is not None:
                create_management_event(wrapper.service_schema, event_internal_id, external_id)

    channel.basic_ack(delivery_tag)


def run_regular_events_handler(wrapper: BaseWrapper):
    channel.basic_consume(
        queue=wrapper.queue,
        on_message_callback=lambda ch, method, properties, body: handle_recv(ch, method, properties, body, wrapper)
    )
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
