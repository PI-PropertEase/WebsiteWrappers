from ProjectUtils.MessagingService.queue_definitions import channel, EXCHANGE_NAME, WRAPPER_ZOOKING_ROUTING_KEY, \
    WRAPPER_EARTHSTAYIN_ROUTING_KEY, WRAPPER_CLICKANDGO_ROUTING_KEY
from ProjectUtils.MessagingService.schemas import (
    MessageFactory,
    MessageType,
    to_json, Service,
)

import random
import string
import pika

from time import sleep

from pydantic import BaseModel

emails = ["alicez@gmail.com", "joedoe@gmail.com"]

class User(BaseModel):
    email: str


def run():
    for email in emails:
        try:
            body = MessageFactory.create_import_properties_message(User(email=email))

            channel.basic_publish(
                exchange=EXCHANGE_NAME,
                routing_key=WRAPPER_ZOOKING_ROUTING_KEY,
                body=to_json(body),
                properties=pika.BasicProperties(delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE)
            )
            print(f"Sent [x] {to_json(body)}")
            sleep(5)
        except ValueError as e:
            print(f"Error occurred: {e}")


if __name__ == "__main__":
    run()
