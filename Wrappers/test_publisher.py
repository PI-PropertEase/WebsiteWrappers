from ProjectUtils.MessagingService.queue_definitions import channel, EXCHANGE_NAME
from ProjectUtils.MessagingService.schemas import (
    create_message,
    PropertyMessage,
    PropertyType,
)

import random
import string

from time import sleep

from pydantic import BaseModel


class PropertyInDB:
    def __init__(self, id, address, name, curr_price, status):
        self.id = id
        self.address = address
        self.name = name
        self.curr_price = curr_price
        self.status = status


def generate_random_string(length=10):
    characters = string.ascii_letters + string.digits
    result = "".join(random.choice(characters) for _ in range(length))
    return result


def run():
    ids = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    while True:
        body = create_message(
            PropertyMessage(
                random.choice([t.value for t in PropertyType]),
                PropertyInDB(
                    id=random.choice(ids),
                    address=generate_random_string(random.choice(ids)),
                    name=generate_random_string(random.choice(ids)),
                    curr_price=1234,
                    status="Free",
                ).__dict__,
            ),
        )
        channel.basic_publish(exchange=EXCHANGE_NAME, routing_key="", body=body)
        print(f"Sent [x] {body}")
        sleep(5)


if __name__ == "__main__":
    run()
