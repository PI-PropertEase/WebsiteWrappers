#!/bin/bash
python3 -m Wrappers.zooking.zooking_regular_handler &
python3 -m Wrappers.zooking.zooking_scheduled_handler &
python3 -m Wrappers.earthstayin.earthstayin_regular_handler &
python3 -m Wrappers.earthstayin.earthstayin_scheduled_handler &
python3 -m Wrappers.clickandgo.clickandgo_regular_handler &
python3 -m Wrappers.clickandgo.clickandgo_scheduled_handler &
wait