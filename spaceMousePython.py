#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
import websockets
import time
from collections import namedtuple
from typing import Callable, Union, List
from easyhid import Enumeration, HIDException
import datetime
import json

# Define named tuples for structured data
AxisSpec = namedtuple("AxisSpec", ["channel", "byte1", "byte2", "scale"])
ButtonSpec = namedtuple("ButtonSpec", ["channel", "byte", "bit"])
SpaceNavigator = namedtuple("SpaceNavigator", ["t", "x", "y", "z", "roll", "pitch", "yaw", "buttons"])
class ButtonState(list):
    def __int__(self):
        # Convert button state list to integer (bitwise operations)
        return sum((b << i) for (i, b) in enumerate(reversed(self)))

def to_int16(y1, y2):
    # Combine two bytes to form a signed 16-bit integer
    x = (y1) | (y2 << 8)
    if x >= 32768:
        x = -(65536 - x)
    return x

class DeviceSpec(object):
    def __init__(self, name, hid_id, led_id, mappings, button_mapping, axis_scale=350.0):
        # Initialize device specification
        self.name = name
        self.hid_id = hid_id
        self.led_id = led_id
        self.mappings = mappings
        self.button_mapping = button_mapping
        self.axis_scale = axis_scale
        self.device = None
        self.dict_state = {
            "t": -1, "x": 0, "y": 0, "z": 0, "roll": 0, "pitch": 0, "yaw": 0,
            "buttons": ButtonState([0] * len(self.button_mapping))
        }
        self.tuple_state = SpaceNavigator(**self.dict_state)

    def open(self):
        # Open the device connection
        if self.device:
            self.device.open()

    def close(self):
        # Close the device connection
        if self.device:
            self.device.close()

    def read(self):
        # Read data from the device and process it
        if not self.device:
            return None
        data = self.device.read(13)
        if data:
            self.process(data)
        return self.tuple_state

    def process(self, data):
        # Process the data received from the device
        for name, (chan, b1, b2, flip) in self.mappings.items():
            if data[0] == chan:
                self.dict_state[name] = flip * to_int16(data[b1], data[b2]) / float(self.axis_scale)

        for button_index, (chan, byte, bit) in enumerate(self.button_mapping):
            if data[0] == chan:
                mask = 1 << bit
                self.dict_state["buttons"][button_index] = 1 if (data[byte] & mask) != 0 else 0

        self.dict_state["t"] = time.time()
        self.tuple_state = SpaceNavigator(**self.dict_state)

# Define the SpaceMouse Wireless device specification
spacemouse_wireless_spec = DeviceSpec(
    name="SpaceNavigator",
    # vendor ID and product ID
    hid_id=[0x46D, 0xC626],
    # LED HID usage code pair
    led_id=[0x8, 0x4B],
    mappings={
        "x": AxisSpec(channel=1, byte1=1, byte2=2, scale=1),
        "y": AxisSpec(channel=1, byte1=3, byte2=4, scale=-1),
        "z": AxisSpec(channel=1, byte1=5, byte2=6, scale=-1),
        "pitch": AxisSpec(channel=2, byte1=1, byte2=2, scale=-1),
        "roll": AxisSpec(channel=2, byte1=3, byte2=4, scale=-1),
        "yaw": AxisSpec(channel=2, byte1=5, byte2=6, scale=1),
    },
    button_mapping=[
        ButtonSpec(channel=3, byte=1, bit=0),  # LEFT
        ButtonSpec(channel=3, byte=1, bit=1),  # RIGHT
    ],
    axis_scale=350.0,
)

def open_device():
    # Find and open the SpaceMouse Wireless device
    hid = Enumeration()
    all_devices = hid.find()
    print("All HID devices:")
    for device in all_devices:
        print(f"Vendor ID: {device.vendor_id}, Product ID: {device.product_id}, Product String: {device.product_string}")
        if (device.vendor_id == spacemouse_wireless_spec.hid_id[0] and 
            device.product_id == spacemouse_wireless_spec.hid_id[1]):
            spacemouse_wireless_spec.device = device
            spacemouse_wireless_spec.open()
            return spacemouse_wireless_spec
    
    raise Exception("SpaceMouse Navigator not found")

def print_state(state):
    # Print the state of the SpaceMouse device
    print("\t".join([f"{k}: {getattr(state, k):+.2f}" for k in ["x", "y", "z", "roll", "pitch", "yaw"]]))
    print(f"Buttons: {list(state.buttons)}")
    print("---")

async def sendSpacemouseData(uri):
    # Send SpaceMouse data to a WebSocket server
    async with websockets.connect(uri) as websocket:
        try:
            dev = open_device()
            print("SpaceMouse Wireless opened. Press Ctrl+C to exit.")
            last_send_time = 0
            while True:
                state = dev.read()
                current_time = time.time()
                timeStamp = datetime.datetime.now()
                if state:
                    # Prepare the data to be sent
                    print_state(state)
                    data = {
                        'x': float("%.2f" % getattr(state, 'x')),
                        'y': float("%.2f" % getattr(state, 'y')),
                        'z': float("%.2f" % getattr(state, 'z')),
                        'roll': float("%.2f" % getattr(state, 'roll')),
                        'pitch': float("%.2f" % getattr(state, 'pitch')),
                        'yaw': float("%.2f" % getattr(state, 'yaw')),
                        'button0': int(state.buttons[0]),
                        'button1': int(state.buttons[1]),
                        'timeStamp': timeStamp.timestamp()  # Convert datetime to Unix timestamp
                    }
                    
                    # Add a small delay to avoid flooding the console
                    if (current_time - last_send_time >= 1.0):
                        await websocket.send(json.dumps(data))
                        last_send_time = current_time
        except KeyboardInterrupt:
            print("\nExiting...")
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            if 'dev' in locals():
                dev.close()

if __name__ == "__main__":
    # Entry point for the script, run the asynchronous function
    websocket_uri = "wss://websocket.atrehealthtech.com/royal/test"
    asyncio.run(sendSpacemouseData(websocket_uri))

