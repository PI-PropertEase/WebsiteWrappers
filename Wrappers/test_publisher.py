from ProjectUtils.MessagingService.queue_definitions import channel, EXCHANGE_NAME
from ProjectUtils.MessagingService.schemas import (
    MessageFactory,
    MessageType,
    to_json,
)

import random
import string

from time import sleep

from pydantic import BaseModel


class PropertyInDB(BaseModel):
    id: int
    address: str
    name: str
    curr_price: float
    status: str


def generate_random_string(length=10):
    characters = string.ascii_letters + string.digits
    result = "".join(random.choice(characters) for _ in range(length))
    return result


def run():
    ids = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    while True:
        try:
            msg_type = random.choice(
                [
                    MessageType.PROPERTY_CREATE,
                    MessageType.PROPERTY_UPDATE,
                    MessageType.PROPERTY_DELETE,
                ]
            )
            body = MessageFactory.create_property(
                msg_type,
                PropertyInDB(
                    id=random.choice(ids),
                    address=generate_random_string(random.choice(ids)),
                    name=generate_random_string(random.choice(ids)),
                    curr_price=1234,
                    status="Free",
                ),
            )

            channel.basic_publish(
                exchange=EXCHANGE_NAME, routing_key="", body=to_json(body)
            )
            print(f"Sent [x] {to_json(body)}")
            sleep(5)
        except ValueError as e:
            print(f"Error occurred: {e}")


if __name__ == "__main__":
    run()
